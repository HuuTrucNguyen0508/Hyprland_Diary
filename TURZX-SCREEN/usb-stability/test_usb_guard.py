#!/usr/bin/env python3
"""USB reconnect helpers. No hardware."""

from __future__ import annotations

from usb_guard import refresh_interval, try_lcd_write, wait_until_stable


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


class FakeLcd:
    def __init__(self, *, fail_on: str = "brightness") -> None:
        self.fail_on = fail_on
        self.brightness_calls = 0
        self.display_calls = 0

    def SetBrightness(self, level: int) -> None:
        self.brightness_calls += 1
        if self.fail_on == "brightness":
            raise OSError(19, "No such device (it may have been disconnected)")

    def DisplayPILImage(self, _frame) -> None:
        self.display_calls += 1
        if self.fail_on == "display":
            raise OSError(19, "No such device (it may have been disconnected)")


def test_brightness_error_does_not_raise() -> None:
    lcd = FakeLcd(fail_on="brightness")
    ok, applied = try_lcd_write(lcd, frame=object(), brightness=50, applied_brightness=-1)
    assert ok is False
    assert applied == -1
    assert lcd.brightness_calls == 1
    assert lcd.display_calls == 0


def test_display_error_after_brightness() -> None:
    lcd = FakeLcd(fail_on="display")
    ok, applied = try_lcd_write(lcd, frame=object(), brightness=50, applied_brightness=-1)
    assert ok is False
    assert applied == 50
    assert lcd.display_calls == 1


def test_wait_rejects_flapping_device() -> None:
    clock = FakeClock()
    samples = [True, False, True, False, True]

    def present() -> bool:
        if samples:
            return samples.pop(0)
        return False

    ok = wait_until_stable(
        stable_s=1.5,
        timeout_s=3.0,
        poll_s=0.2,
        present=present,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert ok is False


def test_wait_accepts_stable_device() -> None:
    clock = FakeClock()
    ok = wait_until_stable(
        stable_s=1.5,
        timeout_s=3.0,
        poll_s=0.2,
        present=lambda: True,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    assert ok is True
    assert clock.t >= 1.5


def test_gpu_load_slows_idle_refresh() -> None:
    assert refresh_interval(
        speed_visible=False,
        busy=False,
        idle_interval=1.0,
        busy_interval=0.25,
        speedtest_interval=0.0,
        gpu_percent=8.0,
    ) == 1.0
    assert refresh_interval(
        speed_visible=False,
        busy=False,
        idle_interval=1.0,
        busy_interval=0.25,
        speedtest_interval=0.0,
        gpu_percent=91.0,
    ) == 5.0


def test_speedtest_stays_asap_under_gpu_load() -> None:
    assert refresh_interval(
        speed_visible=True,
        busy=True,
        idle_interval=1.0,
        busy_interval=0.25,
        speedtest_interval=0.0,
        gpu_percent=99.0,
    ) == 0.0


if __name__ == "__main__":
    tests = [
        test_brightness_error_does_not_raise,
        test_display_error_after_brightness,
        test_wait_rejects_flapping_device,
        test_wait_accepts_stable_device,
        test_gpu_load_slows_idle_refresh,
        test_speedtest_stays_asap_under_gpu_load,
    ]
    for test in tests:
        test()
        print(f"ok {test.__name__}")
    print(f"passed {len(tests)}")
