pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import Caelestia.Config

Singleton {
    id: root

    property string query: ""
    property var results: []
    property int resultsEpoch: 0

    readonly property int minQueryLength: 2
    readonly property int maxResults: 5
    readonly property string helper: `${Quickshell.shellDir}/assets/elephant_provider_query.py`

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
        const bin = item?.name;
        if (!bin)
            return;

        // Prefer launching in the configured terminal. Elephant's activate path
        // is unreliable here; PATH binaries are usually TUI/CLI tools.
        const term = GlobalConfig.general.apps.terminal;
        Quickshell.execDetached([...term, "-e", `${Quickshell.shellDir}/assets/wrap_term_launch.sh`, bin]);
    }

    Timer {
        id: debounce

        interval: 120
        repeat: false
        onTriggered: {
            if (root.query.length < root.minQueryLength)
                return;
            searchProc.command = ["python3", root.helper, "runner", root.query, `${root.maxResults}`];
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

                const q = root.query;
                root.results = parsed.map(item => ({
                            kind: "runner",
                            id: item.id,
                            query: q,
                            name: item.text || "",
                            desc: qsTr("Run %1").arg(item.text || ""),
                            icon: "terminal",
                            score: item.score || 0
                        }));
                root.resultsEpoch++;
            }
        }
    }
}
