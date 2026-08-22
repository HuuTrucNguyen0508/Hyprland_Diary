"""Logical dirty fingerprint and busy-interval helpers for the TURZX dashboard."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime

from speedtest_state import SpeedtestState
from stats import DashboardStats
from theme import Palette

SCHEME_BUSY_BURST_S = 8.0

_PALETTE_RGB_FIELDS = (
    "bg",
    "panel",
    "panel_border",
    "bar_track",
    "spark_bg",
    "text",
    "muted",
    "accent",
    "cpu",
    "gpu",
    "ram",
    "disk",
    "net_down",
    "net_up",
)


def palette_identity(palette: Palette) -> tuple[str, str]:
    """Return (scheme name, content hash) for change detection."""
    parts = [palette.name]
    for key in _PALETTE_RGB_FIELDS:
        parts.append(f"{key}={getattr(palette, key)}")
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]
    return palette.name, digest


def _round_pct(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value))


def _round_rate(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 1)


def _round_temp(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value))


def speedtest_fingerprint(state: SpeedtestState | None) -> tuple:
    if state is None:
        return (False, "", 0.0, 0.0, "", None)
    return (
        bool(state.active),
        str(state.phase or ""),
        round(float(state.download_mbps), 1),
        round(float(state.upload_mbps), 1),
        str(state.error or ""),
        state.until,
    )


def rounded_stats_fingerprint(stats: DashboardStats) -> tuple:
    """CPU/GPU/mem/disk % nearest 1; net nearest 0.1; temps nearest 1."""
    return (
        _round_pct(stats.cpu_percent),
        _round_pct(stats.gpu_percent),
        _round_pct(stats.ram_percent),
        _round_pct(stats.disk_percent),
        _round_pct(stats.ssd.percent) if stats.ssd.mounted else None,
        _round_pct(stats.nvme.percent) if stats.nvme.mounted else None,
        _round_pct(stats.hdd.percent) if stats.hdd.mounted else None,
        _round_rate(stats.net_down_kbps),
        _round_rate(stats.net_up_kbps),
        _round_temp(stats.cpu_temp),
        _round_temp(stats.gpu_temp),
    )


def logical_dirty_key(
    palette: Palette,
    speed: SpeedtestState | None,
    stats: DashboardStats,
    *,
    view: str = "stats",
    now: datetime | None = None,
) -> tuple:
    """Fingerprint compared before render/USB send. Unchanged => skip both."""
    name, digest = palette_identity(palette)
    clock = (now or datetime.now()).strftime("%H:%M")
    return (
        view,
        name,
        digest,
        speedtest_fingerprint(speed),
        clock,
        rounded_stats_fingerprint(stats),
    )


@dataclass
class BusyTracker:
    """Busy while speedtest is visible, or for 8s after a scheme identity change."""

    burst_s: float = SCHEME_BUSY_BURST_S
    _last_identity: tuple[str, str] | None = field(default=None, init=False, repr=False)
    _busy_until: float = field(default=0.0, init=False, repr=False)

    def note_palette(self, palette: Palette, *, now: float | None = None) -> None:
        identity = palette_identity(palette)
        if self._last_identity is None:
            self._last_identity = identity
            return
        if identity != self._last_identity:
            self._last_identity = identity
            t = time.monotonic() if now is None else now
            self._busy_until = t + self.burst_s

    def is_busy(self, speed_visible: bool, *, now: float | None = None) -> bool:
        t = time.monotonic() if now is None else now
        return bool(speed_visible) or t < self._busy_until
