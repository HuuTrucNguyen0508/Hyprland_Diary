#!/usr/bin/env bash
# Toggle TURZX stats dashboard on/off (sticky until pressed again).
# Bound in ~/.config/caelestia/hypr-user.lua as SUPER + SHIFT + D.

set -euo pipefail

STATE="${XDG_STATE_HOME:-$HOME/.local/state}/turzx/dashboard_peek.json"
mkdir -p "$(dirname "$STATE")"

python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".local/state/turzx/dashboard_peek.json"
path.parent.mkdir(parents=True, exist_ok=True)

enabled = False
if path.is_file():
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            enabled = bool(data.get("enabled", False))
    except (OSError, json.JSONDecodeError):
        enabled = False

enabled = not enabled
path.write_text(json.dumps({"enabled": enabled}), encoding="utf-8")
print("dashboard=on" if enabled else "dashboard=off")
PY
