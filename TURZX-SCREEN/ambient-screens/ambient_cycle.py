"""Rotate ambient terminal apps on the TURZX when game mode is off."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from term_capture import TermCapture, TermFrame

STATE_PATH = Path.home() / ".local" / "state" / "turzx" / "ambient.json"
SLOT_SECONDS = 300.0

AMBIENT_SLOTS: tuple[tuple[str, list[str], int, int], ...] = (
    ("weathr", ["weathr", "--metric", "--hide-hud", "--hide-location", "--silent"], 80, 24),
    ("weatherspect", ["weatherspect"], 80, 24),
    ("asciiquarium", ["asciiquarium"], 80, 24),
)


@dataclass
class AmbientSlot:
    name: str
    command: list[str]
    cols: int
    rows: int


class AmbientCycle:
    def __init__(self, *, slot_seconds: float = SLOT_SECONDS) -> None:
        self._slot_seconds = slot_seconds
        self._capture: TermCapture | None = None
        self._slot_index = 0
        self._slot_started = time.monotonic()
        self._active = False
        self._state_mtime: float | None = None
        self._load_state()
        self._sync_state_mtime()

    def set_active(self, active: bool) -> None:
        if active == self._active:
            return
        self._active = active
        if active:
            self._ensure_capture()
        else:
            self.close()

    def close(self) -> None:
        if self._capture is not None:
            self._capture.close()
            self._capture = None

    def poll(self) -> TermFrame:
        if not self._active:
            return TermFrame(label="ambient")
        self._check_external_state()
        self._maybe_rotate()
        if self._capture is None:
            self._ensure_capture()
        if self._capture is None:
            return TermFrame(label="ambient")
        return self._capture.poll()

    def _current_slot(self) -> AmbientSlot:
        name, command, cols, rows = AMBIENT_SLOTS[self._slot_index % len(AMBIENT_SLOTS)]
        return AmbientSlot(name=name, command=list(command), cols=cols, rows=rows)

    def _maybe_rotate(self) -> None:
        elapsed = time.monotonic() - self._slot_started
        if elapsed < self._slot_seconds:
            return
        self._slot_index = (self._slot_index + 1) % len(AMBIENT_SLOTS)
        self._slot_started = time.monotonic()
        self._save_state()
        self._restart_capture()

    def _sync_state_mtime(self) -> None:
        try:
            self._state_mtime = STATE_PATH.stat().st_mtime if STATE_PATH.is_file() else None
        except OSError:
            self._state_mtime = None

    def _check_external_state(self) -> None:
        try:
            mtime = STATE_PATH.stat().st_mtime if STATE_PATH.is_file() else None
        except OSError:
            mtime = None
        if mtime == self._state_mtime:
            return
        prev_index = self._slot_index
        self._load_state()
        self._state_mtime = mtime
        if self._slot_index != prev_index or mtime is not None:
            self._restart_capture()

    def _ensure_capture(self) -> None:
        if self._capture is not None:
            return
        slot = self._current_slot()
        self._capture = TermCapture(slot.command, label=slot.name, cols=slot.cols, rows=slot.rows)

    def _restart_capture(self) -> None:
        if self._capture is not None:
            self._capture.close()
            self._capture = None
        self._ensure_capture()

    def _load_state(self) -> None:
        if not STATE_PATH.is_file():
            return
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        try:
            index = int(data.get("slot_index", 0))
            started = float(data.get("slot_started", time.time()))
        except (TypeError, ValueError):
            return
        index %= len(AMBIENT_SLOTS)
        age = time.time() - started
        if age >= self._slot_seconds:
            steps = int(age // self._slot_seconds)
            index = (index + steps) % len(AMBIENT_SLOTS)
            started += steps * self._slot_seconds
        self._slot_index = index
        self._slot_started = time.monotonic() - max(0.0, time.time() - started)

    def _save_state(self) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "slot_index": self._slot_index,
            "slot_started": time.time() - (time.monotonic() - self._slot_started),
        }
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(STATE_PATH)
        self._sync_state_mtime()

    def advance(self) -> None:
        self._slot_index = (self._slot_index + 1) % len(AMBIENT_SLOTS)
        self._slot_started = time.monotonic()
        self._save_state()
        if self._active:
            self._restart_capture()
