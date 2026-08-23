# TURZX follows Caelestia

The USB panel card colours track the same `scheme.json` file as the rest of the desktop. No separate sync daemon.

USB orientation and letterbox: [TURZX Process](../../TURZX-SCREEN/Process/). Ambient / game mode / speedtest views: [host-engine-refresh](../../TURZX-SCREEN/host-engine-refresh/).

## Start here

The dashboard reads `~/.local/state/caelestia/scheme.json` every frame (~1 Hz idle). Change wallpaper → colours update on the next tick. No restart.

```bash
systemctl --user is-active turzx-dashboard.service
jq '.name, .colours.primary' ~/.local/state/caelestia/scheme.json
```

Change wallpaper. Within about a second the TURZX cards and bars should shift. No restart.

Broken or missing `scheme.json` → hardcoded Everforest fallback (`name=everforest-fallback`).

| Piece | Path |
|-------|------|
| Dashboard | `~/Documents/dashboard/` |
| Palette code | `~/Documents/dashboard/theme.py` |
| Scheme | `~/.local/state/caelestia/scheme.json` |
| Service | `turzx-dashboard.service` |

## Mapping

`theme.py` loads `colours` (or `colors`) from the scheme and maps Material-style keys onto dashboard roles. First key that exists wins:

| Role | Keys tried |
|------|------------|
| `bg` | `base`, `background`, `surface` |
| `panel` | `surfaceContainer`, `surface0`, `surfaceContainerLow` |
| `panel_border` | `outlineVariant`, `overlay0`, `outline` |
| `bar_track` | `surface1`, `surface2`, `surfaceBright` |
| `spark_bg` | `crust`, `mantle`, `surfaceDim` |
| `text` | `text`, `onSurface`, `onBackground` |
| `muted` | `subtext1`, `onSurfaceVariant`, `subtext0` |
| `accent` | `primary`, `green` |
| `cpu` | `blue`, `sapphire`, `term4` |
| `gpu` | `green`, `term2`, `success` |
| `ram` | `mauve`, `lavender`, `pink` |
| `disk` | `peach`, `error`, `maroon` |
| `net_down` | `teal`, `sky`, `sapphire` |
| `net_up` | `yellow`, `pink`, `tertiary` |

## Watch loop

`SchemeWatcher` compares mtime. No inotify.

```python
scheme = SchemeWatcher()
renderer = DashboardRenderer(..., palette=scheme.palette)

while not stop:
    renderer.palette = scheme.poll()
    # render + send to the panel
```

Compared to the others: Cursor and SDDM ride a `postHook`, Zen has its own systemd unit, TURZX just keeps reading the same JSON the desktop already writes.

## Run it

```bash
systemctl --user enable --now turzx-dashboard.service
```

## Copies in this folder

| File | Live path |
|------|-----------|
| `theme.py` | `~/Documents/dashboard/theme.py` |
