"""PTY capture for fullscreen terminal apps on the TURZX panel."""

from __future__ import annotations

import os
import re
import select
import shlex
import signal
import subprocess
import time
from dataclasses import dataclass, field
from shutil import which

COLS = 80
ROWS = 24
MIN_VISIBLE_CELLS = 20
MAX_RAW_BUFFER = 512 * 1024
TRIM_RAW_BUFFER = 384 * 1024
MAX_READ_PER_POLL = 96 * 1024
DEFAULT_FG = (220, 220, 220)
DEFAULT_BG = (0, 0, 0)

_ANSI_16 = (
    (0, 0, 0),
    (205, 49, 49),
    (13, 188, 121),
    (229, 229, 16),
    (36, 114, 200),
    (188, 63, 188),
    (17, 168, 205),
    (229, 229, 229),
    (127, 127, 127),
    (241, 76, 76),
    (35, 209, 139),
    (245, 245, 67),
    (59, 142, 234),
    (214, 112, 214),
    (41, 184, 219),
    (255, 255, 255),
)


@dataclass(frozen=True)
class TermCell:
    ch: str = " "
    fg: tuple[int, int, int] = DEFAULT_FG
    bg: tuple[int, int, int] = DEFAULT_BG


@dataclass
class TermFrame:
    rows: list[list[TermCell]] = field(default_factory=list)
    alive: bool = False
    label: str = ""
    cols: int = COLS
    grid_rows: int = ROWS


