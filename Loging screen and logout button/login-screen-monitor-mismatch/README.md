# Login screen monitor mismatch

After login, Hyprland had DP-3 on the left and HDMI on the right. At the SDDM password screen I had to move *right* to reach the physically *left* monitor. Annoying every single boot.

This is not the Caelestia session drawer issue. That only exists once Hyprland is running. See [logout button](../logout-button/).

| Piece | Detail |
|--------|--------|
| Greeter | SDDM Wayland + `kwin_wayland`, theme `pixie-caelestia` (from [pixie-sddm](https://github.com/xCaptaiN09/pixie-sddm)) |
| Drop-in | `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| Monitors | DP-3 2560×1440 left/main at `(0,0)`; HDMI-A-1 1920×1080 right at `(2560,0)` |
| GPU | NVIDIA RTX 4070 SUPER |

Hyprland layout after login (`~/.config/caelestia/hypr-user.lua`):

```lua
hl.monitor({ output = "DP-3", position = "0x0", ... })
hl.monitor({ output = "HDMI-A-1", position = "2560x0", ... })
```

## Cause

The greeter runs `kwin_wayland` as user `sddm`, not Hyprland. With no greeter-specific layout, kwin follows DRM connector order.

On this machine both outputs sit on NVIDIA `card1`:

```text
card1-HDMI-A-1  connected   (enumerated first)
card1-DP-3      connected
```

So the greeter treated HDMI as left/primary. Opposite of Hyprland.

Things that do not help on Wayland SDDM:

- `xrandr` / `/usr/share/sddm/scripts/Xsetup`
- `PrimaryScreen=` in `sddm.conf`

## Fix: `kwinoutputconfig.json` for the greeter

Same idea as Plasma's `~/.config/kwinoutputconfig.json`, but owned by `sddm`:

| Monitor | Position | Priority | Role |
|---------|----------|----------|------|
| DP-3 | `(0,0)` | 1 | Left / primary |
| HDMI-A-1 | `(2560,0)` | 2 | Right / secondary |

Installed at:

```text
/var/lib/sddm/.config/kwinoutputconfig.json
```

Staged copy and installer on this machine:

```text
~/.local/share/caelestia-sddm-kwinoutputconfig.json
~/.local/bin/caelestia-sddm-monitors
```

```bash
~/.local/bin/caelestia-sddm-monitors
```

Uses sudo. Copies the staged JSON into `/var/lib/sddm/.config/`.

Theme and colour helpers are separate. Wallpaper/palette sync is in [pixie-sddm](../../Caelestia_theme_sync/pixie-sddm/).

| Helper | Role |
|--------|------|
| `~/.local/bin/caelestia-sddm-setup` | Clone `pixie-caelestia`, set `Current=` |
| `~/.local/bin/caelestia-sddm-sync` | Sync wallpaper + palette from Caelestia |
| `caelestia-sddm-sync.service` | User service for live sync |

## Config map

| Concern | Path |
|---------|------|
| SDDM theme / Wayland greeter | `/etc/sddm.conf`, `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| Greeter monitor layout | `/var/lib/sddm/.config/kwinoutputconfig.json` |
| Hyprland monitor positions | `~/.config/caelestia/hypr-user.lua` |
| Greeter layout helper | `~/.local/bin/caelestia-sddm-monitors` |

## Check

1. Log out or reboot to the greeter.
2. Password / user UI should be on DP-3 (left).
3. HDMI should sit to the right of DP-3, same as in Hyprland.
4. Log in and confirm Hyprland layout is unchanged.

If Plasma "Apply SDDM settings" overwrites `kwinoutputconfig.json`, re-run `caelestia-sddm-monitors`.

## Pitfalls

- Focusing DP-3 for the Caelestia session drawer does not fix the greeter. Different compositor, different config.
- Match greeter positions to Hyprland (`0x0` + `2560x0`). Do not copy Plasma scale (e.g. 1.25) unless you want that at login.
- Pixie `Main.qml` uses a fixed `1920×1080` root size. kwin still places that surface from the greeter primary/output layout.

## Copies in this folder

| File | Live path |
|------|-----------|
| `caelestia-sddm-monitors` | `~/.local/bin/caelestia-sddm-monitors` |
| `caelestia-sddm-kwinoutputconfig.json` | `~/.local/share/caelestia-sddm-kwinoutputconfig.json` |
| `10-wayland-matugen.conf` | `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| `hypr-user.lua` | `~/.config/caelestia/hypr-user.lua` |
