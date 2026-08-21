"""Watch ~/.local/state/turzx/speedtest.json for overlay takeover."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

STATE_PATH = Path.home() / ".local" / "state" / "turzx" / "speedtest.json"


@dataclass(frozen=True)
class SpeedtestState:
    active: bool = False
    phase: str = ""
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    error: str = ""
    until: float | None = None
    updated_at: float = 0.0

    @property
    def visible(self) -> bool:
        if self.active:
            return True
        if self.until is not None and self.until > time.time():
            return True
        return False


def load_speedtest_state(path: Path = STATE_PATH) -> SpeedtestState | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None

    def _float(key: str, default: float = 0.0) -> float:
        try:
            return float(data.get(key, default) or default)
        except (TypeError, ValueError):
            return default

    until_raw = data.get("until")
    until: float | None
    if until_raw is None:
        until = None
    else:
        try:
            until = float(until_raw)
        except (TypeError, ValueError):
            until = None

    return SpeedtestState(
        active=bool(data.get("active")),
        phase=str(data.get("phase") or ""),
        download_mbps=_float("download_mbps"),
        upload_mbps=_float("upload_mbps"),
        error=str(data.get("error") or ""),
        until=until,
        updated_at=_float("updated_at"),
    )


class SpeedtestWatcher:
    def __init__(self, path: Path = STATE_PATH) -> None:
        self.path = path
        self._mtime: float | None = None
        self.state: SpeedtestState | None = None

    def poll(self) -> SpeedtestState | None:
        try:
            mtime = self.path.stat().st_mtime if self.path.is_file() else None
        except OSError:
            mtime = None
        if mtime != self._mtime:
            self._mtime = mtime
            self.state = load_speedtest_state(self.path) if mtime is not None else None
        if self.state is not None and not self.state.visible:
            # Hold expired; drop so dashboard reverts even if file lingers
            return None
        return self.state if self.state and self.state.visible else None
