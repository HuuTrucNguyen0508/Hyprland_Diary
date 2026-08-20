# TURZX follows Caelestia

The USB dashboard already redraws about once a second. Instead of another watcher service, it just rereads `~/.local/state/caelestia/scheme.json` on each frame. Wallpaper changes and the screen catches up on the next tick.

USB, orientation, and letterbox setup live in [TURZX-SCREEN/Process](../../TURZX-SCREEN/Process/). This note is only colours.

| Piece | Path |
|--------|------|
| Dashboard | `~/Documents/dashboard/` |
| Palette code | `~/Documents/dashboard/theme.py` |
| Scheme | `~/.local/state/caelestia/scheme.json` |
| Fallback | Everforest Dark Medium, hardcoded |
| Service | `turzx-dashboard.service` |

No `caelestia-turzx-sync`. The process itself is the sync.

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

Missing or broken `scheme.json` → Everforest (`name=everforest-fallback`). That saved me a few times when Caelestia had not written the file yet at boot.

## Watch loop

`SchemeWatcher` compares mtime. No inotify.

```python
scheme = SchemeWatcher()
renderer = DashboardRenderer(..., palette=scheme.palette)

while not stop:
    renderer.palette = scheme.poll()
    # render + send to the panel
```

`renderer.py` paints from `self.palette`. That is the whole story.

## Run it

```bash
systemctl --user enable --now turzx-dashboard.service
```

Caelestia already updates `scheme.json` when the wallpaper changes. TURZX only has to be running.

## Check

```bash
jq '.name, .colours.primary, .colours.background' ~/.local/state/caelestia/scheme.json
```

Change wallpaper. Within about a second the cards and bars should shift. No restart.

Compared to the others: Cursor and SDDM ride a `postHook`, Zen has its own systemd unit, TURZX just keeps reading the same JSON the desktop already writes.

## Copies in this folder

| File | Live path |
|------|-----------|
| `theme.py` | `~/Documents/dashboard/theme.py` |
