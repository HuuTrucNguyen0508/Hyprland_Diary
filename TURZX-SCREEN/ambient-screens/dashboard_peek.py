"""Watch ~/.local/state/turzx/dashboard_peek.json for a temporary stats view."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

STATE_PATH = Path.home() / ".local" / "state" / "turzx" / "dashboard_peek.json"


@dataclass(frozen=True)
class DashboardPeekState:
    until: float | None = None

    @property
    def visible(self) -> bool:
        return self.until is not None and self.until > time.time()


def load_dashboard_peek(path: Path = STATE_PATH) -> DashboardPeekState | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    until_raw = data.get("until")
    if until_raw is None:
        return None
    try:
        until = float(until_raw)
    except (TypeError, ValueError):
        return None
    return DashboardPeekState(until=until)


class DashboardPeekWatcher:
    def __init__(self, path: Path = STATE_PATH) -> None:
        self.path = path
        self._mtime: float | None = None
        self.state: DashboardPeekState | None = None

    def poll(self) -> DashboardPeekState | None:
        try:
            mtime = self.path.stat().st_mtime if self.path.is_file() else None
        except OSError:
            mtime = None
        if mtime != self._mtime:
            self._mtime = mtime
            self.state = load_dashboard_peek(self.path) if mtime is not None else None
        if self.state is not None and not self.state.visible:
            return None
        return self.state if self.state and self.state.visible else None
