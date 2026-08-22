# Hyprland diary

Notes from moving Windows → Hyprland on CachyOS. Stack: [Caelestia](https://github.com/caelestia-dots/caelestia) dots, Hyprland, Fish. SDDM greeter is [pixie-sddm](https://github.com/xCaptaiN09/pixie-sddm), forked locally as `pixie-caelestia` for wallpaper + palette sync.

The TURZX 8" USB panel uses [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) on the wire. The face you actually look at is a custom PIL dashboard in `~/Documents/dashboard`, not the stock Turing UI.

Each folder has a `README.md` plus copies of the configs/scripts that entry talks about. **Live paths win** if a copy drifted.

## Start here after a long break

**What runs on boot**

| Service | What it does |
|---------|----------------|
| `turzx-dashboard.service` | TURZX glass: stats cards, or ambient terminal apps, or speedtest gauges |
| `caelestia-sddm-sync.service` | Greeter wallpaper/colours from Caelestia scheme |

**TURZX in one breath:** 1280×800 dashboard → library rotates 270° → **800×1280** on USB. Never skip that rotate. Details: [Process](./TURZX-SCREEN/Process/).

**What the panel shows today (priority order):**

1. Speedtest gauges while a run is active (`Super+Shift+F`)
2. Stats cards for 10s after `Super+Shift+D` (peek)
3. Stats cards while gaming (fullscreen Steam/Proton/Lutris, or Caelestia game-mode toggle)
4. Otherwise ambient rotation: weathr → weatherspect → asciiquarium (5 min each; `Super+Shift+N` skips)

**Sanity check**

```bash
systemctl --user is-active turzx-dashboard.service   # expect: active
journalctl --user -u turzx-dashboard.service -n 3 --no-pager   # expect: SEND: (800, 1280) … LANDSCAPE
qs -c caelestia ipc call gameMode isEnabled   # manual toggle; fullscreen games flip stats without this
```

**Where the code lives:** `~/Documents/dashboard/` (canonical). Diary snapshots under `TURZX-SCREEN/`.

## Entries

### TURZX smart screen

| Read this | When you need |
|-----------|----------------|
| [Process](./TURZX-SCREEN/Process/) | Orientation, USB 800×1280, why the glass lied about landscape |
| [Host-engine refresh](./TURZX-SCREEN/host-engine-refresh/) | Dual-rate loop, dirty skip, shared top plate, H.264 opt-in |
| [Ambient screens](./TURZX-SCREEN/ambient-screens/) | weathr / weatherspect / asciiquarium, game mode, peek binds |
| [Refresh upgrade spike](./TURZX-SCREEN/refresh-upgrade-spike/) | Measured ~5 fps JPEG ceiling, probe scripts, H.264 go/no-go notes |
| [Custom firmware explore](./TURZX-SCREEN/custom-firmware-explore/) | Why we did not flash the panel |
| [Speedtest widget](./Speedtest-widget/) | `Super+Shift+F`, Fast.com engine, state JSON |
| [TURZX colours](./Caelestia_theme_sync/turzx/) | Scheme from `scheme.json`, no extra sync service |

### Caelestia theme sync

| Read this | When you need |
|-----------|----------------|
| [Cursor](./Caelestia_theme_sync/cursor/) | Catppuccin cursor from scheme primary |
| [Zen Browser](./Caelestia_theme_sync/zen-browser/) | Profile chrome CSS sync |
| [Pixie SDDM](./Caelestia_theme_sync/pixie-sddm/) | Greeter wallpaper + palette |

### Login / session

| Read this | When you need |
|-----------|----------------|
| [Login screen monitor mismatch](./Loging%20screen%20and%20logout%20button/login-screen-monitor-mismatch/) | Greeter on wrong monitor |
| [Logout button](./Loging%20screen%20and%20logout%20button/logout-button/) | Ctrl+Alt+Delete logout → greeter (`hyprshutdown --vt 1`) |

### Other

| Read this | When you need |
|-----------|----------------|
| [Orca theme + Caelestia](./Orca-ide-theme-error/) | Fish OSC sequences overriding Orca/Cursor terminal bg |
