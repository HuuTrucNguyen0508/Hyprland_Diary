#!/usr/bin/env bash
# Show the TURZX stats dashboard for 10 seconds (extends on repeat press).

set -euo pipefail

STATE="${XDG_STATE_HOME:-$HOME/.local/state}/turzx/dashboard_peek.json"
UNTIL=$(python3 - <<'PY'
import json
import time
from pathlib import Path

path = Path.home() / ".local/state/turzx/dashboard_peek.json"
path.parent.mkdir(parents=True, exist_ok=True)
until = time.time() + 10.0
path.write_text(json.dumps({"until": until}), encoding="utf-8")
print(until)
PY
)

exit 0
