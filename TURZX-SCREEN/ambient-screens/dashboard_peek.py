"""Watch ~/.local/state/turzx/dashboard_peek.json for a sticky stats latch.

Super+Shift+D toggles `{ "enabled": true|false }`. While enabled, the panel
stays on the stats dashboard until the shortcut is pressed again. No timer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

STATE_PATH = Path.home() / ".local" / "state" / "turzx" / "dashboard_peek.json"


@dataclass(frozen=True)
class DashboardPeekState:
    enabled: bool = False

    @property
    def visible(self) -> bool:
        return self.enabled


def load_dashboard_peek(path: Path = STATE_PATH) -> DashboardPeekState | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if "enabled" in data:
        return DashboardPeekState(enabled=bool(data.get("enabled")))
    # Legacy timed peek ({"until": ...}) — treat as off so we don't stick forever.
    return None


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
        if self.state is not None and self.state.visible:
            return self.state
        return None
