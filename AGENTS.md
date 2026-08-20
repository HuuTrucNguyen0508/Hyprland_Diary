## Learned user preferences

- Wants practical, command-level troubleshooting and concrete fixes, not high-level theory.
- Expects diagnosis from logs and config before recommendations.
- Avoids heavy always-on Python monitor stacks for the TURZX smart screen. Fine with a lightweight custom PIL dashboard (~1s refresh) or something non-Python.
- Wants low CPU for always-on hardware bits (smart screen, sensors, and similar).
- Prefers letterbox scaling and integer pixel nudges for TURZX layout. Fractional offsets hit dead zones and jump.
- Prefers Caelestia's live dynamic scheme to drive TURZX colours, Cursor theme, Zen Browser UI, and the SDDM greeter wallpaper + palette. No separate fixed themes.
- Prefers the Caelestia session / logout drawer on the left main monitor (DP-3), not the right display.

## Learned workspace facts

- Linux (CachyOS), Hyprland, Zsh. This repo is the Hyprland troubleshooting diary (`Hyprland_Diary`).
- TURZX 8" USB smart screen (`1cbe:0080`, TURZX1.0), TUR_USB protocol. Mounted landscape-wide. On this unit the library's portrait/landscape labels do not match the glass.
- Custom dashboard at `~/Documents/dashboard` (1280×800 PIL; `turzx_screen.py` uses native 1280×800 + LANDSCAPE). Picture card uses `~/Pictures/4.png` with near-black keyed transparent in the renderer.
- `turing-smart-screen-python` at `~/Documents/turing-smart-screen-python` (TUR_USB). `lcd_comm_turing_usb.py` patched so the library does not rotate on USB send. The dashboard owns orientation.
- `turzx-dashboard.service` user unit starts the dashboard on boot.
- Weather card: OpenWeatherMap, city 3019952 (Éragny).
- GPU: NVIDIA RTX 4070 SUPER, stats via `nvidia-smi`.
- Caelestia dots for Hyprland theming. TURZX watches `~/.local/state/caelestia/scheme.json` (Everforest fallback). Cursor via `~/.local/bin/caelestia-cursor`. Zen via `caelestia-zen-sync` + profile `chrome/` CSS; Zen needs a full restart and both can lag after wallpaper changes.
- Orca IDE alongside Cursor.
- Proton Drive mounted with rclone at `~/ProtonDrive` (user systemd service).
- SDDM greeter: `pixie-caelestia` on Wayland/kwin (`/etc/sddm.conf.d/10-wayland-matugen.conf`). Wallpaper/colours via `caelestia-sddm-sync.service`. Greeter layout pinned with `/var/lib/sddm/.config/kwinoutputconfig.json` (DP-3 primary); helper `~/.local/bin/caelestia-sddm-monitors`.
- Dual monitors: DP-3 1440p left (main), HDMI-A-1 1080p right. Ctrl+Alt+Delete focuses DP-3 then opens the session menu. Logout uses `hyprshutdown --vt 1` so the greeter returns. logind `Terminate` SIGABRTs `start-hyprland` on this stack.
