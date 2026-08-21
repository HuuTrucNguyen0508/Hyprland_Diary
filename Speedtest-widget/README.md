# Speedtest widget (TURZX only)

Super+Shift+F runs a Fast.com speedtest on the TURZX panel only. No desktop overlay.

## How it works

Same engine idea as Omarchy Quattro, without the Quickshell dials on the main monitors:

1. `network-speedtest` saturates the link via Netflix Fast.com and prints Mbps once per second from interface byte counters.
2. `speedtest-session` runs download then upload (~5s each), writes `~/.local/state/turzx/speedtest.json`, then holds finals with `until = now+3` before clearing.
3. `turzx-dashboard` polls that JSON each frame; when `active` or `until` is in the future it renders dual gauges instead of the normal cards. While the gauges are up it runs **ASAP** full-frame refresh (no dirty-skip, `--speedtest-interval 0`), which tops out around ~5 fps on this USB path. Idle dashboard stays at 1 Hz.

USB stays exclusive to the dashboard.

## Bind

In `~/.config/caelestia/hypr-user.lua`:

```lua
hl.bind("SUPER + SHIFT + F", hl.dsp.exec_cmd("~/.config/hypr/scripts/toggle_speedtest.sh"))
```

Press again to abort (clears state immediately, no 3s hold).

## Install paths

| Piece | Live path |
|-------|-----------|
| Engine | `~/.local/bin/network-speedtest` |
| Session | `~/.local/bin/speedtest-session` |
| Toggle | `~/.config/hypr/scripts/toggle_speedtest.sh` |
| TURZX watcher | `~/Documents/dashboard/speedtest_state.py` |
| TURZX draw | `DashboardRenderer.render_speedtest` in `renderer.py` |
| Loop hook | `dashboard.py` polls `SpeedtestWatcher` |

After dashboard code changes: `systemctl --user restart turzx-dashboard.service`. After hypr-user.lua: `hyprctl reload`.

Optional leftover: `~/.config/quickshell/speedtest/` from an earlier desktop-overlay experiment. Unused; safe to delete.

## State JSON

```json
{
  "active": true,
  "phase": "down",
  "download_mbps": 412,
  "upload_mbps": 0,
  "error": "",
  "until": null,
  "updated_at": 1710000000.0
}
```

## Copies in this folder

Scripts and notes from setup. Prefer the live paths above if they diverge.
