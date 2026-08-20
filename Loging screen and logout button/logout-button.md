# Logout button fix

How the Caelestia session **Logout** button was diagnosed and fixed on this Hyprland setup.

---

## Environment

| Piece | Detail |
|--------|--------|
| WM | Hyprland 0.56 (Lua config) |
| Shell | Caelestia (quickshell) |
| Greeter | SDDM Wayland + `kwin_wayland`, theme `pixie-caelestia` |
| Monitors | **DP-3** 2560×1440 left/main; **HDMI-A-1** 1920×1080 right |
| GPU | NVIDIA RTX 4070 SUPER |

---

## Symptoms

- Ctrl+Alt+Delete opens the Caelestia session menu.
- **Logout** either did nothing, or ended in a black screen needing the power button.
- `SUPER+L` (lock) was a red herring — it only runs `caelestia:lock` and is unrelated to logout.

---

## How logout is wired

1. Keybind `kbSession = "CTRL + ALT + Delete"` → `caelestia:session`.
2. Session UI buttons use `Config.session.commands.*`.
3. Default logout command is `["logout"]`, which maps to logind **`Terminate`** via Caelestia `SessionManager`.

```text
logout → SessionManager.logout() → login1.Session.Terminate
```

Session menu order (top → bottom): **Logout**, Shutdown, (gif), Hibernate, Reboot.

Journal lines like `reboot requested from client … ('reboot')` mean the **reboot** button (or `reboot` binary) was used, not logout.

---

## Root causes

### A. Wrong exit command for Hyprland 0.56

First override used:

```text
hyprctl dispatch exit
```

Hyprland 0.56 Lua rejects that:

```text
hl.dispatch: expected a dispatcher (e.g. hl.dsp.window.close())
```

So the button appeared to do nothing.

Stock Hyprland exit path:

```text
hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'
```

### B. Hard session kill + NVIDIA greeter

`Terminate` made `start-hyprland` die with **SIGABRT**. SDDM logged `Process crashed` and the Wayland greeter often failed to come back cleanly (black screen).

### C. Session drawer on the wrong monitor

The session panel is hardcoded to the **right edge of the focused monitor**. With HDMI focused, the logout UI appeared on the far right of the right screen — not on the main left display.

---

## Fixes applied

### 1. Logout command → clean exit + VT switch

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

- `hyprshutdown` closes apps, then exits Hyprland.
- `--vt 1` switches back to the SDDM greeter VT (NVIDIA+SDDM black-screen fix).
- Fallback: `hyprctl dispatch 'hl.dsp.exit()'`.

Reload shell:

```bash
caelestia shell -k; sleep .2; caelestia shell -d
```

### 2. Always open session on DP-3

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

Disable session on the right monitor — `~/.config/caelestia/monitors/HDMI-A-1/shell.json`:

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

---

## Config map

| Concern | Path |
|---------|------|
| Session keybind + focus DP-3 | `~/.config/hypr/hyprland/keybinds.lua`, `~/.config/hypr/variables.lua` |
| Logout command | `~/.config/caelestia/shell.json` → `session.commands.logout` |
| Disable session on HDMI | `~/.config/caelestia/monitors/HDMI-A-1/shell.json` |

---

## Verify

1. Ctrl+Alt+Delete → session UI on **DP-3** (left).
2. Click **Logout** (top button).
3. Expect brief “Logging out…” then **pixie-caelestia** on VT1 — not a stuck black screen.

---

## Pitfalls

- Do not confuse **reboot** with **logout** in the session menu (reboot icon is Material `cached`).
- **Lock (`SUPER+L`)** does not affect logout.
- Prefer `hyprshutdown --vt 1` / `hl.dsp.exit()` over bare logind `Terminate` on this NVIDIA + SDDM Wayland stack.

See also: [Login screen monitor mismatch](./login-screen-monitor-mismatch.md).
