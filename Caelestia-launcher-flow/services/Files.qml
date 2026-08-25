pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import qs.utils

Singleton {
    id: root

    property string query: ""
    property var results: []
    property int resultsEpoch: 0

    readonly property int minQueryLength: 2
    readonly property int maxResults: 8
    readonly property string helper: `${Quickshell.shellDir}/assets/elephant_files_query.py`

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

    Timer {
        id: debounce

        interval: 120
        repeat: false
        onTriggered: {
            if (root.query.length < root.minQueryLength)
                return;
            searchProc.command = ["python3", root.helper, root.query, `${root.maxResults}`];
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
                    const path = item.path || "";
                    const base = path.split("/").pop() || path;
                    return {
                        kind: "file",
                        id: item.id || path,
                        path,
                        name: base,
                        desc: Paths.shortenHome(path),
                        icon: path.endsWith("/") ? "folder" : "draft",
                        score: item.score || 0
                    };
                });
                root.resultsEpoch++;
            }
        }
    }
}
