#!/usr/bin/env python3
"""TURZX 8\" landscape system monitor — always 1280x800 wide layout."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from PIL import Image

TURING_ROOT = Path(__file__).resolve().parent.parent / "turing-smart-screen-python"
sys.path.insert(0, str(TURING_ROOT))

from library.lcd.lcd_comm import Orientation  # noqa: E402
from library.lcd.lcd_comm_turing_usb import LcdCommTuringUSB  # noqa: E402

from frame_dirty import BusyTracker, logical_dirty_key  # noqa: E402
from renderer import DashboardRenderer, HEIGHT, WIDTH  # noqa: E402
from settings import SettingsWatcher  # noqa: E402
from speedtest_state import SpeedtestWatcher  # noqa: E402
from stats import StatsCollector  # noqa: E402
from theme import SchemeWatcher  # noqa: E402
from turzx_screen import (  # noqa: E402
    CONTENT_ROTATE,
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
PANEL_W, PANEL_H = NATIVE_WIDTH, NATIVE_HEIGHT

VIEW_SPEEDTEST = "speedtest"
VIEW_STATS = "stats"


def rotate_clockwise(image: Image.Image, degrees: int) -> Image.Image:
    if degrees == 90:
        return image.transpose(Image.Transpose.ROTATE_270)
    if degrees == 180:
        return image.transpose(Image.Transpose.ROTATE_180)
    if degrees == 270:
        return image.transpose(Image.Transpose.ROTATE_90)
    return image


def apply_zoom(
    frame: Image.Image,
    zoom: float,
    crop_anchor: str = "center",
    crop_nudge_x: int = 0,
    crop_nudge_y: int = 0,
) -> Image.Image:
    """Magnify layout; crop window anchored so rotate-180 left edge is preserved."""
    if zoom == 1.0 and crop_nudge_x == 0 and crop_nudge_y == 0:
        return frame
    w, h = frame.size
    scaled = frame.resize((round(w * zoom), round(h * zoom)), Image.Resampling.LANCZOS)
    sw, sh = scaled.size
    max_left = max(0, sw - w)
    max_top = max(0, sh - h)

    if crop_anchor == "top-left":
        left, top = 0, 0
    elif crop_anchor == "top-right":
        left, top = max_left, 0
    elif crop_anchor == "bottom-left":
        left, top = 0, max_top
    elif crop_anchor == "bottom-right":
        left, top = max_left, max_top
    else:
        left, top = (sw - w) // 2, (sh - h) // 2

    left = max(0, min(left + crop_nudge_x, max_left))
    top = max(0, min(top + crop_nudge_y, max_top))
    return scaled.crop((left, top, left + w, top + h))


def scale_to_panel(
    frame: Image.Image,
    target_w: int,
    target_h: int,
    *,
    mode: str,
    fit: float,
    nudge_x: int,
    nudge_y: int,
    bg: tuple[int, int, int],
) -> tuple[Image.Image, int, int]:
    """Place landscape frame on panel; returns image and paste (x, y) for debugging."""
    if mode == "stretch":
        return frame.resize((target_w, target_h), Image.Resampling.LANCZOS), 0, 0

    src_w, src_h = frame.size
    base_scale = min(target_w / src_w, target_h / src_h) if mode == "letterbox" else max(
        target_w / src_w, target_h / src_h
    )
    scale = base_scale * (fit if mode == "letterbox" else 1.0)
    new_w = round(src_w * scale)
    new_h = round(src_h * scale)
    resized = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if mode == "cover":
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h)), 0, 0

    out = Image.new("RGB", (target_w, target_h), bg)
    cx = (target_w - new_w) // 2
    cy = (target_h - new_h) // 2
    x = cx + nudge_x
    y = cy + nudge_y
    out.paste(resized, (x, y))
    return out, x, y


def prepare_frame(
    frame: Image.Image,
    *,
    rotate: int,
    scale: str,
    zoom: float,
    fit: float,
    nudge_x: int,
    nudge_y: int,
    crop_nudge_x: int,
    crop_nudge_y: int,
    crop_anchor: str,
    bg: tuple[int, int, int],
) -> tuple[Image.Image, int, int]:
    if rotate:
        frame = rotate_clockwise(frame, rotate)
    frame = apply_zoom(frame, zoom, crop_anchor, crop_nudge_x, crop_nudge_y)
    return scale_to_panel(
        frame, PANEL_W, PANEL_H, mode=scale, fit=fit, nudge_x=nudge_x, nudge_y=nudge_y, bg=bg
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TURZX 8\" landscape dashboard (1280x800 layout)")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "preview.png")
    parser.add_argument(
        "--idle-interval",
        "--interval",
        type=float,
        default=1.0,
        dest="idle_interval",
        help="Sleep when idle (default: 1.0). --interval is an alias.",
    )
    parser.add_argument(
        "--busy-interval",
        type=float,
        default=0.25,
        help="Sleep during scheme-change burst (default: 0.25). Not used for speedtest.",
    )
    parser.add_argument(
        "--speedtest-interval",
        type=float,
        default=0.0,
        help="Sleep between frames while speedtest is on glass (default: 0 = ASAP / USB max)",
    )
    parser.add_argument(
        "--brightness",
        type=int,
        default=None,
        help="LCD brightness 0-100 (default: ~/.config/turzx/config.json, else 50)",
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--rotate", type=int, default=CONTENT_ROTATE, choices=(0, 90, 180, 270))
    parser.add_argument(
        "--scale",
        choices=("stretch", "letterbox", "cover"),
        default=DEFAULT_SCALE,
        help="Fit mode (default: letterbox)",
    )
    parser.add_argument("--zoom", type=float, default=DEFAULT_ZOOM, help="Layout magnification (default: 1.20)")
    parser.add_argument(
        "--fit",
        type=float,
        default=DEFAULT_FIT,
        help="Letterbox scale fraction (default: 1.0 = full 800px width)",
    )
    parser.add_argument(
        "--crop-anchor",
        choices=("center", "top-left", "top-right", "bottom-left", "bottom-right"),
        default=DEFAULT_CROP_ANCHOR,
        help="Zoom crop anchor (default: top-right keeps physical left after rotate 180)",
    )
    parser.add_argument(
        "--nudge-x",
        type=int,
        default=DEFAULT_NUDGE_X,
        help="Pixels from center, negative=left (default: 0)",
    )
    parser.add_argument(
        "--nudge-y",
        type=int,
        default=DEFAULT_NUDGE_Y,
        help="Pixels from center, negative=up (default: 0)",
    )
    parser.add_argument(
        "--crop-nudge-x",
        type=int,
        default=DEFAULT_CROP_NUDGE_X,
        help="Zoom crop shift from center, pixels (default: 0)",
    )
    parser.add_argument(
        "--crop-nudge-y",
        type=int,
        default=DEFAULT_CROP_NUDGE_Y,
        help="Zoom crop shift from center, pixels (default: 0)",
    )
    return parser.parse_args()



def open_lcd() -> LcdCommTuringUSB:
    """Open / re-open the TURZX USB handle (needed after hub blips)."""
    lcd = LcdCommTuringUSB(
        com_port="AUTO",
        display_width=NATIVE_WIDTH,
        display_height=NATIVE_HEIGHT,
    )
    lcd.InitializeComm()
    lcd.SetOrientation(LCD_ORIENTATION)
    return lcd


def close_lcd(lcd: LcdCommTuringUSB | None) -> None:
    if lcd is None:
        return
    try:
        lcd.closeSerial()
    except Exception as exc:
        print(f"USB close ignored: {exc}")


def main() -> int:
    args = parse_args()
    scheme = SchemeWatcher()
    settings_watch = SettingsWatcher()
    speedtest_watch = SpeedtestWatcher()
    renderer = DashboardRenderer(FONT_DIR, palette=scheme.palette)
    collector = StatsCollector()
    busy = BusyTracker()
    last_dirty: tuple | None = None
    stop = False

    def handle_signal(_signum, _frame) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    lcd: LcdCommTuringUSB | None = None
    applied_brightness = -1
    usb_backoff_s = 1.0
    last_view: str | None = None
    if not args.preview:
        print(f"palette={scheme.palette.name}")
        print("views=stats,speedtest (ambient off)")
        try:
            lcd = open_lcd()
            print("USB connected")
        except Exception as exc:
            print(f"USB open failed ({exc}); retrying")

    try:
        while not stop:
            renderer.palette = scheme.poll()
            settings = settings_watch.poll()
            speed_state = speedtest_watch.poll()

            # Priority: speedtest overlay, otherwise always-on stats.
            # Ambient / peek / game-mode flips were resetting USB on the shared hub.
            if speed_state is not None and speed_state.visible:
                view = VIEW_SPEEDTEST
            else:
                view = VIEW_STATS

            if view != last_view:
                print(f"view {last_view or '-'} -> {view}")
                if last_view is not None:
                    time.sleep(0.35)
                last_view = view
                last_dirty = None

            speed_visible = view == VIEW_SPEEDTEST
            if speed_visible:
                interval = args.speedtest_interval
            elif busy.is_busy(False):
                interval = args.busy_interval
            else:
                interval = args.idle_interval

            brightness = args.brightness if args.brightness is not None else settings.brightness
            if lcd is not None and brightness != applied_brightness:
                lcd.SetBrightness(brightness)
                applied_brightness = brightness

            stats = collector.poll(settings)
            busy.note_palette(renderer.palette)
            dirty = logical_dirty_key(renderer.palette, speed_state, stats, view=view)

            if (
                dirty == last_dirty
                and not speed_visible
                and not args.once
                and not args.preview
            ):
                time.sleep(interval)
                continue

            if speed_state is not None:
                layout = renderer.render_speedtest(speed_state)
            else:
                layout = renderer.render(stats)

            frame, paste_x, paste_y = prepare_frame(
                layout,
                rotate=args.rotate,
                scale=args.scale,
                zoom=args.zoom,
                fit=args.fit,
                nudge_x=args.nudge_x,
                nudge_y=args.nudge_y,
                crop_nudge_x=args.crop_nudge_x,
                crop_nudge_y=args.crop_nudge_y,
                crop_anchor=args.crop_anchor,
                bg=renderer.palette.bg,
            )
            assert frame.size == (PANEL_W, PANEL_H)

            if not args.preview and lcd is not None and args.once:
                print(
                    f"layout={WIDTH}x{HEIGHT}  panel={PANEL_W}x{PANEL_H}  "
                    f"{LCD_ORIENTATION.name}  rotate={args.rotate}°  scale={args.scale}  "
                    f"zoom={args.zoom}  fit={args.fit}  crop={args.crop_anchor}  "
                    f"paste=({paste_x},{paste_y})  nudge=({args.nudge_x},{args.nudge_y})"
                )

            if args.preview:
                frame.save(args.output)
                print(f"Saved {args.output} paste=({paste_x},{paste_y})")
            elif lcd is None:
                time.sleep(usb_backoff_s)
                try:
                    lcd = open_lcd()
                    usb_backoff_s = 1.0
                    last_dirty = None
                    print("USB reconnected")
                except Exception as reopen_exc:
                    print(f"USB reconnect failed: {reopen_exc}")
                    usb_backoff_s = min(30.0, usb_backoff_s * 2)
                continue
            else:
                try:
                    lcd.DisplayPILImage(frame)
                    usb_backoff_s = 1.0
                except Exception as exc:
                    # Stale handle after USB blip — reopen instead of spinning on Errno 19
                    print(f"USB display failed ({exc}); reconnecting in {usb_backoff_s:.0f}s")
                    close_lcd(lcd)
                    lcd = None
                    applied_brightness = -1
                    last_dirty = None
                    time.sleep(usb_backoff_s)
                    usb_backoff_s = min(30.0, usb_backoff_s * 2)
                    continue

            last_dirty = dirty

            if args.once:
                break
            if interval > 0:
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        collector.close()
        close_lcd(lcd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
