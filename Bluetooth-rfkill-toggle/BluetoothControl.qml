pragma Singleton

import Quickshell
import Quickshell.Bluetooth
import Quickshell.Io

Singleton {
    id: root

    readonly property bool enabled: Bluetooth.defaultAdapter?.enabled ?? false // qmllint disable unresolved-type

    function setEnabled(wantOn: bool): void {
        const adapter = Bluetooth.defaultAdapter; // qmllint disable unresolved-type
        if (!adapter)
            return;

        if (!wantOn) {
            enableProc.running = false;
            // Power off only. Never soft-block via rfkill or the toggle sticks off.
            adapter.enabled = false;
            return;
        }

        // Clear soft-block first. Quickshell refuses Powered=on while state is Blocked.
        enableProc.running = false;
        enableProc.running = true;
    }

    function toggle(): void {
        root.setEnabled(!root.enabled);
    }

    Process {
        id: enableProc

        // BlueZ often returns Busy immediately after rfkill unblock; retry once.
        command: ["sh", "-c", "rfkill unblock bluetooth; bluetoothctl power on || { sleep 0.6; bluetoothctl power on; }"]
    }
}
