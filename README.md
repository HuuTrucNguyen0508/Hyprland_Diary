# Hyprland diary

Troubleshooting notes from one desktop: CachyOS, [Hyprland](https://hyprland.org/), [Caelestia](https://github.com/caelestia-dots/caelestia) dots. I wrote these while fixing  bugs. This is not an install guide or a maintained app, just stuff I got fiddling around and thus wants to keep a memory of it. Could very well be a work on my machine type of shit. 

**You might find this useful if you:**

- Run a TURZX / Turing USB smart screen on Linux and want a custom dashboard
- Use Caelestia on Hyprland and need the greeter, browser, or cursor to follow the wallpaper
- Hit SDDM on the wrong monitor, or logout leaving a black screen instead of the login UI

## How this repo is organized

One folder = one problem or feature. Each folder has:

- `README.md` — what broke, what fixed it, commands to check it
- Copied configs and scripts — snapshot of what was on my machine when I wrote the entry

Paths use `~` (my home directory). **If a copy here disagrees with a live file on disk, trust the live file.** The diary is a paper trail, not something you clone and run.

## Terms you will see


| Term            | Meaning                                                            |
| --------------- | ------------------------------------------------------------------ |
| Hyprland        | Wayland compositor / window manager                                |
| Caelestia       | Dotfiles + Quickshell bar and session UI for Hyprland              |
| TURZX           | 8" USB side monitor (Turing, USB id `1cbe:0080`, TUR_USB protocol) |
| `scheme.json`   | Colour palette Caelestia generates from the wallpaper              |
| SDDM            | Login screen before your desktop session                           |
| Greeter         | Same as SDDM (runs kwin on Wayland here, not Hyprland)             |
| pixie-caelestia | Local SDDM theme; wallpaper and colours synced from Caelestia      |


## TURZX panel (if that is why you are here)

Most of this repo is about a small USB screen beside the keyboard. It uses [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) on the wire. The UI is a custom Python dashboard in `~/Documents/dashboard` on my machine (not shipped in this repo). Code snapshots live under `TURZX-SCREEN/`.

**Rotation rule that bites everyone:** draw at 1280×800, the library rotates 270° before USB, the panel receives 800×1280. Skip that step and you get a sideways strip plus leftover vendor wallpaper. Details: [Process](./TURZX-SCREEN/Process/).

**What the panel shows (highest priority wins):**

1. Speedtest gauges while a run is active (`Super+Shift+F`)
2. Otherwise the stats dashboard (~1 Hz)

Ambient rotation, peek (`Super+Shift+D`), and auto game-mode view flips are off. They reset USB on this hub. History: [ambient-screens](./TURZX-SCREEN/ambient-screens/), [usb-stability](./TURZX-SCREEN/usb-stability/).

**Services on my machine:**


| Service                       | Role                                      |
| ----------------------------- | ----------------------------------------- |
| `turzx-dashboard.service`     | Drives the USB panel                      |
| `caelestia-sddm-sync.service` | Keeps greeter wallpaper + colours in sync |


```bash
systemctl --user is-active turzx-dashboard.service
journalctl --user -u turzx-dashboard.service -n 3 --no-pager   # expect: SEND: (800, 1280)
```

## Browse by topic

### TURZX smart screen


| Folder                                                             | Read if you want to…                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------------------- |
| [Process](./TURZX-SCREEN/Process/)                                 | Fix sideways image, stuck TURZX V2 wallpaper, wrong orientation     |
| [Host-engine refresh](./TURZX-SCREEN/host-engine-refresh/)         | Understand the always-on refresh loop, dirty skip, H.264 experiment |
| [Ambient screens](./TURZX-SCREEN/ambient-screens/)                 | Old weathr/curses path (off boot; USB instability)                  |
| [USB stability](./TURZX-SCREEN/usb-stability/)                     | Hub resets, reconnect, why ambient left the loop                    |
| [Refresh upgrade spike](./TURZX-SCREEN/refresh-upgrade-spike/)     | See measured USB fps ceiling and probe scripts                      |
| [Custom firmware explore](./TURZX-SCREEN/custom-firmware-explore/) | Know why flashing the panel was ruled out                           |
| [Speedtest widget](./Speedtest-widget/)                            | Wire speedtest to the panel only (`Super+Shift+F`)                  |
| [TURZX colours](./Caelestia_theme_sync/turzx/)                     | Match panel card colours to the Caelestia wallpaper                 |


### Caelestia theme sync

Caelestia picks colours from the wallpaper. These entries hook other apps into `scheme.json`.


| Folder                                             | Read if you want to…                     |
| -------------------------------------------------- | ---------------------------------------- |
| [Cursor](./Caelestia_theme_sync/cursor/)           | Pointer theme from scheme primary colour |
| [Zen Browser](./Caelestia_theme_sync/zen-browser/) | Zen toolbar colours from scheme          |
| [Pixie SDDM](./Caelestia_theme_sync/pixie-sddm/)   | Login screen wallpaper + palette         |


### Login / session


| Folder                                                                                                    | Read if you want to…                      |
| --------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| [Login screen monitor mismatch](./Loging%20screen%20and%20logout%20button/login-screen-monitor-mismatch/) | Password UI on the wrong physical monitor |
| [Logout button](./Loging%20screen%20and%20logout%20button/logout-button/)                                 | Logout → black screen instead of greeter  |


### Other


| Folder                                            | Read if you want to…                                  |
| ------------------------------------------------- | ----------------------------------------------------- |
| [Caelestia launcher (Flow-style)](./Caelestia-launcher-flow/) | Super launcher with files, calc, windows, PATH runner, URLs |
| [Orca theme + Caelestia](./Orca-ide-theme-error/) | Fish shell overriding Orca/Cursor terminal background |


