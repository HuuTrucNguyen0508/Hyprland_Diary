#!/usr/bin/env python3
"""TURZX refresh-upgrade spike: measure full-frame ceiling and partial-upload viability.

Phases:
  A — full-frame JPEG/PNG timing at several intervals
  B — DisplayPILImage(x,y) host-composite vs payload size; small JPEG alone
  C — send_frame_rate_command (cmd 15) effect on JPEG slideshow fps

Stop turzx-dashboard.service before running (USB exclusive).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TURING_ROOT = Path(__file__).resolve().parent.parent / "turing-smart-screen-python"
sys.path.insert(0, str(TURING_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from library.lcd.lcd_comm_turing_usb import (  # noqa: E402
    MAX_IMAGE_PAYLOAD_DEFAULT,
    LcdCommTuringUSB,
    _encode_jpeg_under_limit,
    _encode_png,
    send_frame_rate_command,
    send_jpeg,
    send_pil_image_auto,
)
import library.lcd.lcd_comm_turing_usb as turzx_usb  # noqa: E402

from dashboard import prepare_frame  # noqa: E402
from turzx_screen import (  # noqa: E402
    CONTENT_ROTATE,
    DEFAULT_CROP_ANCHOR,
    DEFAULT_CROP_NUDGE_X,
    DEFAULT_CROP_NUDGE_Y,
    DEFAULT_FIT,
    DEFAULT_NUDGE_X,
    DEFAULT_NUDGE_Y,
    DEFAULT_SCALE,
    LCD_ORIENTATION,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
)

FONT_DIR = TURING_ROOT / "res" / "fonts"
OUT_DIR = Path(__file__).resolve().parent / "diag"
PANEL_W, PANEL_H = NATIVE_WIDTH, NATIVE_HEIGHT

# Last payload size observed by instrumented send
_LAST_PAYLOAD: dict[str, int | str] = {"bytes": 0, "format": ""}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(FONT_DIR / "jetbrains-mono/JetBrainsMono-Bold.ttf"), size)
    except OSError:
        return ImageFont.load_default()


def instrument_send() -> None:
    """Wrap send_pil_image_auto / send_jpeg to record payload sizes."""

    def tracked_auto(dev, image: Image.Image, *, max_bytes: int = MAX_IMAGE_PAYLOAD_DEFAULT) -> None:
        png = _encode_png(image)
        if len(png) <= max_bytes:
            _LAST_PAYLOAD["bytes"] = len(png)
            _LAST_PAYLOAD["format"] = "png"
            _LAST_PAYLOAD["image_wh"] = f"{image.size[0]}x{image.size[1]}"
            turzx_usb.send_image(dev, png)
            return
        jpg = _encode_jpeg_under_limit(image, max_bytes=max_bytes, quality=90, subsampling=-1)
        _LAST_PAYLOAD["bytes"] = len(jpg)
        _LAST_PAYLOAD["format"] = "jpeg"
        _LAST_PAYLOAD["image_wh"] = f"{image.size[0]}x{image.size[1]}"
        send_jpeg(dev, jpg)

    turzx_usb.send_pil_image_auto = tracked_auto  # type: ignore[attr-defined]


def make_layout(frame_i: int, *, bg: tuple[int, int, int] = (30, 40, 50)) -> Image.Image:
    """1280x800 layout with changing counter (dashboard content space)."""
    img = Image.new("RGB", (PANEL_W, PANEL_H), bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, PANEL_W - 1, PANEL_H - 1), outline=(200, 200, 200), width=3)
    draw.text((PANEL_W // 2, PANEL_H // 2 - 40), "REFRESH PROBE", font=_font(48), fill=(240, 240, 240), anchor="mm")
    draw.text((PANEL_W // 2, PANEL_H // 2 + 30), f"frame {frame_i}", font=_font(64), fill=(180, 220, 140), anchor="mm")
    return img


def to_panel(layout: Image.Image) -> Image.Image:
    frame, _, _ = prepare_frame(
        layout,
        rotate=CONTENT_ROTATE,
        scale=DEFAULT_SCALE,
        zoom=1.0,
        fit=DEFAULT_FIT,
        nudge_x=DEFAULT_NUDGE_X,
        nudge_y=DEFAULT_NUDGE_Y,
        crop_nudge_x=DEFAULT_CROP_NUDGE_X,
        crop_nudge_y=DEFAULT_CROP_NUDGE_Y,
        crop_anchor=DEFAULT_CROP_ANCHOR,
        bg=layout.getpixel((0, 0)),
    )
    return frame


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))
    return ordered[idx]


def summarize(samples: list[dict]) -> dict:
    builds = [s["build_ms"] for s in samples]
    encodes = [s["encode_ms"] for s in samples]
    sends = [s["send_ms"] for s in samples]
    totals = [s["total_ms"] for s in samples]
    payloads = [s["payload_bytes"] for s in samples]
    wall = samples[-1]["t_end"] - samples[0]["t_start"] if samples else 0.0
    fps = (len(samples) / wall) if wall > 0 else 0.0
    return {
        "n": len(samples),
        "fps_achieved": round(fps, 2),
        "build_ms_median": round(statistics.median(builds), 2) if builds else 0,
        "encode_ms_median": round(statistics.median(encodes), 2) if encodes else 0,
        "send_ms_median": round(statistics.median(sends), 2) if sends else 0,
        "total_ms_median": round(statistics.median(totals), 2) if totals else 0,
        "total_ms_p95": round(pct(totals, 95), 2) if totals else 0,
        "payload_bytes_median": int(statistics.median(payloads)) if payloads else 0,
        "payload_format": samples[0]["payload_format"] if samples else "",
    }


def phase_a_burst(lcd: LcdCommTuringUSB, *, n: int, interval: float | None) -> dict:
    """Timed full-frame loop. interval=None means as-fast-as-possible."""
    samples: list[dict] = []
    label = "asap" if interval is None else f"{interval:g}s"
    print(f"\n=== Phase A: full-frame burst ({label}, n={n}) ===")
    for i in range(n):
        t0 = time.perf_counter()
        layout = make_layout(i)
        panel = to_panel(layout)
        t1 = time.perf_counter()

        # Encode timing separate from USB (same path as library)
        enc0 = time.perf_counter()
        png = _encode_png(panel)
        if len(png) <= MAX_IMAGE_PAYLOAD_DEFAULT:
            payload_bytes = len(png)
            payload_format = "png"
        else:
            jpg = _encode_jpeg_under_limit(panel, max_bytes=MAX_IMAGE_PAYLOAD_DEFAULT, quality=90, subsampling=-1)
            payload_bytes = len(jpg)
            payload_format = "jpeg"
        enc1 = time.perf_counter()

        send0 = time.perf_counter()
        lcd.DisplayPILImage(panel)
        send1 = time.perf_counter()
        # Prefer instrumented size if available
        if _LAST_PAYLOAD.get("bytes"):
            payload_bytes = int(_LAST_PAYLOAD["bytes"])
            payload_format = str(_LAST_PAYLOAD.get("format") or payload_format)

        samples.append(
            {
                "i": i,
                "t_start": t0,
                "t_end": send1,
                "build_ms": (t1 - t0) * 1000,
                "encode_ms": (enc1 - enc0) * 1000,
                "send_ms": (send1 - send0) * 1000,
                "total_ms": (send1 - t0) * 1000,
                "payload_bytes": payload_bytes,
                "payload_format": payload_format,
            }
        )
        if interval is not None:
            elapsed = time.perf_counter() - t0
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    summary = summarize(samples)
    print(
        f"  fps={summary['fps_achieved']}  "
        f"total_med={summary['total_ms_median']}ms  "
        f"p95={summary['total_ms_p95']}ms  "
        f"encode_med={summary['encode_ms_median']}ms  "
        f"send_med={summary['send_ms_median']}ms  "
        f"payload={summary['payload_bytes_median']} ({summary['payload_format']})"
    )
    return {"interval": interval, "label": label, "summary": summary, "samples": samples}


def phase_b_partial(lcd: LcdCommTuringUSB) -> dict:
    """Host-composite x,y paste vs raw small JPEG upload."""
    print("\n=== Phase B: partial / host-composite proof ===")
    results: dict = {"steps": []}

    # 1) Full solid green
    base = Image.new("RGB", (PANEL_W, PANEL_H), (20, 120, 60))
    draw = ImageDraw.Draw(base)
    draw.text((PANEL_W // 2, 40), "BASE GREEN — then patch", font=_font(28), fill=(255, 255, 255), anchor="mt")
    panel = to_panel(base)
    lcd.DisplayPILImage(panel)
    full_bytes = int(_LAST_PAYLOAD.get("bytes") or 0)
    full_wh = str(_LAST_PAYLOAD.get("image_wh") or "")
    results["steps"].append(
        {
            "name": "full_green",
            "payload_bytes": full_bytes,
            "payload_format": _LAST_PAYLOAD.get("format"),
            "image_wh": full_wh,
            "expect_glass": "solid green full screen",
        }
    )
    print(f"  full green: {_LAST_PAYLOAD}")
    time.sleep(1.5)

    # 2) Library DisplayPILImage with small patch at x,y (host pastes into current_state, sends ALL)
    patch = Image.new("RGB", (200, 120), (240, 40, 40))
    pd = ImageDraw.Draw(patch)
    pd.text((100, 60), "PATCH", font=_font(28), fill=(255, 255, 255), anchor="mm")
    # Note: DisplayPILImage coords are in LCD canvas space after SetOrientation.
    # Dashboard rotates content before send; here we paste on already-oriented current_state.
    # Reset state by full send already done; paste into library buffer:
    lcd.DisplayPILImage(patch, x=100, y=100)
    patch_via_lib_bytes = int(_LAST_PAYLOAD.get("bytes") or 0)
    results["steps"].append(
        {
            "name": "library_xy_paste",
            "payload_bytes": patch_via_lib_bytes,
            "payload_format": _LAST_PAYLOAD.get("format"),
            "image_wh": _LAST_PAYLOAD.get("image_wh"),
            "patch_size": "200x120",
            "paste_xy": [100, 100],
            "expect_glass": "red PATCH on green (host composite); payload ~full frame",
            "ratio_vs_full": round(patch_via_lib_bytes / full_bytes, 3) if full_bytes else None,
        }
    )
    print(f"  library x,y paste: {_LAST_PAYLOAD}  ratio={results['steps'][-1]['ratio_vs_full']}")
    time.sleep(2.0)

    # 3) Raw small JPEG only (no host paste) — does device place it or stretch/wipe?
    jpg = _encode_jpeg_under_limit(patch, max_bytes=MAX_IMAGE_PAYLOAD_DEFAULT, quality=90, subsampling=-1)
    send_jpeg(lcd.dev, jpg)
    results["steps"].append(
        {
            "name": "raw_small_jpeg_alone",
            "payload_bytes": len(jpg),
            "payload_format": "jpeg",
            "image_wh": "200x120",
            "expect_glass": "observe: stretch/wipe/misplace vs true corner overlay",
        }
    )
    print(f"  raw small JPEG alone: {len(jpg)} bytes — check glass visually")
    time.sleep(2.5)

    # Restore readable frame
    restore = make_layout(0, bg=(40, 40, 50))
    lcd.DisplayPILImage(to_panel(restore))

    # Verdict heuristic from sizes
    lib_is_full = full_bytes > 0 and patch_via_lib_bytes >= full_bytes * 0.7
    results["library_sends_full_frame"] = lib_is_full
    results["partial_via_library"] = False  # library always encodes current_state full canvas
    results["notes"] = (
        "DisplayPILImage(x,y) pastes on host then send_pil_image_auto(entire current_state). "
        "If library_xy_paste payload ≈ full_green, USB is not doing a region update."
    )
    return results


def phase_c_framerate(lcd: LcdCommTuringUSB, *, n: int = 15) -> dict:
    print("\n=== Phase C: send_frame_rate_command (cmd 15) ===")
    results: dict = {"bursts": []}
    for rate in (10, 25, 60):
        print(f"  cmd 15 frame_rate={rate}")
        send_frame_rate_command(lcd.dev, rate)
        time.sleep(0.2)
        burst = phase_a_burst(lcd, n=n, interval=None)
        results["bursts"].append({"frame_rate_cmd": rate, "summary": burst["summary"]})
    # Leave rate unset / video default irrelevant for JPEG path
    return results


def open_lcd() -> LcdCommTuringUSB:
    lcd = LcdCommTuringUSB(
        com_port="AUTO",
        display_width=NATIVE_WIDTH,
        display_height=NATIVE_HEIGHT,
    )
    lcd.InitializeComm()
    lcd.SetOrientation(LCD_ORIENTATION)
    lcd.SetBrightness(50)
    return lcd


def main() -> int:
    parser = argparse.ArgumentParser(description="TURZX refresh upgrade verification probe")
    parser.add_argument("--frames", type=int, default=20, help="Frames per Phase A burst")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=OUT_DIR / "refresh_probe_results.json",
        help="Write results JSON",
    )
    parser.add_argument("--skip-c", action="store_true", help="Skip frame-rate command phase")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    instrument_send()

    lcd = open_lcd()
    report: dict = {
        "panel": f"{NATIVE_WIDTH}x{NATIVE_HEIGHT}",
        "orientation": LCD_ORIENTATION.name,
        "content_rotate": CONTENT_ROTATE,
        "phases": {},
    }

    try:
        # Phase A
        a_runs = []
        for interval in (1.0, 0.5, 0.25, 0.1, None):
            a_runs.append(phase_a_burst(lcd, n=args.frames, interval=interval))
        report["phases"]["A"] = {"runs": [{"label": r["label"], "interval": r["interval"], "summary": r["summary"]} for r in a_runs]}

        asap = next(r for r in a_runs if r["interval"] is None)["summary"]
        report["phases"]["A"]["full_frame_ge_5fps"] = asap["fps_achieved"] >= 5.0

        # Phase B
        report["phases"]["B"] = phase_b_partial(lcd)

        # Phase C
        if not args.skip_c:
            report["phases"]["C"] = phase_c_framerate(lcd, n=min(12, args.frames))
            fps_vals = [b["summary"]["fps_achieved"] for b in report["phases"]["C"]["bursts"]]
            spread = max(fps_vals) - min(fps_vals) if fps_vals else 0
            report["phases"]["C"]["cmd15_changes_jpeg_fps"] = spread >= 1.0
        else:
            report["phases"]["C"] = {"skipped": True}

        # Overall verdict
        partial_ok = False  # TUR_USB library path is never true device partial
        if report["phases"]["B"].get("library_sends_full_frame"):
            partial_ok = False
        full_ok = report["phases"]["A"]["full_frame_ge_5fps"]

        if partial_ok:
            verdict = "partial_yes"
            verdict_text = (
                "Device/library supports region updates without full-frame USB. Dirty-rect redesign is viable."
            )
        elif full_ok:
            verdict = "partial_no_full_frame_yes"
            verdict_text = (
                "TUR_USB DisplayPILImage always uploads a full-canvas compressed frame "
                f"(asap ~{asap['fps_achieved']} fps). Higher refresh is possible via more full JPEGs "
                "(dual-rate / skip-unchanged), not true partial USB regions."
            )
        else:
            verdict = "neither_useful"
            verdict_text = (
                "Encode+USB could not sustain ≥5 fps full-frame with acceptable cost on this unit."
            )

        report["verdict"] = verdict
        report["verdict_text"] = verdict_text
        print("\n=== VERDICT ===")
        print(verdict)
        print(verdict_text)

    finally:
        lcd.closeSerial()

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
