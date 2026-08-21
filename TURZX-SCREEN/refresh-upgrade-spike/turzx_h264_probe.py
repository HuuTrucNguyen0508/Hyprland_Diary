#!/usr/bin/env python3
"""TURZX H.264 stream probe skeleton (Approach 2).

Builds a tiny Annex-B H.264 clip via ffmpeg, then (with --usb) pushes it through
the stock TUR_USB chunk path and measures start latency + sustained push rate.

Wire size is 800x1280 (firmware portrait). Dashboard content is 1280x800 LANDSCAPE;
stock DisplayPILImage rotates 270 before USB. This probe encodes at wire size so
send_video / PLAY_H264_CHUNK sees the same orientation the JPEG path delivers.

Default is dry-run: synthesize + validate only. Does NOT open the panel unless
you pass --usb. Stop turzx-dashboard.service before any USB run.

Example:
  .venv/bin/python turzx_h264_probe.py
  systemctl --user stop turzx-dashboard.service
  .venv/bin/python turzx_h264_probe.py --usb --seconds 3 --fps 25
  systemctl --user start turzx-dashboard.service
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TURING_ROOT = Path.home() / "Documents" / "turing-smart-screen-python"
sys.path.insert(0, str(TURING_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from library.lcd.lcd_comm_turing_usb import (  # noqa: E402
    CMD_GET_H264_CHUNK_SIZE,
    CMD_GET_STREAM_STATUS,
    CMD_PLAY_H264_CHUNK,
    CMD_STOP_STREAM,
    LcdCommTuringUSB,
    build_command_packet_header,
    clear_image,
    delay,
    encrypt_command_packet,
    send_brightness_command,
    send_frame_rate_command,
    write_to_device,
)
from library.lcd.lcd_comm import Orientation  # noqa: E402

from turzx_screen import (  # noqa: E402
    DEFAULT_BRIGHTNESS,
    LCD_ORIENTATION,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
)

# Post-ROTATE_270 wire size (matches DisplayPILImage LANDSCAPE send).
WIRE_W, WIRE_H = 800, 1280
DEFAULT_CHUNK = 202752
OUT_DIR = Path(__file__).resolve().parent / "diag"


def require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg not found on PATH (needed to build Annex-B clip)")
    return path


def build_annexb_clip(
    out_h264: Path,
    *,
    seconds: float,
    fps: int,
    ffmpeg: str,
) -> dict:
    """Synthetic 800x1280 H.264 Annex-B (baseline, no audio).

    lavfi testsrc2 + drawtext counter. Pixel format yuv420p for broad decoder
    friendliness. Resolution is wire size, not content canvas.
    """
    out_h264.parent.mkdir(parents=True, exist_ok=True)
    # Two-step via MP4 then annexb bsf keeps SPS/PPS framing consistent with
    # extract_h264_from_mp4 / send_video. Direct -f h264 also works; MP4 path
    # matches the library's preferred extract route.
    with tempfile.TemporaryDirectory(prefix="turzx_h264_") as tmp:
        mp4 = Path(tmp) / "clip.mp4"
        vf = (
            f"scale={WIRE_W}:{WIRE_H},"
            f"drawtext=text='H264 WIRE {WIRE_W}x{WIRE_H} fps={fps}':"
            f"x=24:y=48:fontsize=36:fontcolor=white:"
            f"box=1:boxcolor=black@0.5,"
            f"drawtext=text='%{{n}}':x=24:y=100:fontsize=48:fontcolor=lime"
        )
        gen = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={WIRE_W}x{WIRE_H}:rate={fps}:duration={seconds}",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-profile:v",
            "baseline",
            "-level",
            "3.1",
            "-pix_fmt",
            "yuv420p",
            "-g",
            str(fps),
            "-bf",
            "0",
            "-an",
            str(mp4),
        ]
        subprocess.run(gen, check=True, capture_output=True)
        extract = [
            ffmpeg,
            "-y",
            "-i",
            str(mp4),
            "-c:v",
            "copy",
            "-bsf:v",
            "h264_mp4toannexb",
            "-an",
            "-f",
            "h264",
            str(out_h264),
        ]
        subprocess.run(extract, check=True, capture_output=True)

    size = out_h264.stat().st_size
    return {
        "path": str(out_h264),
        "bytes": size,
        "wire_wh": f"{WIRE_W}x{WIRE_H}",
        "content_wh_note": f"{NATIVE_WIDTH}x{NATIVE_HEIGHT} LANDSCAPE + ROTATE_270 → wire",
        "seconds": seconds,
        "fps": fps,
    }


def negotiate_chunk_size(dev) -> int:
    resp = write_to_device(dev, encrypt_command_packet(build_command_packet_header(CMD_GET_H264_CHUNK_SIZE)))
    chunk_size = DEFAULT_CHUNK
    if resp and len(resp) >= 12:
        negotiated = int.from_bytes(resp[8:12], byteorder="big", signed=False)
        if 0 < negotiated <= 1024 * 1024:
            chunk_size = negotiated
    return chunk_size


def video_preamble(dev, *, frame_rate: int, brightness_device: int = 32) -> None:
    """Mirror send_video() setup before PLAY_H264_CHUNK (cmds 111/112/13/14/41/102/15)."""
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(111)))
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(112)))
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(13)))
    send_brightness_command(dev, brightness_device)
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(41)))
    clear_image(dev)
    send_frame_rate_command(dev, frame_rate)


def push_annexb_chunks(
    dev,
    h264_path: Path,
    *,
    chunk_size: int,
    loop: bool = False,
) -> dict:
    """Instrumented copy of send_video()'s chunk loop (cmd 121 + flow-control 122)."""
    file_size = h264_path.stat().st_size
    chunk_times_ms: list[float] = []
    bytes_sent = 0
    chunks = 0
    flow_waits = 0
    t_first_chunk_done: float | None = None
    t_start = time.perf_counter()

    try:
        while True:
            with open(h264_path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    chunksize = len(data)
                    is_last = f.tell() == file_size

                    cmd_packet = build_command_packet_header(CMD_PLAY_H264_CHUNK)
                    cmd_packet[8] = (chunksize >> 24) & 0xFF
                    cmd_packet[9] = (chunksize >> 16) & 0xFF
                    cmd_packet[10] = (chunksize >> 8) & 0xFF
                    cmd_packet[11] = chunksize & 0xFF
                    if is_last:
                        cmd_packet[12] = 1

                    full_payload = encrypt_command_packet(cmd_packet) + data
                    c0 = time.perf_counter()
                    response = write_to_device(dev, full_payload)
                    c1 = time.perf_counter()
                    chunk_times_ms.append((c1 - c0) * 1000)
                    bytes_sent += chunksize
                    chunks += 1
                    if t_first_chunk_done is None:
                        t_first_chunk_done = c1

                    if response is None:
                        flow_waits += 1
                        delay(dev, 2)
                    else:
                        st = write_to_device(
                            dev,
                            encrypt_command_packet(build_command_packet_header(CMD_GET_STREAM_STATUS)),
                        )
                        if st and len(st) > 8 and st[8] > 3:
                            flow_waits += 1
                            delay(dev, 2)

            if not loop:
                break
    finally:
        write_to_device(dev, encrypt_command_packet(build_command_packet_header(CMD_STOP_STREAM)))

    t_end = time.perf_counter()
    wall = t_end - t_start
    start_latency_ms = ((t_first_chunk_done - t_start) * 1000) if t_first_chunk_done else None
    return {
        "file_bytes": file_size,
        "bytes_sent": bytes_sent,
        "chunks": chunks,
        "chunk_size": chunk_size,
        "flow_waits": flow_waits,
        "wall_s": round(wall, 4),
        "start_latency_ms": round(start_latency_ms, 2) if start_latency_ms is not None else None,
        "chunk_ms_median": round(statistics.median(chunk_times_ms), 2) if chunk_times_ms else None,
        "chunk_ms_p95": (
            round(sorted(chunk_times_ms)[min(len(chunk_times_ms) - 1, int(0.95 * (len(chunk_times_ms) - 1)))], 2)
            if chunk_times_ms
            else None
        ),
        "sustained_mib_s": round((bytes_sent / wall) / (1024 * 1024), 3) if wall > 0 else 0.0,
        "sustained_chunks_s": round(chunks / wall, 2) if wall > 0 else 0.0,
    }


def open_lcd() -> LcdCommTuringUSB:
    lcd = LcdCommTuringUSB(
        com_port="AUTO",
        display_width=NATIVE_WIDTH,
        display_height=NATIVE_HEIGHT,
    )
    lcd.InitializeComm()
    lcd.SetOrientation(LCD_ORIENTATION)
    lcd.SetBrightness(DEFAULT_BRIGHTNESS)
    return lcd


def restore_still(lcd: LcdCommTuringUSB) -> None:
    """Leave a readable still after STOP_STREAM so the panel is not stuck mid-stream."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (NATIVE_WIDTH, NATIVE_HEIGHT), (28, 32, 40))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, NATIVE_WIDTH - 1, NATIVE_HEIGHT - 1), outline=(180, 180, 180), width=3)
    draw.text((NATIVE_WIDTH // 2, NATIVE_HEIGHT // 2), "H264 PROBE DONE", fill=(220, 220, 200), anchor="mm")
    lcd.DisplayPILImage(img)
    lcd.SetBrightness(DEFAULT_BRIGHTNESS)


def dry_run_report(clip_meta: dict, *, fps: int) -> dict:
    """No USB: describe how a live push would call the library."""
    return {
        "mode": "dry-run",
        "clip": clip_meta,
        "usb_opened": False,
        "would_call": {
            "preamble": ["111", "112", "13", "14 brightness", "41", "102 clear_image", f"15 frame_rate={fps}"],
            "negotiate": f"CMD_GET_H264_CHUNK_SIZE={CMD_GET_H264_CHUNK_SIZE} (default {DEFAULT_CHUNK})",
            "push": f"CMD_PLAY_H264_CHUNK={CMD_PLAY_H264_CHUNK} + annex-B payload",
            "flow": f"CMD_GET_STREAM_STATUS={CMD_GET_STREAM_STATUS} (queue depth resp[8]; delay if >3)",
            "stop": f"CMD_STOP_STREAM={CMD_STOP_STREAM}",
            "orientation": (
                f"encode {WIRE_W}x{WIRE_H}; LCD_ORIENTATION={LCD_ORIENTATION.name}; "
                "JPEG path rotates 270 for LANDSCAPE — H.264 path does not rotate"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TURZX H.264 probe skeleton (dry-run default)")
    parser.add_argument("--usb", action="store_true", help="Open panel and push (default: dry-run only)")
    parser.add_argument("--seconds", type=float, default=2.0, help="Synthetic clip length")
    parser.add_argument("--fps", type=int, default=25, help="Encode fps + cmd 15 value")
    parser.add_argument(
        "--out-h264",
        type=Path,
        default=OUT_DIR / "h264_probe_clip.h264",
        help="Annex-B output path",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=OUT_DIR / "h264_probe_results.json",
        help="Results JSON path",
    )
    parser.add_argument("--loop", action="store_true", help="Loop annex-B until Ctrl-C (USB only)")
    args = parser.parse_args()

    ffmpeg = require_ffmpeg()
    print(f"Building Annex-B clip → {args.out_h264} ({WIRE_W}x{WIRE_H}, {args.seconds}s @ {args.fps} fps)")
    clip_meta = build_annexb_clip(args.out_h264, seconds=args.seconds, fps=args.fps, ffmpeg=ffmpeg)
    print(f"  clip bytes={clip_meta['bytes']}")

    results: dict = {"clip": clip_meta, "usb": False}

    if not args.usb:
        results.update(dry_run_report(clip_meta, fps=args.fps))
        print("Dry-run complete (no USB). Pass --usb to push to the panel.")
    else:
        print("Opening USB (stop turzx-dashboard.service first)...")
        lcd = open_lcd()
        assert lcd.orientation == Orientation.LANDSCAPE
        results["usb"] = True
        try:
            t0 = time.perf_counter()
            video_preamble(lcd.dev, frame_rate=args.fps)
            chunk_size = negotiate_chunk_size(lcd.dev)
            t_ready = time.perf_counter()
            print(f"  negotiated chunk_size={chunk_size}")
            push = push_annexb_chunks(
                lcd.dev,
                args.out_h264,
                chunk_size=chunk_size,
                loop=args.loop,
            )
            push["preamble_ms"] = round((t_ready - t0) * 1000, 2)
            results["push"] = push
            print(
                f"  start_latency_ms={push['start_latency_ms']}  "
                f"sustained_MiB/s={push['sustained_mib_s']}  "
                f"chunks={push['chunks']}  flow_waits={push['flow_waits']}"
            )
            restore_still(lcd)
            results["restored_still"] = True
        except Exception as exc:
            results["error"] = repr(exc)
            try:
                write_to_device(
                    lcd.dev,
                    encrypt_command_packet(build_command_packet_header(CMD_STOP_STREAM)),
                )
            except Exception:
                pass
            raise
        finally:
            # Device handle is process-scoped; leave brightness/still as restored above.
            pass

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
