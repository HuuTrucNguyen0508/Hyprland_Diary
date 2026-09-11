"""Keep TURZX USB I/O from crashing the dashboard after a hub blip."""

from __future__ import annotations

import time
from collections.abc import Callable

USB_VENDOR = 0x1CBE
USB_PRODUCT = 0x0080
USB_SETTLE_S = 1.5
USB_SETTLE_TIMEOUT_S = 3.0
USB_SETTLE_POLL_S = 0.2
GPU_LOAD_PCT = 40.0
GPU_LOAD_INTERVAL_S = 5.0


def device_present() -> bool:
    """True if 1cbe:0080 is on the bus. Does not set configuration."""
    try:
        import usb.core
    except ImportError:
        return False
    try:
        return usb.core.find(idVendor=USB_VENDOR, idProduct=USB_PRODUCT) is not None
    except Exception:
        return False


def wait_until_stable(
    stable_s: float = USB_SETTLE_S,
    timeout_s: float = USB_SETTLE_TIMEOUT_S,
    poll_s: float = USB_SETTLE_POLL_S,
    *,
    present: Callable[[], bool] = device_present,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> bool:
    """True if the panel stays present for stable_s within timeout_s."""
    deadline = monotonic() + timeout_s
    seen_since: float | None = None
    while monotonic() < deadline:
        if present():
            now = monotonic()
            if seen_since is None:
                seen_since = now
            elif now - seen_since >= stable_s:
                return True
        else:
            seen_since = None
        sleep(poll_s)
    return False


def refresh_interval(
    *,
    speed_visible: bool,
    busy: bool,
    idle_interval: float,
    busy_interval: float,
    speedtest_interval: float,
    gpu_percent: float | None,
    gpu_load_pct: float = GPU_LOAD_PCT,
    gpu_load_interval: float = GPU_LOAD_INTERVAL_S,
) -> float:
    """Pick USB sleep. GPU load slows JPEG so the shared hub does not reset."""
    if speed_visible:
        return speedtest_interval
    interval = busy_interval if busy else idle_interval
    if gpu_percent is not None and gpu_percent >= gpu_load_pct:
        return max(interval, gpu_load_interval)
    return interval


def try_lcd_write(lcd, frame, brightness: int, applied_brightness: int) -> tuple[bool, int]:
    """Set brightness and push a frame. Never raises. False means drop the handle."""
    try:
        if brightness != applied_brightness:
            lcd.SetBrightness(brightness)
            applied_brightness = brightness
        lcd.DisplayPILImage(frame)
        return True, applied_brightness
    except Exception as exc:
        print(f"USB display failed ({exc})")
        return False, applied_brightness
