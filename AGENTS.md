## Learned User Preferences
- Prefers practical, command-level troubleshooting with concrete fixes over high-level theory.
- Expects direct diagnosis from logs/config evidence before recommendations.
- Avoids heavy always-on Python monitor stacks for TURZX/smart screen; accepts lightweight custom PIL dashboards (~1s refresh) or native/non-Python alternatives.
- Wants low-CPU configurations for always-on hardware integrations (smart screen, sensors, etc.).
- Prefers letterbox scaling and integer pixel nudges over fractional offsets when positioning TURZX dashboard content (avoids dead-zone jumps).
- Prefers Caelestia's live dynamic scheme to drive TURZX dashboard colors and the SDDM greeter (wallpaper + palette), not independent/fixed themes.
- Prefers the Caelestia session/logout drawer on the left/main monitor (DP-3) rather than the right display.

## Learned Workspace Facts
- Primary environment is Linux (CachyOS) with Hyprland and Zsh.
- Has TURZX 8" USB smart screen (1cbe:0080, TURZX1.0) using TUR_USB vendor protocol; physically mounted landscape-wide; library portrait/landscape labels inverted vs physical mount on this unit.
- Custom TURZX system monitor at ~/Documents/dashboard (1280×800 PIL layout; turzx_screen.py uses native 1280×800 + LANDSCAPE); picture card uses ~/Pictures/4.png (near-black keyed transparent in renderer).
- turing-smart-screen-python at ~/Documents/turing-smart-screen-python (TUR_USB); lcd_comm_turing_usb.py patched to skip library USB rotation (dashboard owns orientation).
- turzx-dashboard runs as a user systemd service (`turzx-dashboard.service`) on boot.
- TURZX weather card uses OpenWeatherMap (city 3019952, Éragny).
- GPU: NVIDIA RTX 4070 SUPER (stats via nvidia-smi).
- Uses Caelestia dotfiles for Hyprland theming (Fish shell color sequences); TURZX dashboard watches ~/.local/state/caelestia/scheme.json for live palette sync (Everforest fallback).
- Uses Orca IDE alongside Cursor.
- Proton Drive is mounted via rclone at ~/ProtonDrive (user systemd service).
- SDDM greeter is `pixie-caelestia` (Wayland/kwin; `/etc/sddm.conf.d/10-wayland-matugen.conf`); wallpaper and colors sync from Caelestia via `caelestia-sddm-sync.service`.
- Dual monitors: DP-3 1440p left (main), HDMI-A-1 1080p right; Ctrl+Alt+Delete focuses DP-3 then opens the session menu; logout uses `hyprshutdown --vt 1` so the greeter returns (logind Terminate SIGABRTs `start-hyprland`).
