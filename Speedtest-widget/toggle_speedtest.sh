#!/usr/bin/env bash
# Toggle Fast.com speedtest on the TURZX panel only (no desktop overlay).

set -euo pipefail

RUNTIME="${XDG_RUNTIME_DIR:-/tmp}"
SESS_PIDFILE="$RUNTIME/speedtest-session.pid"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/turzx/speedtest.json"
SESSION="$HOME/.local/bin/speedtest-session"

session_running() {
  [[ -f $SESS_PIDFILE ]] || return 1
  local pid
  pid=$(cat "$SESS_PIDFILE" 2>/dev/null || true)
  [[ -n ${pid:-} ]] && kill -0 "$pid" 2>/dev/null
}

stop_it() {
  if session_running; then
    kill "$(cat "$SESS_PIDFILE")" 2>/dev/null || true
    sleep 0.25
  fi
  # Drop any leftover desktop overlay from earlier builds
  qs kill -c speedtest 2>/dev/null || true
  rm -f "$SESS_PIDFILE" "$STATE"
}

if session_running; then
  stop_it
  exit 0
fi

# Also treat an active state file as "running" (session between phases)
if [[ -f $STATE ]]; then
  stop_it
  exit 0
fi

rm -f "$STATE"
"$SESSION" >/dev/null 2>&1 &
echo $! >"$SESS_PIDFILE"
exit 0
