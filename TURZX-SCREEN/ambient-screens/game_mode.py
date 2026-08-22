"""Poll Caelestia game mode and fullscreen games for TURZX view switching."""

from __future__ import annotations

import json
import subprocess
import time

_GAME_CLASS_PREFIXES = (
    "steam_app_",
    "gamescope",
    "lutris",
    "heroic",
)


class GameModeWatcher:
    def __init__(self, *, poll_interval: float = 2.0) -> None:
        self._poll_interval = poll_interval
        self._last_check = 0.0
        self._enabled = False

    def poll(self) -> bool:
        now = time.monotonic()
        if now - self._last_check < self._poll_interval:
            return self._enabled
        self._last_check = now
        self._enabled = self._read_enabled()
        return self._enabled

    def _read_enabled(self) -> bool:
        if self._caelestia_enabled():
            return True
        if self._fullscreen_game():
            return True
        return self._hypr_tuning_fallback()

    @staticmethod
    def _caelestia_enabled() -> bool:
        try:
            result = subprocess.run(
                ["qs", "-c", "caelestia", "ipc", "call", "gameMode", "isEnabled"],
                capture_output=True,
                text=True,
                timeout=1.5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip().lower() == "true"
        except (subprocess.SubprocessError, OSError):
            pass
        return False

    @staticmethod
    def _fullscreen_game() -> bool:
        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return False
            clients = json.loads(result.stdout)
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            return False

        for client in clients:
            if not client.get("mapped", True):
                continue
            if client.get("fullscreen", 0) < 1:
                continue
            window_class = (client.get("class") or "").lower()
            if any(window_class.startswith(prefix) for prefix in _GAME_CLASS_PREFIXES):
                return True
        return False

    @staticmethod
    def _hypr_tuning_fallback() -> bool:
        try:
            anim = subprocess.run(
                ["hyprctl", "getoption", "animations:enabled"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
            tear = subprocess.run(
                ["hyprctl", "getoption", "general:allow_tearing"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except (subprocess.SubprocessError, OSError):
            return False
        anim_off = "bool: false" in (anim.stdout or "").lower()
        tear_on = "bool: true" in (tear.stdout or "").lower()
        return anim_off and tear_on
