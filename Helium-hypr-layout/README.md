# Helium layout follows Hyprland monitors

Sep 2026. Vertical tabs on both screens: left strip on DP-3, right strip on HDMI-A-1. If the strip stays on the wrong side after a move, the helper probably died or Helium was launched without CDP.

## Start here

Helium stores layout in profile-wide prefs (`helium.browser.layout` and
`helium.browser.vertical_right_aligned`). This helper watches Hyprland window
moves and sets both over Chromium DevTools on localhost.


| Monitor                   | Layout   | Tab side |
| ------------------------- | -------- | -------- |
| `DP-3` (left, 1440p)      | vertical | left     |
| `HDMI-A-1` (right, 1080p) | vertical | right    |


```bash
cat ~/.config/helium-hypr-layout/config.json
pgrep -af helium-hypr-layout
~/.local/bin/helium-hypr-layout --once --force
cat ~/.local/state/helium-hypr-layout/state.json
```

Launch Helium through `~/.local/bin/helium` so CDP is on (port 9333). The AppImageLauncher `.desktop` Exec lines were pointed at that wrapper. AppImageLauncher may rewrite them on an upgrade, so check if layout stops following monitors.

Autostart is the `execs.lua` line inside `hyprland.start` (not the systemd unit; that unit exists but stays disabled). After editing `execs.lua`, the next Hyprland login picks it up, or start the daemon by hand:

```bash
~/.local/bin/helium-hypr-layout --daemon &
# optional alternate: systemctl --user enable --now helium-hypr-layout.service
```

Sanity check: move Helium DP-3 ↔ HDMI-A-1 and watch:

```bash
tail -f ~/.local/state/helium-hypr-layout/daemon.log
# expect: DP-3 -> vertical/left / HDMI-A-1 -> vertical/right
```

## How it works

1. `~/.local/bin/helium` launches the AppImage with `--remote-debugging-port=9333` (localhost only).
2. `helium-hypr-layout --daemon` listens on Hyprland `socket2` (`movewindowv2`, `openwindow`, focus changes, …) and also polls about once a second.
3. It picks the most recently focused Helium window, maps its monitor name through the config, and sets layout + tab side over CDP.
4. If Helium is not listening on CDP, it writes `~/.config/net.imput.helium/Default/Preferences` so the next cold start matches.

One Helium profile means one layout at a time. Two windows on different monitors will fight; the focused window wins.

## Live paths


| Piece          | Path                                                                               |
| -------------- | ---------------------------------------------------------------------------------- |
| Launcher       | `~/.local/bin/helium`                                                              |
| Daemon         | `~/.local/bin/helium-hypr-layout`                                                  |
| Config         | `~/.config/helium-hypr-layout/config.json`                                         |
| State / log    | `~/.local/state/helium-hypr-layout/`                                               |
| Autostart      | `~/.config/hypr/hyprland/execs.lua` (`hyprland.start`)                             |
| Optional unit  | `~/.config/systemd/user/helium-hypr-layout.service` (disabled here)                |
| Helium profile | `~/.config/net.imput.helium/Default/Preferences`                                   |
| Desktop Exec   | `~/.local/share/applications/appimagekit_*-Helium.desktop` → `~/.local/bin/helium` |


Prefer live paths if copies in this folder drift.

## Commands

```bash
# Force a layout + side now (Helium must be running via the wrapper)
~/.local/bin/helium-hypr-layout --set vertical --side left
~/.local/bin/helium-hypr-layout --set vertical --side right

# Apply for whatever monitor Helium is on
~/.local/bin/helium-hypr-layout --once --force

# Change the mapping
edit ~/.config/helium-hypr-layout/config.json
# layout: classic | compact | vertical | dynamic
# side: left | right
```

Port override: `HELIUM_REMOTE_DEBUG_PORT=9333`.

## Copies in this folder


| File                         | What it is                       |
| ---------------------------- | -------------------------------- |
| `helium`                     | AppImage launcher with CDP flags |
| `helium-hypr-layout`         | Event listener + CDP pref setter |
| `config.json`                | Monitor → layout + side map      |
| `helium-hypr-layout.service` | Optional systemd user unit       |
| `execs-snippet.lua`          | Autostart line from `execs.lua`  |


## Related

- Polite Helium quit (Alt+F4 / session actions): [logout-button](../Loging%20screen%20and%20logout%20button/logout-button/)