def _color256(index: int) -> tuple[int, int, int]:
    index &= 255
    if index < 16:
        return _ANSI_16[index]
    if index < 232:
        index -= 16
        r = index // 36
        g = (index // 6) % 6
        b = index % 6
        ramp = (0, 95, 135, 175, 215, 255)
        return (ramp[r], ramp[g], ramp[b])
    gray = 8 + (index - 232) * 10
    return (gray, gray, gray)


class _AnsiGrid:
    def __init__(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self._grid = [[TermCell() for _ in range(cols)] for _ in range(rows)]
        self._row = 0
        self._col = 0
        self._fg = DEFAULT_FG
        self._bg = DEFAULT_BG

    def clear(self) -> None:
        self._grid = [[TermCell() for _ in range(self.cols)] for _ in range(self.rows)]
        self._row = 0
        self._col = 0

    def move(self, row: int, col: int) -> None:
        self._row = max(0, min(row - 1, self.rows - 1))
        self._col = max(0, min(col - 1, self.cols - 1))

    def move_row(self, row: int) -> None:
        self._row = max(0, min(row - 1, self.rows - 1))

    def move_col(self, col: int) -> None:
        self._col = max(0, min(col - 1, self.cols - 1))

    def shift_row(self, delta: int) -> None:
        self._row = max(0, min(self._row + delta, self.rows - 1))

    def shift_col(self, delta: int) -> None:
        self._col = max(0, min(self._col + delta, self.cols - 1))

    def erase_line(self, mode: int = 0) -> None:
        row = self._grid[self._row]
        if mode == 0:
            for i in range(self._col, self.cols):
                row[i] = TermCell(" ", self._fg, self._bg)
        elif mode == 1:
            for i in range(0, self._col + 1):
                row[i] = TermCell(" ", self._fg, self._bg)
        else:
            for i in range(self.cols):
                row[i] = TermCell(" ", self._fg, self._bg)

    def erase_display(self, mode: int = 0) -> None:
        if mode == 2:
            self.clear()
            return
        if mode == 1:
            for r in range(0, self._row + 1):
                for c in range(self.cols):
                    if r < self._row or c <= self._col:
                        self._grid[r][c] = TermCell(" ", self._fg, self._bg)
            return
        for r in range(self._row, self.rows):
            start_col = self._col if r == self._row else 0
            for c in range(start_col, self.cols):
                self._grid[r][c] = TermCell(" ", self._fg, self._bg)

    def erase_chars(self, count: int) -> None:
        n = count if count > 0 else 1
        for _ in range(n):
            if self._col < self.cols:
                self._grid[self._row][self._col] = TermCell(" ", self._fg, self._bg)
                self._col += 1

    def write(self, text: str) -> None:
        for ch in text:
            if ch == "\n":
                self._row = min(self._row + 1, self.rows - 1)
                self._col = 0
                continue
            if ch == "\x08":
                self.shift_col(-1)
                continue
            if self._row >= self.rows:
                continue
            if self._col >= self.cols:
                self._row = min(self._row + 1, self.rows - 1)
                self._col = 0
                if self._row >= self.rows:
                    break
            self._grid[self._row][self._col] = TermCell(ch, self._fg, self._bg)
            self._col += 1

    def snapshot(self) -> list[list[TermCell]]:
        return [[TermCell(c.ch, c.fg, c.bg) for c in row] for row in self._grid]

    def set_sgr(self, params: list[int]) -> None:
        idx = 0
        bold = False
        while idx < len(params):
            code = params[idx]
            if code == 0:
                self._fg = DEFAULT_FG
                self._bg = DEFAULT_BG
                bold = False
            elif code == 1:
                bold = True
            elif code in (30, 31, 32, 33, 34, 35, 36, 37):
                base = code - 30
                self._fg = _ANSI_16[base + (8 if bold else 0)]
            elif code in (90, 91, 92, 93, 94, 95, 96, 97):
                self._fg = _ANSI_16[code - 90 + 8]
            elif code in (40, 41, 42, 43, 44, 45, 46, 47):
                self._bg = _ANSI_16[code - 40]
            elif code in (100, 101, 102, 103, 104, 105, 106, 107):
                self._bg = _ANSI_16[code - 100 + 8]
            elif code == 38 and idx + 2 < len(params) and params[idx + 1] == 5:
                self._fg = _color256(params[idx + 2])
                idx += 2
            elif code == 48 and idx + 2 < len(params) and params[idx + 1] == 5:
                self._bg = _color256(params[idx + 2])
                idx += 2
            elif code == 39:
                self._fg = DEFAULT_FG
            elif code == 49:
                self._bg = DEFAULT_BG
            idx += 1


class _AnsiParser:
    """Apply a PTY byte stream onto an ANSI colour grid."""

    _CSI = re.compile(r"\x1b\[[0-9?;]*[ -/]*[@-~]")

    def __init__(self, grid: _AnsiGrid) -> None:
        self._grid = grid
        self._pending = ""

    def feed(self, data: str) -> None:
        data = self._pending + data
        self._pending = ""
        idx = 0
        while idx < len(data):
            ch = data[idx]
            if ch == "\x1b":
                match = self._CSI.match(data, idx)
                if match:
                    self._handle_csi(match.group(0))
                    idx = match.end()
                    continue
                if idx + 2 < len(data) and data[idx + 1] in "([])":
                    idx += 3
                    continue
                if self._is_incomplete_escape(data[idx:]):
                    self._pending = data[idx:]
                    return
                idx += 1
                continue
            if ch == "\r":
                self._grid.move_col(1)
                idx += 1
                continue
            if ch == "\x07":
                idx += 1
                continue
            self._grid.write(ch)
            idx += 1

    @staticmethod
    def _is_incomplete_escape(fragment: str) -> bool:
        if fragment == "\x1b":
            return True
        if fragment.startswith("\x1b(") and len(fragment) < 3:
            return True
        if fragment.startswith("\x1b[") and not re.search(r"[@-~]$", fragment):
            return True
        return False

    @staticmethod
    def _parse_params(raw: str) -> list[int]:
        if not raw:
            return [0]
        parts: list[int] = []
        for piece in raw.split(";"):
            if not piece:
                parts.append(0)
                continue
            try:
                parts.append(int(piece))
            except ValueError:
                continue
        return parts

    def _param(self, params: list[int], index: int, default: int) -> int:
        if index >= len(params) or params[index] == 0:
            return default
        return params[index]

    def _handle_csi(self, seq: str) -> None:
        if seq in ("\x1b[?1049h", "\x1b[?1049l", "\x1b[?25h", "\x1b[?25l", "\x1b[?7h", "\x1b[?7l"):
            return
        if seq == "\x1b[2J":
            self._grid.clear()
            return
        if seq == "\x1b[H":
            self._grid.move(1, 1)
            return
        if seq.endswith("m"):
            self._grid.set_sgr(self._parse_params(seq[2:-1]))
            return

        body = seq[2:-1]
        final = seq[-1]
        params = self._parse_params(body)

        if final in ("H", "f"):
            row = self._param(params, 0, 1)
            col = self._param(params, 1, 1)
            self._grid.move(row, col)
            return
        if final == "A":
            self._grid.shift_row(-self._param(params, 0, 1))
            return
        if final == "B":
            self._grid.shift_row(self._param(params, 0, 1))
            return
        if final == "C":
            self._grid.shift_col(self._param(params, 0, 1))
            return
        if final == "D":
            self._grid.shift_col(-self._param(params, 0, 1))
            return
        if final == "G":
            self._grid.move_col(self._param(params, 0, 1))
            return
        if final == "d":
            self._grid.move_row(self._param(params, 0, 1))
            return
        if final == "K":
            self._grid.erase_line(self._param(params, 0, 0))
            return
        if final == "J":
            self._grid.erase_display(self._param(params, 0, 0))
            return
        if final == "X":
            self._grid.erase_chars(self._param(params, 0, 1))
            return


class TermCapture:
    """Run one terminal app under script(1) and parse ANSI into a colour grid."""

    def __init__(self, command: list[str], *, label: str = "", cols: int = COLS, rows: int = ROWS) -> None:
        self.command = command
        self.label = label
        self.cols = cols
        self.rows = rows
        self._grid = _AnsiGrid(rows, cols)
        self._parser = _AnsiParser(self._grid)
        self._proc: subprocess.Popen[bytes] | None = None
        self._stdout_fd: int | None = None
        self._raw_buffer = ""
        self._last_good: TermFrame | None = None
        self._started_at = 0.0
        self._start()

    def _script_command(self) -> list[str]:
        if not self.command:
            return []
        if self.command[0] == "script":
            return list(self.command)
        inner = " ".join(shlex.quote(part) for part in self.command)
        setup = (
            "export TERM=xterm-256color COLORTERM=truecolor; "
            f"stty cols {self.cols} rows {self.rows} 2>/dev/null; exec {inner}"
        )
        return ["script", "-q", "-c", setup, "/dev/null"]

    def _start(self) -> None:
        if not self.command or not which(self.command[0]) or not which("script"):
            return
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        try:
            self._proc = subprocess.Popen(
                self._script_command(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                env=env,
                start_new_session=True,
            )
        except OSError:
            self._proc = None
            return
        if self._proc.stdout is not None:
            self._stdout_fd = self._proc.stdout.fileno()
        self._started_at = time.monotonic()

    def close(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            try:
                os.killpg(self._proc.pid, signal.SIGTERM)
                self._proc.wait(timeout=1.0)
            except (ProcessLookupError, subprocess.SubprocessError, OSError):
                try:
                    os.killpg(self._proc.pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
        if self._proc is not None and self._proc.stdout is not None:
            try:
                self._proc.stdout.close()
            except OSError:
                pass
        self._stdout_fd = None
        self._proc = None

    def poll(self) -> TermFrame:
        alive = self._proc is not None and self._proc.poll() is None
        if alive and self._stdout_fd is not None:
            self._drain_output()
        elif self._proc is not None and self._proc.poll() is not None and which(self.command[0]):
            self.close()
            self._reset()
            self._start()
            alive = self._proc is not None and self._proc.poll() is None

        return self._finalize_frame(
            rows=self._grid.snapshot(),
            alive=alive,
            label=self.label,
            cols=self.cols,
            grid_rows=self.rows,
        )

    def _reset(self) -> None:
        self._grid = _AnsiGrid(self.rows, self.cols)
        self._parser = _AnsiParser(self._grid)
        self._raw_buffer = ""
        self._last_good = None

    def _trim_buffer(self) -> None:
        if len(self._raw_buffer) <= MAX_RAW_BUFFER:
            return
        self._raw_buffer = self._raw_buffer[-TRIM_RAW_BUFFER:]
        grid = _AnsiGrid(self.rows, self.cols)
        self._parser = _AnsiParser(grid)
        self._parser.feed(self._raw_buffer)
        self._grid = grid

    def _drain_output(self) -> int:
        if self._stdout_fd is None:
            return 0
        total = 0
        ready, _, _ = select.select([self._stdout_fd], [], [], 0.2)
        if self._stdout_fd in ready:
            total += self._read_available(MAX_READ_PER_POLL)

        if total:
            self._trim_buffer()

        warming = time.monotonic() - self._started_at < 4.0
        if warming and self._visible_cells(self._grid.snapshot()) < MIN_VISIBLE_CELLS:
            ready, _, _ = select.select([self._stdout_fd], [], [], 0.35)
            if self._stdout_fd in ready:
                got = self._read_available(MAX_READ_PER_POLL - total)
                total += got
                if got:
                    self._trim_buffer()
        return total

    def _read_available(self, limit: int) -> int:
        if self._stdout_fd is None or limit <= 0:
            return 0
        total = 0
        while total < limit:
            ready, _, _ = select.select([self._stdout_fd], [], [], 0)
            if self._stdout_fd not in ready:
                break
            try:
                chunk = os.read(self._stdout_fd, min(65536, limit - total))
            except OSError:
                break
            if not chunk:
                break
            total += len(chunk)
            text = chunk.decode("utf-8", "replace")
            self._raw_buffer += text
            self._parser.feed(text)
        return total

    def _visible_cells(self, rows: list[list[TermCell]]) -> int:
        return sum(1 for row in rows for cell in row if cell.ch.strip())

    def _finalize_frame(self, **kwargs) -> TermFrame:
        frame = TermFrame(**kwargs)
        visible = self._visible_cells(frame.rows)
        if visible >= MIN_VISIBLE_CELLS:
            self._last_good = frame
            return frame
        if self._last_good is not None:
            return TermFrame(
                rows=self._last_good.rows,
                alive=frame.alive,
                label=frame.label,
                cols=frame.cols,
                grid_rows=frame.grid_rows,
            )
        return frame
