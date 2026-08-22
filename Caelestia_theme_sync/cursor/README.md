# Cursor follows Caelestia

Caelestia has a live dynamic scheme. Catppuccin cursors do not. `caelestia-cursor` grabs the primary colour, picks the nearest Catppuccin Mocha accent, and applies it to Hyprland + GTK.

## Catch up in 60 seconds

Wallpaper change → `postHook` runs the script → pointer theme updates (not always instant). Session start: delayed run in `execs.lua` after Caelestia writes `scheme.json`.

```bash
~/.local/bin/caelestia-cursor
# expect: Caelestia primary, Selected accent, Cursor theme lines
```

Package: `catppuccin-cursors-mocha`. Size: 24.

| Piece | Path |
|-------|------|
| Script | `~/.local/bin/caelestia-cursor` |
| Wallpaper hook | `~/.config/caelestia/cli.json` → `wallpaper.postHook` |
| Session start | `~/.config/hypr/hyprland/execs.lua` |

## What it does

1. Runs `caelestia scheme get` and strips ANSI junk to get the primary hex.
2. Measures RGB distance to the Mocha accent list (rosewater, flamingo, pink, mauve, red, maroon, peach, yellow, green, teal, sky, sapphire, blue, lavender).
3. Builds `catppuccin-mocha-<accent>-cursors`.
4. Applies it:

```bash
hyprctl setcursor <theme> 24
gsettings set org.gnome.desktop.interface cursor-theme <theme>
gsettings set org.gnome.desktop.interface cursor-size 24
```

It is not a perfect match. Primary `#ecbe8a` lands on peach, which is close enough that I stop noticing.

## When it runs

Wallpaper change, via `~/.config/caelestia/cli.json`:

```json
{
    "wallpaper": {
        "postHook": "/home/theadenkingof/.local/bin/caelestia-cursor; /home/theadenkingof/.local/bin/caelestia-sddm-sync"
    }
}
```

Session start, in `~/.config/hypr/hyprland/execs.lua` after the stock cursor line:

```lua
hl.exec_cmd("sleep 2 && ~/.local/bin/caelestia-cursor")
```

The sleep is there because Caelestia needs a moment to write `scheme.json`. Without it you sometimes get the previous accent for a few seconds.

## Caveats

After a wallpaper change the script usually runs from the `postHook`, but the pointer can still take a bit to catch up. Same slow apply feeling as Zen after a restart.

## Check

```bash
~/.local/bin/caelestia-cursor
```

Change wallpaper, wait a moment, then look at the pointer.

## Copies in this folder

| File | Live path |
|------|-----------|
| `caelestia-cursor` | `~/.local/bin/caelestia-cursor` |
| `cli.json` | `~/.config/caelestia/cli.json` |
| `execs.lua` | `~/.config/hypr/hyprland/execs.lua` |
