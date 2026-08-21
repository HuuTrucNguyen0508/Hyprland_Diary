#!/usr/bin/env python3
"""Live H.264 dashboard experiment for TURZX (opt-in; not the default service).

Renders the normal 1280x800 dashboard, rotates to wire 800x1280, encodes with
ffmpeg (prefer h264_nvenc, else libx264 ultrafast/zerolatency), and pushes
Annex-B chunks over the proven TUR_USB path.

Stop turzx-dashboard.service first (USB exclusive).

  systemctl --user stop turzx-dashboard.service
  cd ~/Documents/dashboard && .venv/bin/python turzx_h264_live.py --seconds 15 --fps 15
  systemctl --user start turzx-dashboard.service
"""

from __future__ import annotations

import argparse
import json
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from PIL import Image

TURING_ROOT = Path(__file__).resolve().parent.parent / "turing-smart-screen-python"
sys.path.insert(0, str(TURING_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from library.lcd.lcd_comm import Orientation  # noqa: E402
from library.lcd.lcd_comm_turing_usb import LcdCommTuringUSB  # noqa: E402

from dashboard import prepare_frame  # noqa: E402
from h264_usb import (  # noqa: E402
    WIRE_H,
    WIRE_W,
    flow_control,
    negotiate_chunk_size,
    play_chunk,
    stop_stream,
    video_preamble,
)
from renderer import (  # noqa: E402
    GAP,
    HEADER_H,
    MARGIN,
    MARGIN_LEFT,
    WIDTH,
    DashboardRenderer,
)
from settings import SettingsWatcher  # noqa: E402
from speedtest_state import SpeedtestWatcher  # noqa: E402
from stats import DashboardStats, StatsCollector  # noqa: E402
from theme import Palette, SchemeWatcher  # noqa: E402
from turzx_screen import (  # noqa: E402
    CONTENT_ROTATE,
    DEFAULT_BRIGHTNESS,
    DEFAULT_CROP_ANCHOR,
    DEFAULT_CROP_NUDGE_X,
    DEFAULT_CROP_NUDGE_Y,
    DEFAULT_FIT,
    DEFAULT_NUDGE_X,
    DEFAULT_NUDGE_Y,
    DEFAULT_SCALE,
    DEFAULT_ZOOM,
    LCD_ORIENTATION,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
)

FONT_DIR = TURING_ROOT / "res" / "fonts"
OUT_DIR = Path(__file__).resolve().parent / "diag"


def require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg not found on PATH")
    return path


def pick_encoder(ffmpeg: str, prefer: str) -> str:
    """prefer: auto | nvenc | x264.

    auto → libx264 (cleaner on flat UI). NVENC is faster but harsher on this layout.
    """
    if prefer == "nvenc":
        return "h264_nvenc"
    return "libx264"


def ffmpeg_encoder_args(encoder: str, fps: int) -> list[str]:
    # Short GOP for lower glass latency (trade: more keyframe bytes).
    gop = max(3, min(fps, 5))
    if encoder == "h264_nvenc":
        return [
            "-c:v",
            "h264_nvenc",
            "-profile:v",
            "baseline",
            "-preset",
            "p1",
            "-tune",
            "ll",
            "-rc",
            "constqp",
            "-qp",
            "28",
            "-g",
            str(gop),
            "-bf",
            "0",
            "-pix_fmt",
            "yuv420p",
        ]
    return [
        "-c:v",
        "libx264",
        "-profile:v",
        "baseline",
        "-level",
        "3.1",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-g",
        str(gop),
        "-keyint_min",
        str(gop),
        "-bf",
        "0",
        "-x264-params",
        "repeat-headers=1:scenecut=0",
        "-pix_fmt",
        "yuv420p",
    ]


def to_wire_rgb(frame_1280x800: Image.Image) -> bytes:
    """Match JPEG LANDSCAPE path: ROTATE_270 → 800x1280 RGB."""
    wire = frame_1280x800.transpose(Image.Transpose.ROTATE_270)
    if wire.size != (WIRE_W, WIRE_H):
        raise RuntimeError(f"wire size {wire.size}, expected {(WIRE_W, WIRE_H)}")
    return wire.convert("RGB").tobytes()


def soften_layout_gaps(layout: Image.Image, palette: Palette) -> Image.Image:
    """No-op: shared top metrics plate removed the mid-bar; kept for call-site compat."""
    return layout


def warm_bonsai(collector: StatsCollector, settings_watch: SettingsWatcher, *, timeout_s: float = 4.0) -> DashboardStats:
    """Give rbonsai a moment so the centre panel is not an empty dark slab at stream start."""
    deadline = time.perf_counter() + timeout_s
    stats = collector.poll(settings_watch.poll())
    while time.perf_counter() < deadline and not stats.bonsai_lines:
        time.sleep(0.2)
        stats = collector.poll(settings_watch.poll())
    return stats


class AnnexBPusher(threading.Thread):
    """Read Annex-B from ffmpeg stdout and push USB chunks."""

    def __init__(self, dev, stdout, chunk_size: int, *, min_flush: int = 8192, flush_ms: float = 40.0) -> None:
        super().__init__(name="h264-pusher", daemon=True)
        self.dev = dev
        self.stdout = stdout
        self.chunk_size = chunk_size
        self.min_flush = min_flush
        self.flush_s = flush_ms / 1000.0
        self.buf = bytearray()
        self.chunks = 0
        self.bytes_sent = 0
        self.flow_waits = 0
        self.error: BaseException | None = None
        self._stop = threading.Event()
        self.t_first: float | None = None
        self.t_start = time.perf_counter()
        self._last_send = self.t_start

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        try:
            fd = self.stdout.fileno()
            while not self._stop.is_set():
                ready, _, _ = select.select([fd], [], [], self.flush_s)
                if ready:
                    chunk = self.stdout.read(65536)
                    if not chunk:
                        break
                    self.buf.extend(chunk)
                self._flush_ready(force=False)
            self._flush_ready(force=True)
        except BaseException as exc:
            self.error = exc

    def _flush_ready(self, *, force: bool) -> None:
        now = time.perf_counter()
        while len(self.buf) >= self.chunk_size:
            piece = bytes(self.buf[: self.chunk_size])
            del self.buf[: self.chunk_size]
            self._send(piece, is_last=False)
            now = time.perf_counter()
        if not self.buf:
            return
        aged = (now - self._last_send) >= self.flush_s
        if force or (aged and len(self.buf) >= self.min_flush) or (aged and self.t_first is None):
            piece = bytes(self.buf)
            self.buf.clear()
            self._send(piece, is_last=False)

    def _send(self, data: bytes, *, is_last: bool) -> None:
        resp = play_chunk(self.dev, data, is_last=is_last)
        self.chunks += 1
        self.bytes_sent += len(data)
        self._last_send = time.perf_counter()
        if self.t_first is None:
            self.t_first = self._last_send
        if flow_control(self.dev, resp):
            self.flow_waits += 1

    def flush_final(self) -> None:
        """Send remaining buffer with is_last=1, then STOP."""
        if self.buf:
            self._send(bytes(self.buf), is_last=True)
            self.buf.clear()
        stop_stream(self.dev)

    def stats(self) -> dict:
        wall = time.perf_counter() - self.t_start
        start_ms = ((self.t_first - self.t_start) * 1000) if self.t_first else None
        return {
            "chunks": self.chunks,
            "bytes_sent": self.bytes_sent,
            "flow_waits": self.flow_waits,
            "wall_s": round(wall, 4),
            "start_latency_ms": round(start_ms, 2) if start_ms is not None else None,
            "sustained_mib_s": round((self.bytes_sent / wall) / (1024 * 1024), 3) if wall > 0 else 0.0,
        }


def restore_still(lcd: LcdCommTuringUSB, frame: Image.Image | None = None) -> None:
    if frame is None:
        img = Image.new("RGB", (NATIVE_WIDTH, NATIVE_HEIGHT), (28, 32, 40))
    else:
        img = frame
    lcd.DisplayPILImage(img)
    lcd.SetBrightness(DEFAULT_BRIGHTNESS)


def main() -> int:
    parser = argparse.ArgumentParser(description="TURZX live H.264 dashboard experiment")
    parser.add_argument("--seconds", type=float, default=15.0, help="Run duration (0 = until Ctrl-C)")
    parser.add_argument("--fps", type=int, default=15, help="Encode + cmd15 fps")
    parser.add_argument(
        "--stats-interval",
        type=float,
        default=1.0,
        help="How often to refresh CPU/GPU/etc on the painted frame (default 1s; stops percent flicker)",
    )
    parser.add_argument(
        "--bonsai-warmup",
        type=float,
        default=4.0,
        help="Seconds to wait for rbonsai lines before streaming (0=skip)",
    )
    parser.add_argument(
        "--encoder",
        choices=("auto", "nvenc", "x264"),
        default="auto",
        help="auto=libx264 (cleaner UI); nvenc=faster, harsher seams",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=OUT_DIR / "h264_live_results.json",
        help="Results JSON",
    )
    parser.add_argument("--rotate", type=int, default=CONTENT_ROTATE, choices=(0, 90, 180, 270))
    args = parser.parse_args()

    ffmpeg = require_ffmpeg()
    encoder = pick_encoder(ffmpeg, args.encoder)
    print(
        f"encoder={encoder} fps={args.fps} stats_interval={args.stats_interval}s "
        f"wire={WIRE_W}x{WIRE_H} seconds={args.seconds or '∞'}"
    )

    scheme = SchemeWatcher()
    settings_watch = SettingsWatcher()
    speedtest_watch = SpeedtestWatcher()
    renderer = DashboardRenderer(FONT_DIR, palette=scheme.palette)
    collector = StatsCollector()

    stop = False

    def handle_signal(_signum, _frame) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if args.bonsai_warmup > 0:
        print(f"warming bonsai up to {args.bonsai_warmup:.0f}s…")
        warm_bonsai(collector, settings_watch, timeout_s=args.bonsai_warmup)

    lcd = LcdCommTuringUSB(
        com_port="AUTO",
        display_width=NATIVE_WIDTH,
        display_height=NATIVE_HEIGHT,
    )
    lcd.InitializeComm()
    lcd.SetOrientation(LCD_ORIENTATION)
    assert lcd.orientation == Orientation.LANDSCAPE

    ff_cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIRE_W}x{WIRE_H}",
        "-r",
        str(args.fps),
        "-i",
        "pipe:0",
        *ffmpeg_encoder_args(encoder, args.fps),
        "-an",
        "-f",
        "h264",
        "pipe:1",
    ]
    print("ffmpeg:", " ".join(ff_cmd))

    results: dict = {
        "encoder": encoder,
        "fps": args.fps,
        "stats_interval": args.stats_interval,
        "seconds": args.seconds,
        "wire_wh": f"{WIRE_W}x{WIRE_H}",
    }
    last_frame: Image.Image | None = None
    last_wire: bytes | None = None
    last_stats_at = 0.0
    frames_in = 0
    layout_refreshes = 0
    pusher: AnnexBPusher | None = None
    proc: subprocess.Popen | None = None

    try:
        video_preamble(lcd.dev, frame_rate=args.fps)
        chunk_size = negotiate_chunk_size(lcd.dev)
        print(f"chunk_size={chunk_size}")
        results["chunk_size"] = chunk_size

        proc = subprocess.Popen(
            ff_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        assert proc.stdin and proc.stdout
        pusher = AnnexBPusher(lcd.dev, proc.stdout, chunk_size)
        pusher.start()

        frame_period = 1.0 / args.fps
        t_end = time.perf_counter() + args.seconds if args.seconds > 0 else None
        next_frame_at = time.perf_counter()

        while not stop:
            if t_end is not None and time.perf_counter() >= t_end:
                break
            if pusher.error is not None:
                raise RuntimeError(f"pusher failed: {pusher.error!r}")
            if proc.poll() is not None:
                err = (proc.stderr.read() if proc.stderr else b"").decode("utf-8", "replace")
                raise RuntimeError(f"ffmpeg exited {proc.returncode}: {err[-500:]}")

            now = time.perf_counter()
            if now < next_frame_at:
                time.sleep(min(0.005, next_frame_at - now))
                continue
            next_frame_at = max(next_frame_at + frame_period, time.perf_counter())

            refresh_layout = last_wire is None or (now - last_stats_at) >= args.stats_interval
            if refresh_layout:
                renderer.palette = scheme.poll()
                settings = settings_watch.poll()
                speed_state = speedtest_watch.poll()
                stats = collector.poll(settings)
                if speed_state is not None and speed_state.visible:
                    layout = renderer.render_speedtest(speed_state)
                else:
                    layout = soften_layout_gaps(renderer.render(stats), renderer.palette)

                frame, _, _ = prepare_frame(
                    layout,
                    rotate=args.rotate,
                    scale=DEFAULT_SCALE,
                    zoom=DEFAULT_ZOOM,
                    fit=DEFAULT_FIT,
                    nudge_x=DEFAULT_NUDGE_X,
                    nudge_y=DEFAULT_NUDGE_Y,
                    crop_nudge_x=DEFAULT_CROP_NUDGE_X,
                    crop_nudge_y=DEFAULT_CROP_NUDGE_Y,
                    crop_anchor=DEFAULT_CROP_ANCHOR,
                    bg=renderer.palette.bg,
                )
                assert frame.size == (NATIVE_WIDTH, NATIVE_HEIGHT)
                last_frame = frame
                last_wire = to_wire_rgb(frame)
                last_stats_at = now
                layout_refreshes += 1

            assert last_wire is not None
            try:
                proc.stdin.write(last_wire)
                proc.stdin.flush()
            except BrokenPipeError as exc:
                err = (proc.stderr.read() if proc.stderr else b"").decode("utf-8", "replace")
                raise RuntimeError(f"ffmpeg stdin broken: {err[-500:]}") from exc
            frames_in += 1
            if frames_in == 1 or frames_in % args.fps == 0:
                print(
                    f"  frames_in={frames_in} layout_refreshes={layout_refreshes} "
                    f"chunks={pusher.chunks} bytes={pusher.bytes_sent}"
                )

        # shutdown encoder → drain annex-B
        print("closing encoder…")
        try:
            proc.stdin.close()
        except Exception:
            pass
        pusher.join(timeout=15)
        leftover = proc.stdout.read() if proc.stdout else b""
        if leftover:
            pusher.buf.extend(leftover)
        pusher.flush_final()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

        results["frames_in"] = frames_in
        results["layout_refreshes"] = layout_refreshes
        results["push"] = pusher.stats()
        results["ok"] = True
        print(
            f"done frames_in={frames_in} layout_refreshes={layout_refreshes} chunks={pusher.chunks} "
            f"start_latency_ms={results['push']['start_latency_ms']} "
            f"flow_waits={pusher.flow_waits}"
        )
    except Exception as exc:
        results["ok"] = False
        results["error"] = repr(exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        try:
            stop_stream(lcd.dev)
        except Exception:
            pass
        if proc is not None:
            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass
            proc.kill()
        if pusher is not None:
            pusher.stop()
    finally:
        collector.close()
        try:
            restore_still(lcd, last_frame)
            results["restored_still"] = True
        except Exception as exc:
            results["restore_error"] = repr(exc)
        try:
            lcd.closeSerial()
        except Exception:
            pass

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Wrote {args.json_out}")
    return 0 if results.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
