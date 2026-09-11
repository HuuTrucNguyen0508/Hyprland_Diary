# Bluetooth soft-block and Caelestia toggles

Sep 2026. MediaTek USB Bluetooth (`hci0` on `usb 1-7`, same mt7921 card as WiFi) comes back soft-blocked. The Caelestia Bluetooth switches then look dead because Quickshell refuses `Powered=on` while BlueZ reports `PowerState: off-blocked`.

## Start here

If Bluetooth is off and the bar toggle will not turn it back on:

```bash
rfkill list bluetooth
bluetoothctl show | rg 'Powered|PowerState'
```

Soft blocked + `PowerState: off-blocked` means rfkill, not a dead dongle. Clear it and power on:

```bash
rfkill unblock bluetooth
# BlueZ may return Busy for a beat right after unblock
bluetoothctl power on || { sleep 0.6; bluetoothctl power on; }
```

Caelestia shell on this machine uses a helper so the UI does that path for you. After editing the shell, reload:

```bash
caelestia shell -k
caelestia shell -d
```

## What was going wrong

1. Soft block is a software kill switch (`Hard blocked: no`).
2. Boot already runs `unblock-bluetooth.service` (`rfkill unblock bluetooth` before `bluetooth.service`). That alone is not enough: the adapter can end up soft-blocked again after session settle / USB BT re-register, and `systemd-rfkill` restores saved soft state when the rfkill device reappears.
3. Stock Caelestia toggles only set Quickshell `adapter.enabled` (BlueZ `Powered`). That does not soft-block on its own. When the adapter is already blocked, Quickshell logs that it cannot enable and returns. The switch looks broken.
4. Journals often show `bluetoothd: Failed to set mode: Failed (0x03)` at login when the radio is already unusable.

Turning Bluetooth off with BlueZ power-off does not soft-block (verified with `bluetoothctl power off` then `rfkill list`). Soft-block is a separate sticky state.

## What shipped

| Piece | Behaviour |
|-------|-----------|
| `unblock-bluetooth.service` | One-shot `rfkill unblock bluetooth` at boot (`WantedBy=multi-user.target`) |
| `BluetoothControl.qml` | Off: BlueZ power only. On: `rfkill unblock` then `bluetoothctl power on` (one retry after 0.6 s if Busy) |
| Bar / utilities / nexus toggles | Call `BluetoothControl` instead of writing `adapter.enabled` directly |

## Live paths

| Piece | Path |
|-------|------|
| Shell fork (canonical) | `~/orca/projects/Hyprland_Laucnher/shell` |
| Config symlink | `~/.config/quickshell/caelestia` → that fork |
| Helper | `…/shell/services/BluetoothControl.qml` |
| Bar popout | `…/shell/modules/bar/popouts/Bluetooth.qml` |
| Utilities card | `…/shell/modules/utilities/cards/Toggles.qml` |
| Nexus page | `…/shell/modules/nexus/pages/BluetoothPage.qml` |
| Boot unblock unit | `/etc/systemd/system/unblock-bluetooth.service` |

Prefer live paths if copies in this folder drift.

## Commands

```bash
systemctl is-enabled unblock-bluetooth.service
systemctl status unblock-bluetooth.service --no-pager
journalctl -b --no-pager | rg 'block set for type bluetooth|unblock set for type bluetooth|Failed to set mode|PowerState'

# Install / re-enable boot unblock (needs sudo)
sudo cp /path/to/unblock-bluetooth.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now unblock-bluetooth.service
```

## Copies in this folder

| File | Role |
|------|------|
| `BluetoothControl.qml` | Singleton used by the three toggles |
| `unblock-bluetooth.service` | Boot rfkill unblock |
| `bar-popout-enabled-toggle.qml.snip` | Bar Enabled switch |
| `utilities-bluetooth-toggle.qml.snip` | Utilities quick toggle |
| `nexus-bluetooth-toggle.qml.snip` | Nexus Bluetooth page switch |

## Related

- Caelestia shell fork / launcher work: [Caelestia-launcher-flow](../Caelestia-launcher-flow/)
