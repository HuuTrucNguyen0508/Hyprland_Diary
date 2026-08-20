# Login screen monitor mismatch

How the SDDM **pixie-caelestia** greeter monitor layout was fixed so the password / user UI sits on the left (DP-3), matching Hyprland after login.

---

## Environment

| Piece | Detail |
|--------|--------|
| Greeter | SDDM Wayland + `kwin_wayland`, theme `pixie-caelestia` |
| Drop-in | `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| Monitors | **DP-3** 2560×1440 left/main @ `(0,0)`; **HDMI-A-1** 1920×1080 right @ `(2560,0)` |
| GPU | NVIDIA RTX 4070 SUPER |

Hyprland layout (correct **after** login):

```lua
-- ~/.config/caelestia/hypr-user.lua
hl.monitor({ output = "DP-3", position = "0x0", ... })
hl.monitor({ output = "HDMI-A-1", position = "2560x0", ... })
```

---

## Symptoms

- After login: monitors correct (DP-3 left, HDMI right).
- At SDDM password / user selection: layout wrong — had to move **right** to reach the physically **left** screen / password field.
- This is **not** the Caelestia session drawer issue (that only applies once Hyprland is running).

---

## Root cause

The greeter runs **kwin_wayland as user `sddm`**, not Hyprland. Without a greeter-specific layout, kwin follows **DRM connector order**.

On this machine both outputs are on NVIDIA `card1`:

```text
card1-HDMI-A-1  connected   (enumerated first)
card1-DP-3      connected
```

So the greeter often treated **HDMI as left/primary**, opposite of Hyprland.

These do **not** help on Wayland SDDM:

- `xrandr` / `/usr/share/sddm/scripts/Xsetup`
- `PrimaryScreen=` in `sddm.conf`

---

## Fix — `kwinoutputconfig.json` for the greeter user

Install a kwin output layout for SDDM (same mechanism as Plasma’s `~/.config/kwinoutputconfig.json`):

| Monitor   | Position   | Priority | Role              |
|-----------|------------|----------|-------------------|
| DP-3      | `(0,0)`    | 1        | Left / primary    |
| HDMI-A-1  | `(2560,0)` | 2        | Right / secondary |

Target file (owned by `sddm:sddm`):

```text
/var/lib/sddm/.config/kwinoutputconfig.json
```

Staged copy + installer on this machine:

```text
~/.local/share/caelestia-sddm-kwinoutputconfig.json
~/.local/bin/caelestia-sddm-monitors
```

Install / reinstall:

```bash
~/.local/bin/caelestia-sddm-monitors
```

(Uses sudo; copies the staged JSON into `/var/lib/sddm/.config/`.)

Related helpers (theme / colours, not monitor geometry):

| Helper | Role |
|--------|------|
| `~/.local/bin/caelestia-sddm-setup` | Install/clone `pixie-caelestia` theme, set `Current=` |
| `~/.local/bin/caelestia-sddm-sync` | Sync wallpaper + palette from Caelestia |
| `caelestia-sddm-sync.service` | User service for live sync |

---

## Config map

| Concern | Path |
|---------|------|
| SDDM theme / Wayland greeter | `/etc/sddm.conf`, `/etc/sddm.conf.d/10-wayland-matugen.conf` |
| Greeter monitor layout | `/var/lib/sddm/.config/kwinoutputconfig.json` |
| Hyprland monitor positions | `~/.config/caelestia/hypr-user.lua` |
| Greeter layout helper | `~/.local/bin/caelestia-sddm-monitors` |

---

## Verify

1. Logout (or reboot) to the greeter.
2. Password / user UI should be on **DP-3** (left).
3. HDMI should sit to the right of DP-3, same as in Hyprland.
4. Log in and confirm Hyprland layout is unchanged.

If Plasma “Apply SDDM settings” overwrites `kwinoutputconfig.json`, re-run `caelestia-sddm-monitors`.

---

## Pitfalls

- Fixing Caelestia session placement (focus DP-3) does **not** fix the greeter — different compositor, different config.
- Prefer matching greeter layout to Hyprland (`0x0` + `2560x0`) rather than copying Plasma scale (e.g. 1.25) unless you want that at login.
- Pixie `Main.qml` uses a fixed `1920×1080` root size; kwin still places that surface according to greeter primary/output layout.

See also: [Logout button fix](./logout-button.md).
