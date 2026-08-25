# TURZX ambient screens

Terminal apps on the USB panel (weathr, weatherspect, asciiquarium). This is how that path was built. **It is off the boot dashboard as of Aug 2026.** JPEG ambient plus view flips reset the panel on the hub shared with USB audio. Live loop is stats cards plus `Super+Shift+F` speedtest only. See [usb-stability](../usb-stability/) and [host-engine-refresh](../host-engine-refresh/).

Code still sits in `~/Documents/dashboard` (`ambient_cycle.py`, `term_capture.py`, peek scripts) if you want it later. `dashboard.py` no longer imports it.

## Start here

**Normal day now:** stats cards at 1 Hz. `Super+Shift+F` overlays Fast.com gauges, then cards return.

`Super+Shift+D` and `Super+Shift+N` are unbound. Peek and next-ambient scripts remain under `~/.config/hypr/scripts/` but do nothing unless you wire them again.

**Restart after code edits:**

```bash
systemctl --user restart turzx-dashboard.service
```

**Quick checks (only useful if you re-enable ambient):**

```bash
cat ~/.local/state/turzx/ambient.json
cat ~/.local/state/turzx/dashboard_peek.json
```

Black ambient app was almost always `TERM=dumb` or the wrong capture path. Troubleshooting is below.

## Ambient rotation (unused)

`ambient_cycle.py` keeps a 5 min timer in `~/.local/state/turzx/ambient.json`:

1. weathr — `weathr --metric --hide-location --silent` (HUD stripped from the top row and drawn beside the house)
2. weatherspect — `weatherspect`
3. asciiquarium — `asciiquarium`

`ambient_next.sh` used to be bound to `Super+Shift+N`. It still bumps the slot index if you run it by hand.

While ambient was showing, bonsai and `nvidia-smi` polling paused to save CPU.

Idle frames get a colour lift in `render_terminal()` (black floor → charcoal, then brightness/contrast via a cached LUT). That is separate from LCD brightness (`turzx-ctl brightness`). Tune `AMBIENT_LIFT_FLOOR` / `AMBIENT_BRIGHTNESS` / `AMBIENT_CONTRAST` in `renderer.py` if it still looks muddy.

## Game mode (disabled)

`game_mode.py` still exists. Auto ambient ↔ stats on game open/close reset the USB panel, so the loop never reads it.

## Sticky dashboard latch (disabled)

`toggle_dashboard_peek.sh` still flips `{ "enabled": true|false }` in `~/.local/state/turzx/dashboard_peek.json`. The live loop ignores that file. Stats are always on unless speedtest is running.

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
- weathr draws its HUD on row 1; at 24 rows that line sits above the house and was easy to lose when the frame was tightened. The dashboard strips that row and redraws condition + temp / wind + precip as two larger lines beside the house.

## App config

| App | Live config | Copy here |
|-----|-------------|-----------|
| weathr | `~/.config/weathr/config.toml` | [`weathr-config.toml`](weathr-config.toml) — needs `[location]` / `[units]` sections; flat keys failed to load |
| weatherspect | `~/.weatherspect` | — |
| asciiquarium | none | — |

## Hypr binds

Live file: `~/.config/caelestia/hypr-user.lua`. Snippet: [`hypr-user-binds.lua`](hypr-user-binds.lua) (speedtest only).

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
- [USB stability](../usb-stability/) — why ambient left the boot path
- [Speedtest widget](../../Speedtest-widget/) — `Super+Shift+F`
- [Process](../Process/) — USB orientation if the glass looks sideways
