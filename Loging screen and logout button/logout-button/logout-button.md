# Logout button fix

Ctrl+Alt+Delete opened the Caelestia session menu, but Logout either did nothing or left me on a black screen that needed the power button. Lock (`SUPER+L`) was a red herring. That only runs `caelestia:lock`.

| Piece | Detail |
|--------|--------|
| WM | Hyprland 0.56 (Lua config) |
| Shell | Caelestia (quickshell) |
| Greeter | SDDM Wayland + `kwin_wayland`, theme `pixie-caelestia` (from [pixie-sddm](https://github.com/xCaptaiN09/pixie-sddm)) |
| Monitors | DP-3 2560×1440 left/main; HDMI-A-1 1920×1080 right |
| GPU | NVIDIA RTX 4070 SUPER |

## How logout is wired

1. Keybind `kbSession = "CTRL + ALT + Delete"` → `caelestia:session`.
2. Session UI buttons use `Config.session.commands.*`.
3. Default logout is `["logout"]`, which goes through Caelestia `SessionManager` into logind `Terminate`.

```text
logout → SessionManager.logout() → login1.Session.Terminate
```

Menu order top to bottom: Logout, Shutdown, (gif), Hibernate, Reboot.

If the journal says `reboot requested from client … ('reboot')`, you hit Reboot, not Logout. Easy to mix up when debugging.

## What was wrong

### Wrong exit command for Hyprland 0.56

First override I tried:

```text
hyprctl dispatch exit
```

0.56 Lua rejects that:

```text
hl.dispatch: expected a dispatcher (e.g. hl.dsp.window.close())
```

So the button looked dead.

Stock exit path:

```text
hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'
```

### Hard session kill + NVIDIA greeter

`Terminate` made `start-hyprland` die with SIGABRT. SDDM logged `Process crashed`, and the Wayland greeter often never came back cleanly. Black screen.

### Session drawer on the wrong monitor

The panel sticks to the right edge of whatever monitor is focused. Focus HDMI and Logout appears on the far right of the right screen, not on the main left one.

## Fixes

### Logout command: clean exit + VT switch

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

`hyprshutdown` closes apps, then exits Hyprland. `--vt 1` jumps back to the SDDM greeter VT, which is what stopped the NVIDIA black screen for me. Fallback is `hyprctl dispatch 'hl.dsp.exit()'`.

Reload the shell:

```bash
caelestia shell -k; sleep .2; caelestia shell -d
```

### Always open session on DP-3

`~/.config/hypr/variables.lua`:

```lua
sessionMonitor = "DP-3",
```

`~/.config/hypr/hyprland/keybinds.lua`:

```lua
create_bind(vars.kbSession, function()
    hl.dispatch(hl.dsp.focus({ monitor = vars.sessionMonitor }))
    hl.dispatch(hl.dsp.global("caelestia:session"))
end)
```

And kill session on the right monitor in `~/.config/caelestia/monitors/HDMI-A-1/shell.json`:

```json
{
    "bar": { "persistent": false },
    "osd": { "enabled": false },
    "session": { "enabled": false }
}
```

Then:

```bash
hyprctl reload
caelestia shell -k; sleep .2; caelestia shell -d
```

## Config map

| Concern | Path |
|---------|------|
| Session keybind + focus DP-3 | `~/.config/hypr/hyprland/keybinds.lua`, `~/.config/hypr/variables.lua` |
| Logout command | `~/.config/caelestia/shell.json` → `session.commands.logout` |
| Disable session on HDMI | `~/.config/caelestia/monitors/HDMI-A-1/shell.json` |

## Check

1. Ctrl+Alt+Delete → session UI on DP-3 (left).
2. Click Logout (top button).
3. Brief "Logging out…", then pixie-caelestia on VT1. Not a stuck black screen.

## Pitfalls

- Do not confuse reboot with logout. Reboot uses the Material `cached` icon.
- Lock is unrelated.
- Prefer `hyprshutdown --vt 1` / `hl.dsp.exit()` over bare logind `Terminate` on this NVIDIA + SDDM Wayland stack.

See also: [Login screen monitor mismatch](../login-screen-monitor-mismatch/login-screen-monitor-mismatch.md).

## Copies in this folder

| File | Live path |
|------|-----------|
| `shell.json` | `~/.config/caelestia/shell.json` |
| `variables.lua` | `~/.config/hypr/variables.lua` |
| `hypr-vars.lua` | `~/.config/caelestia/hypr-vars.lua` |
| `keybinds.lua` | `~/.config/hypr/hyprland/keybinds.lua` |
| `HDMI-A-1-shell.json` | `~/.config/caelestia/monitors/HDMI-A-1/shell.json` |
