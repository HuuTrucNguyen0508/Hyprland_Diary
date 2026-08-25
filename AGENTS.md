## Learned user preferences

- Unslop is always on: follow `~/.agents/skills/unslop/SKILL.md`. Machine-global rule at `~/.cursor/rules/unslop.mdc` (`alwaysApply`) so it applies in every workspace; project rule in this repo is backup.
- Wants practical, command-level troubleshooting and concrete fixes, not high-level theory.
- Expects diagnosis from logs and config before recommendations.
- Avoids heavy always-on Python monitor stacks for the TURZX smart screen. Fine with a lightweight custom PIL dashboard (~1s refresh) or something non-Python.
- Wants low CPU for always-on hardware bits (smart screen, sensors, and similar).
- Prefers letterbox scaling and integer pixel nudges for TURZX layout. Fractional offsets hit dead zones and jump.
- Prefers Caelestia's live dynamic scheme to drive TURZX colours, Cursor theme, Zen Browser UI, and the SDDM greeter wallpaper + palette. No separate fixed themes.
- Prefers the Caelestia session / logout drawer on the left main monitor (DP-3), not the right display.
- Fish interactive shell: home-wide fzf file launcher on Ctrl-F; cwd fzf on Ctrl-T after loading `fzf_key_bindings` in `~/.config/fish/config.fish`. `cat` pipes through lolcat with vivid Caelestia neon colours (not dull, not white-heavy).
- Prefers diary topics as `README.md` (GitHub-visible) written so a stranger can catch up cold; related config files copied into the same topic folder; avoid hardcoding machine-specific Zen profile directory names in checks/docs. Full write-up process: `.cursor/diary-writing.md` (local, gitignored).
- Prefers speedtest on the TURZX panel only (no desktop overlay). Super+Shift+F toggles; press again to abort.
- TURZX idle is the stats dashboard at ~1 Hz. Super+Shift+F overlays speedtest. Ambient cycle, Super+Shift+D peek, and Super+Shift+N are off the boot path (USB resets when JPEG flooded the hub shared with audio). TURZX binds live in `~/.config/caelestia/hypr-user.lua`. Interested in higher refresh where feasible (dual-rate JPEG/PNG; H.264 clip path proven for a later live-encoder experiment).

## Learned workspace facts

- Linux (CachyOS), Hyprland, Fish (`~/.config/fish`) and Zsh. This repo is the Hyprland troubleshooting diary (`Hyprland_Diary`).
- TURZX 8" USB smart screen (`1cbe:0080`, TURZX1.0), TUR_USB protocol. Mounted landscape-wide. Firmware framebuffer is portrait 800×1280; library portrait/landscape labels do not match the glass. Windows/cold-plug leave the panel expecting an 800×1280 stream (raw 1280×800 shows a sideways strip + leftover TURZX V2).
- Custom dashboard at `~/Documents/dashboard` (1280×800 PIL layout; `CONTENT_ROTATE = 0`; `Orientation.LANDSCAPE`). Library rotates 270° before USB so the wire size is 800×1280. Picture card uses `~/Pictures/4.png` with near-black keyed transparent. Storage card tracks SSD (`/`), NVMe (`/mnt/nvme`), and HDD (`/mnt/hdd`). Started by `turzx-dashboard.service` on boot (`PYTHONUNBUFFERED=1`). Views: stats always on, speedtest overlay. Ambient / peek / game-mode code still lives under `~/Documents/dashboard` but is unused. USB reconnect on errno 19. Diary: `TURZX-SCREEN/ambient-screens/`, `TURZX-SCREEN/usb-stability/`.
- `turing-smart-screen-python` at `~/Documents/turing-smart-screen-python` (TUR_USB). Keep stock `DisplayPILImage` USB rotate for LANDSCAPE (do not skip it). Full-frame JPEG/PNG over USB tops out around ~5 fps; dirty-rect still uploads the full canvas on the public path. H.264 chunk stream paints smoothly; live experiment `turzx_h264_live.py` (NVENC → Annex-B → cmds 17/121/122/123) is opt-in, not the default service. Spike notes in `TURZX-SCREEN/refresh-upgrade-spike/`.
- Weather card: OpenWeatherMap, city 3019952 (Éragny). Ambient weathr layout puts weather text on the right of the house so it stays visible when the panel is letterboxed smaller.
- GPU: NVIDIA RTX 4070 SUPER, stats via `nvidia-smi`.
- Caelestia dots for Hyprland theming. TURZX watches `~/.local/state/caelestia/scheme.json` (Everforest fallback). Cursor via `~/.local/bin/caelestia-cursor`. Zen via `caelestia-zen-sync` + profile `chrome/` CSS; Zen needs a full restart and both can lag after wallpaper changes.
- Orca IDE alongside Cursor.
- Proton Drive via user unit `rclone-proton.service` at `~/ProtonDrive` (not on the TURZX storage card).
- SDDM greeter: `pixie-caelestia` on Wayland/kwin (`/etc/sddm.conf.d/10-wayland-matugen.conf`). Wallpaper/colours via `caelestia-sddm-sync.service`. Greeter layout pinned with `/var/lib/sddm/.config/kwinoutputconfig.json` (DP-3 primary); helper `~/.local/bin/caelestia-sddm-monitors`.
- Dual monitors: DP-3 1440p left (main), HDMI-A-1 1080p right. Ctrl+Alt+Delete focuses DP-3 then opens the session menu. Logout uses `hyprshutdown --vt 1` so the greeter returns. logind `Terminate` SIGABRTs `start-hyprland` on this stack.
- Speedtest (Super+Shift+F): Fast.com engine via `~/.local/bin/network-speedtest` + `speedtest-session`; state at `~/.local/state/turzx/speedtest.json`; dashboard swaps to dual gauges for the run and holds ~3s. Toggle script `~/.config/hypr/scripts/toggle_speedtest.sh`. Diary topic `Speedtest-widget/`. AUR `fast-git` is a separate CLI, not the widget engine.
- Primary Super launcher is Caelestia (`caelestia:launcher`). Overlay at `~/.config/quickshell/caelestia` → `~/orca/projects/Hyprland_Laucnher/shell` adds Flow-style rows: Elephant files (`fd` fallback), Qalculator calc/convert, URL/websearch, PATH runner, Hyprland window focus via Lua `hl.dsp.focus`. Diary: `Caelestia-launcher-flow/`. Fuzzel stays for clipboard/emoji; Walker for cheatsheet (`CTRL + SPACE`).
- Runner launches need Ghostty `-e` before `wrap_term_launch.sh` or Ghostty treats args as config keys. Window focus uses Lua dispatch, not classic `focuswindow`.
