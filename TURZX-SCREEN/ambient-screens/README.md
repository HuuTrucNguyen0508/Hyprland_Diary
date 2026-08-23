# TURZX ambient screens

When the USB panel has nothing urgent to show, it cycles terminal apps (weather, ascii art) instead of the stats dashboard. This entry covers that rotation, plus hotkeys that pull the stats view back.

Added Aug 2026. Live code: `~/Documents/dashboard`. Copies in this folder are snapshots only.

## Start here

**Normal day:** stats cards at 1 Hz when you are at the desktop. When you walk away from that, the panel rotates weathr (5 min) → weatherspect (5 min) → asciiquarium (5 min).

**Overrides (highest wins):**

| You do / what happens | Panel shows |
|------------------------|-------------|
| `Super+Shift+F` speedtest running | Dual gauges, full USB speed |
| `Super+Shift+D` | Stats cards for 10 s (press again to extend) |
| Fullscreen game (Proton/Steam/Lutris) or Caelestia game-mode toggle | Stats cards |
| None of the above | Ambient app |

**Hotkeys:** `Super+Shift+D` peek stats · `Super+Shift+N` next ambient app · `Super+Shift+F` speedtest (see [Speedtest widget](../../Speedtest-widget/)).

**Restart after code edits:**

```bash
systemctl --user restart turzx-dashboard.service
```

**Quick checks:**

```bash
# Which ambient slot is active?
cat ~/.local/state/turzx/ambient.json

# Is game mode logic firing? (fullscreen ZZZ → true even if Caelestia toggle is off)
python3 -c "import sys; sys.path.insert(0,'$HOME/Documents/dashboard'); from game_mode import GameModeWatcher; print(GameModeWatcher()._read_enabled())"

# Black ambient app? Almost always TERM=dumb or wrong capture path — see troubleshooting below.
```

## Ambient rotation

`ambient_cycle.py` keeps a 5 min timer in `~/.local/state/turzx/ambient.json`:

1. weathr — `weathr --metric --hide-hud --hide-location --silent`
2. weatherspect — `weatherspect`
3. asciiquarium — `asciiquarium`

`ambient_next.sh` (bound to `Super+Shift+N`) bumps the slot index and resets the timer. The dashboard kills and respawns the capture process on the next poll.

While ambient is showing, bonsai and `nvidia-smi` polling pause to save CPU.

## Game mode

Stats on the panel while you play. `game_mode.py` returns true if any of these match:

1. Caelestia toggle — `qs -c caelestia ipc call gameMode isEnabled` prints `true`
2. Fullscreen game on Hyprland — `hyprctl clients -j`, any client with `fullscreen >= 1` and class starting with `steam_app_`, `gamescope`, `lutris`, or `heroic` (ZZZ shows up as `steam_app_default`)
3. Shell dead fallback — Hypr animations off and tearing on

Item 2 exists because the Caelestia toggle is manual. Proton games never flipped it for you.

## Dashboard peek

`toggle_dashboard_peek.sh` writes `{ "until": <now + 10> }` to `~/.local/state/turzx/dashboard_peek.json`. Repeat press pushes `until` forward another 10 s.

## Terminal capture (why this was painful)

weathr draws plain text. weatherspect and asciiquarium use curses. A bare Python PTY gave a black panel or a single flickering line at the bottom.

Working path in `term_capture.py`:

```text
script -q -c 'export TERM=xterm-256color COLORTERM=truecolor; stty cols 80 rows 24; exec <app>' /dev/null
```

Then read the pipe with `select` + `os.read()` on the fd. Do not use `proc.stdout.read()` on a buffered stream; it hangs.

Gotchas we hit:

- Inherited `TERM=dumb` from the service environment → curses barely painted. Force `xterm-256color` inside the shell command, not only in `Popen` env.
- `--ambient-interval 0` on the dashboard loop. `poll()` already waits ~0.2 s on `select`. An extra sleep broke animation timing.
- Grid is 80×24. `render_terminal()` in `renderer.py` stretches cells to 1280×800.

## App config

| App | Live config | Copy here |
|-----|-------------|-----------|
| weathr | `~/.config/weathr/config.toml` | [`weathr-config.toml`](weathr-config.toml) — needs `[location]` / `[units]` sections; flat keys failed to load |
| weatherspect | `~/.weatherspect` | — |
| asciiquarium | none | — |

## Hypr binds

Live file: `~/.config/caelestia/hypr-user.lua`. Snippet: [`hypr-user-binds.lua`](hypr-user-binds.lua).

After editing binds: `hyprctl reload`

## Live paths

| Piece | Path |
|-------|------|
| Main loop | `~/Documents/dashboard/dashboard.py` |
| Script capture + ANSI grid | `~/Documents/dashboard/term_capture.py` |
| Rotation | `~/Documents/dashboard/ambient_cycle.py` |
| Game detection | `~/Documents/dashboard/game_mode.py` |
| Peek watcher | `~/Documents/dashboard/dashboard_peek.py` |
| Terminal draw | `~/Documents/dashboard/renderer.py` |
| Peek script | `~/.config/hypr/scripts/toggle_dashboard_peek.sh` |
| Next ambient | `~/.config/hypr/scripts/ambient_next.sh` |
| Service | `~/.config/systemd/user/turzx-dashboard.service` |

Dual-rate JPEG loop and dirty skip: [host-engine-refresh](../host-engine-refresh/).

## Copies in this folder

Python modules, Hypr scripts, weathr config, bind snippet.

## Related

- [Host-engine refresh](../host-engine-refresh/) — main dashboard loop, speedtest ASAP mode
- [Speedtest widget](../../Speedtest-widget/) — `Super+Shift+F`
- [Process](../Process/) — USB orientation if the glass looks sideways
