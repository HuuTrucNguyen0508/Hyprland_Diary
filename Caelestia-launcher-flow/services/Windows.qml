pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    property string query: ""
    property var results: []
    property int resultsEpoch: 0

    readonly property int minQueryLength: 1
    readonly property int maxResults: 6
    readonly property string helper: `${Quickshell.shellDir}/assets/hypr_windows.py`

    function setQuery(text: string): void {
        const trimmed = text.trim();
        if (trimmed === root.query)
            return;

        root.query = trimmed;

        if (trimmed.length < root.minQueryLength) {
            debounce.stop();
            if (root.results.length !== 0) {
                root.results = [];
                root.resultsEpoch++;
            }
            return;
        }

        debounce.restart();
    }

    function clear(): void {
        debounce.stop();
        root.query = "";
        if (root.results.length !== 0) {
            root.results = [];
            root.resultsEpoch++;
        }
    }

    function activate(item: var): void {
        const address = item?.address || item?.id;
        if (!address)
            return;
        Quickshell.execDetached(["python3", root.helper, "focus", address]);
    }

    Timer {
        id: debounce

        interval: 80
        repeat: false
        onTriggered: {
            searchProc.command = ["python3", root.helper, "list", root.query, `${root.maxResults}`];
            searchProc.running = true;
        }
    }

    Process {
        id: searchProc

        stdout: StdioCollector {
            onStreamFinished: {
                let parsed = [];
                try {
                    parsed = JSON.parse(text || "[]");
                } catch (e) {
                    parsed = [];
                }
                if (!Array.isArray(parsed))
                    parsed = [];

                root.results = parsed.map(item => {
                    const ws = item.workspace || "";
                    const clazz = item.class || "";
                    const bits = [];
                    if (clazz)
                        bits.push(clazz);
                    if (ws)
                        bits.push(ws);
                    return {
                        kind: "window",
                        id: item.address,
                        address: item.address,
                        name: item.title || clazz || item.address,
                        desc: bits.length ? qsTr("Focus · %1").arg(bits.join(" · ")) : qsTr("Focus window"),
                        icon: "select_window",
                        score: item.score || 0
                    };
                });
                root.resultsEpoch++;
            }
        }
    }
}
