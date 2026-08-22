#!/usr/bin/env bash
# Toggle opt-in H.264 live dashboard on the TURZX panel.
# JPEG dual-rate (turzx-dashboard.service) remains the boot/always-on default.
#
# Start: stop JPEG service, run turzx_h264_live.py until stopped.
# Stop (press again): SIGTERM live process → STOP+still restore → start JPEG service.

set -euo pipefail

STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/turzx"
PIDFILE="$STATE_DIR/h264_live.pid"
LOG="${XDG_RUNTIME_DIR:-/tmp}/turzx-h264-live.log"
DASHBOARD_DIR="$HOME/Documents/dashboard"
PY="$DASHBOARD_DIR/.venv/bin/python"
LIVE="$DASHBOARD_DIR/turzx_h264_live.py"
SERVICE="turzx-dashboard.service"
FPS="${TURZX_H264_FPS:-15}"

mkdir -p "$STATE_DIR"

live_running() {
  [[ -f $PIDFILE ]] || return 1
  local pid
  pid=$(cat "$PIDFILE" 2>/dev/null || true)
  [[ -n ${pid:-} ]] && kill -0 "$pid" 2>/dev/null
}

stop_live() {
  if live_running; then
    local pid
    pid=$(cat "$PIDFILE")
    kill -TERM "$pid" 2>/dev/null || true
    # Wait for STOP + still restore (finally in turzx_h264_live.py)
    local i
    for i in $(seq 1 40); do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 0.25
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PIDFILE"
  systemctl --user start "$SERVICE" || true
}

if live_running; then
  stop_live
  exit 0
fi

# Stale pidfile
rm -f "$PIDFILE"

if [[ ! -x $PY ]]; then
  echo "ERROR: missing venv python at $PY" >&2
  exit 1
fi
if [[ ! -f $LIVE ]]; then
  echo "ERROR: missing $LIVE" >&2
  exit 1
fi

systemctl --user stop "$SERVICE"
# Give the JPEG process time to release USB
sleep 0.5

# --seconds 0 = run until SIGTERM from this toggle
nohup "$PY" "$LIVE" --seconds 0 --fps "$FPS" >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
exit 0
