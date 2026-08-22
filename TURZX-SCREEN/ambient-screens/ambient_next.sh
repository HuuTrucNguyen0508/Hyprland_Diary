#!/usr/bin/env bash
# Advance the TURZX ambient screen to the next app.

set -euo pipefail

python3 - <<'PY'
import json
import time
from pathlib import Path

path = Path.home() / ".local/state/turzx/ambient.json"
slots = 3
index = 0
if path.is_file():
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        index = int(data.get("slot_index", 0)) % slots
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
index = (index + 1) % slots
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    json.dumps({"slot_index": index, "slot_started": time.time()}),
    encoding="utf-8",
)
PY
