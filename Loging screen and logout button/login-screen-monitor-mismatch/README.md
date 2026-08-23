# Login screen monitor mismatch

SDDM put the password field on the wrong physical monitor. Hyprland was fine after login; only the greeter was wrong.

Aug 2026. After login, Hyprland had DP-3 left and HDMI right. At the SDDM password screen I had to move *right* to reach the physically *left* monitor.

Not the Caelestia session drawer (Hyprland only). See [logout button](../logout-button/).

## Start here

Greeter runs `kwin_wayland` as `sddm`, not Hyprland. Without a greeter layout, kwin follows DRM order: HDMI enumerated before DP-3 on this NVIDIA box → greeter primary on the wrong screen.

**Fix:** `/var/lib/sddm/.config/kwinoutputconfig.json` pins DP-3 at `(0,0)`.

```bash
~/.local/bin/caelestia-sddm-monitors   # sudo; copies staged JSON into /var/lib/sddm/.config/
```

Log out and confirm password UI is on DP-3 (left). If Plasma overwrote the file, re-run the helper.

| Piece | Detail |
|--------|--------|
| Greeter | SDDM Wayland + `kwin_wayland`, theme `pixie-caelestia` |
| Monitors | DP-3 2560×1440 left `(0,0)`; HDMI-A-1 1920×1080 right `(2560,0)` |
| GPU | NVIDIA RTX 4070 SUPER |

Hyprland layout (`~/.config/caelestia/hypr-user.lua`):

```lua
hl.monitor({ output = "DP-3", position = "0x0", ... })
hl.monitor({ output = "HDMI-A-1", position = "2560x0", ... })
```

## Cause

On this machine both outputs sit on NVIDIA `card1`:

```text
card1-HDMI-A-1  connected   (enumerated first)
card1-DP-3      connected
```

Things that do not help on Wayland SDDM:

- `xrandr` / `/usr/share/sddm/scripts/Xsetup`
- `PrimaryScreen=` in `sddm.conf`

## Fix: `kwinoutputconfig.json` for the greeter

| Monitor | Position | Priority | Role |
|---------|----------|----------|------|
| DP-3 | `(0,0)` | 1 | Left / primary |
| HDMI-A-1 | `(2560,0)` | 2 | Right / secondary |

Installed at:

```text
/var/lib/sddm/.config/kwinoutputconfig.json
```

Staged copy:

```text
~/.local/share/caelestia-sddm-kwinoutputconfig.json
~/.local/bin/caelestia-sddm-monitors
```

Greeter colours/wallpaper: [pixie-sddm](../../Caelestia_theme_sync/pixie-sddm/).

## Config map

| Concern | Path |
|---------|------|
| SDDM theme / Wayland greeter | `/etc/sddm.conf`, `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| Greeter monitor layout | `/var/lib/sddm/.config/kwinoutputconfig.json` |
| Hyprland monitor positions | `~/.config/caelestia/hypr-user.lua` |
| Greeter layout helper | `~/.local/bin/caelestia-sddm-monitors` |

## Pitfalls

- Focusing DP-3 for the Caelestia session drawer does not fix the greeter. Different compositor, different config.
- Match greeter positions to Hyprland (`0x0` + `2560x0`). Do not copy Plasma scale unless you want that at login.
- Pixie `Main.qml` uses a fixed `1920×1080` root size. kwin still places that surface from the greeter primary/output layout.

## Copies in this folder

| File | Live path |
|------|-----------|
| `caelestia-sddm-monitors` | `~/.local/bin/caelestia-sddm-monitors` |
| `caelestia-sddm-kwinoutputconfig.json` | `~/.local/share/caelestia-sddm-kwinoutputconfig.json` |
| `10-wayland-matugen.conf` | `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| `hypr-user.lua` | `~/.config/caelestia/hypr-user.lua` |
