# Monitor workspace defaults

Hyprland put the main left monitor on workspace 2 at login and the right HDMI on workspace 1. Positions were correct; workspace numbers were swapped.

Sep 2026. DP-3 (2560×1440, left) should default to workspace 1. HDMI-A-1 (1920×1080, right) should default to workspace 2.

Same HDMI-first enumeration as the SDDM greeter issue, but a different fix. Greeter layout: [login screen monitor mismatch](../Loging%20screen%20and%20logout%20button/login-screen-monitor-mismatch/).

## Start here

After login, DP-3 should show workspace **1** in the bar. HDMI-A-1 should show workspace **2**.

```bash
hyprctl monitors -j | jq -r '.[] | "\(.name): ws \(.activeWorkspace.name)"'
hyprctl workspaces -j | jq -r '.[] | "\(.name) -> \(.monitor)"'
```

Expect `DP-3: ws 1` and `HDMI-A-1: ws 2` on a fresh session. After config-only changes: `hyprctl reload`. Workspace rules apply cleanly on re-login; reload alone may not move existing workspaces.

## Cause

Monitor positions in `hypr-user.lua` were already right (`DP-3` at `0x0`, `HDMI-A-1` at `2560x0`). Hyprland still assigns default workspace IDs by **detection order**, not config order.

On this NVIDIA box HDMI enumerates before DP:

```text
HDMI-A-1  monitor id 0  → grabbed workspace 1 at boot
DP-3      monitor id 1  → got workspace 2
```

Reordering `hl.monitor({ ... })` blocks does not change that.

Caelestia bar uses `perMonitorWorkspaces: true` (`~/.config/caelestia/shell.json`), so each screen shows its own 1–5 strip. Global workspace IDs still matter for focus, window rules, and `hyprctl`.

## Fix

Two workspace rules in `~/.config/caelestia/hypr-user.lua`:

```lua
hl.workspace_rule({ workspace = "1", monitor = "DP-3", default = true })
hl.workspace_rule({ workspace = "2", monitor = "HDMI-A-1", default = true })
```

`default = true` sets which workspace each monitor lands on at login. One default per monitor.

Live test before editing:

```bash
hyprctl keyword workspace 1,monitor:DP-3,default:true
hyprctl keyword workspace 2,monitor:HDMI-A-1,default:true
hyprctl reload
```

Then focus workspace 1 on DP-3:

```bash
hyprctl dispatch 'hl.dsp.focus({ monitor = "DP-3" })'
hyprctl dispatch 'hl.dsp.focus({ workspace = "1" })'
```

## Optional: pin all five bar workspaces per monitor

If you want DP-3 on global IDs 1–5 and HDMI on 6–10 (still shows 1–5 locally in the bar with `perMonitorWorkspaces`):

```lua
for i = 1, 5 do
    hl.workspace_rule({ workspace = tostring(i), monitor = "DP-3", default = (i == 1) })
end
for i = 6, 10 do
    hl.workspace_rule({ workspace = tostring(i), monitor = "HDMI-A-1", default = (i == 6) })
end
```

Not applied on this machine yet. The two-line default fix was enough.

## Config map

| Concern | Path |
|---------|------|
| Monitor positions + workspace rules | `~/.config/caelestia/hypr-user.lua` |
| Per-monitor workspace bar | `~/.config/caelestia/shell.json` → `bar.workspaces.perMonitorWorkspaces` |
| Hyprland load order | `~/.config/hypr/hyprland.lua` (requires `hypr-user` after stock configs) |
| Session drawer monitor pin | `~/.config/hypr/variables.lua` → `sessionMonitor = "DP-3"` |

## Pitfalls

- `hyprctl reload` loads rules but may not reshuffle workspaces already open. Re-login to confirm boot behaviour.
- Do not set two `default = true` rules on the same monitor.
- HDMI-first enumeration also broke SDDM layout. Fixing the greeter does not fix Hyprland workspace IDs.

## Copies in this folder

| File | Live path |
|------|-----------|
| `hypr-user-workspaces.lua` | Snippet from `~/.config/caelestia/hypr-user.lua` (monitors + workspace rules) |

Prefer live paths if copies drift.
