# Logout button fix

Aug 2026. Ctrl+Alt+Delete opened the Caelestia session menu, but Logout either did nothing or left a black screen. Lock (`SUPER+L`) is unrelated.

## Catch up in 60 seconds

**Working logout today:** `hyprshutdown --vt 1` via `shell.json`, session UI forced onto DP-3 before opening.

```bash
# After editing shell.json or keybinds:
caelestia shell -k; sleep .2; caelestia shell -d
hyprctl reload
```

Test: Ctrl+Alt+Delete → UI on left monitor → Logout (top button) → pixie-caelestia greeter, not a black screen.

Greeter monitor layout: [login screen monitor mismatch](../login-screen-monitor-mismatch/).

| Piece | Detail |
|--------|--------|
| WM | Hyprland 0.56 (Lua config) |
| Shell | Caelestia (quickshell) |
| Greeter | SDDM Wayland + `pixie-caelestia` |
| Monitors | DP-3 left/main; HDMI-A-1 right |

## How logout is wired

1. `CTRL + ALT + Delete` → `caelestia:session` (after focus DP-3).
2. Session buttons use `Config.session.commands.*`.
3. Default logout was `["logout"]` → logind `Terminate` (broke on this stack).

Menu order top to bottom: Logout, Shutdown, (gif), Hibernate, Reboot. Journal `reboot requested` means you hit Reboot, not Logout.

## What was wrong

`hyprctl dispatch exit` does not work on Hyprland 0.56 Lua (`hl.dispatch: expected a dispatcher`).

`Terminate` made `start-hyprland` die with SIGABRT. SDDM logged `Process crashed`; Wayland greeter often never came back. Black screen.

Session drawer stuck to whichever monitor had focus. Focus HDMI → Logout on the far right of the right screen.

## Fixes

### Logout command

`~/.config/caelestia/shell.json`:

```json
"session": {
    "commands": {
        "logout": [
            "sh",
            "-c",
            "command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown --vt 1 -t 'Logging out...' || hyprctl dispatch 'hl.dsp.exit()'"
        ]
    }
}
```

`--vt 1` jumps back to the SDDM greeter VT. That stopped the NVIDIA black screen for me.

### Always open session on DP-3

`~/.config/hypr/variables.lua`: `sessionMonitor = "DP-3"`

`~/.config/hypr/hyprland/keybinds.lua`:

```lua
create_bind(vars.kbSession, function()
    hl.dispatch(hl.dsp.focus({ monitor = vars.sessionMonitor }))
    hl.dispatch(hl.dsp.global("caelestia:session"))
end)
```

Disable session on HDMI: `~/.config/caelestia/monitors/HDMI-A-1/shell.json` → `"session": { "enabled": false }`

## Config map

| Concern | Path |
|---------|------|
| Session keybind + focus DP-3 | `~/.config/hypr/hyprland/keybinds.lua`, `~/.config/hypr/variables.lua` |
| Logout command | `~/.config/caelestia/shell.json` → `session.commands.logout` |
| Disable session on HDMI | `~/.config/caelestia/monitors/HDMI-A-1/shell.json` |

## Pitfalls

- Do not confuse reboot with logout.
- Prefer `hyprshutdown --vt 1` / `hl.dsp.exit()` over bare logind `Terminate` on this NVIDIA + SDDM Wayland stack.

## Copies in this folder

| File | Live path |
|------|-----------|
| `shell.json` | `~/.config/caelestia/shell.json` |
| `variables.lua` | `~/.config/hypr/variables.lua` |
| `hypr-vars.lua` | `~/.config/caelestia/hypr-vars.lua` |
| `keybinds.lua` | `~/.config/hypr/hyprland/keybinds.lua` |
| `HDMI-A-1-shell.json` | `~/.config/caelestia/monitors/HDMI-A-1/shell.json` |
