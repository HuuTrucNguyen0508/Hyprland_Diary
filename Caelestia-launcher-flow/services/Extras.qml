pragma Singleton

import QtQuick
import Quickshell
import Caelestia

Singleton {
    id: root

    property string query: ""
    property var results: []
    property int resultsEpoch: 0
    property string pendingCalcQuery: ""

    readonly property int minQueryLength: 1

    function setQuery(text: string): void {
        const trimmed = text.trim();
        if (trimmed === root.query)
            return;

        root.query = trimmed;
        root.rebuild();
    }

    function clear(): void {
        root.query = "";
        root.pendingCalcQuery = "";
        if (root.results.length !== 0) {
            root.results = [];
            root.resultsEpoch++;
        }
    }

    function looksLikeCalc(q: string): bool {
        if (!q || q.length < 1)
            return false;
        if (/^https?:\/\//i.test(q))
            return false;
        if (!/\d/.test(q))
            return false;
        if (/\bto\b/i.test(q))
            return true;
        if (/[=+\-*/^%()]/.test(q))
            return true;
        if (/^\s*\d[\d.,]*\s*[a-zA-Z°µ]+\s*$/.test(q))
            return true;
        return false;
    }

    function looksLikeUrl(q: string): bool {
        if (/^https?:\/\/\S+$/i.test(q))
            return true;
        if (/^(www\.)?[a-z0-9-]+(\.[a-z0-9-]+)+([/?#]\S*)?$/i.test(q))
            return true;
        return false;
    }

    function normalizeUrl(q: string): string {
        if (/^https?:\/\//i.test(q))
            return q;
        return `https://${q}`;
    }

    function rebuild(): void {
        const q = root.query;
        const out = [];

        if (!q) {
            root.results = [];
            root.resultsEpoch++;
            root.pendingCalcQuery = "";
            return;
        }

        if (root.looksLikeUrl(q)) {
            const url = root.normalizeUrl(q);
            out.push({
                kind: "url",
                name: qsTr("Open %1").arg(q),
                desc: url,
                icon: "link",
                url
            });
        }

        if (root.looksLikeCalc(q)) {
            root.pendingCalcQuery = q;
            Qalculator.evalAsync(q);
            // Calc row inserted asynchronously in onResultChanged.
        } else {
            root.pendingCalcQuery = "";
        }

        if (q.length >= 2 && !root.looksLikeUrl(q)) {
            const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(q)}`;
            out.push({
                kind: "web",
                name: qsTr("Search Google for \"%1\"").arg(q),
                desc: searchUrl,
                icon: "travel_explore",
                url: searchUrl
            });
        }

        root.results = out;
        root.resultsEpoch++;
    }

    function activate(item: var): void {
        if (!item)
            return;

        if (item.kind === "calc") {
            const text = item.copyText || item.name || "";
            if (text)
                Quickshell.execDetached(["wl-copy", text]);
            return;
        }

        if ((item.kind === "web" || item.kind === "url") && item.url)
            Quickshell.execDetached(["xdg-open", item.url]);
    }

    Connections {
        target: Qalculator

        function onResultChanged(): void {
            const q = root.pendingCalcQuery;
            if (!q || q !== root.query)
                return;

            const result = Qalculator.result || "";
            const raw = Qalculator.rawResult || "";
            if (!result || result.includes("error:") || result.includes("warning:"))
                return;

            // Drop stale calc rows, keep url/web.
            const withoutCalc = root.results.filter(r => r.kind !== "calc");
            withoutCalc.unshift({
                kind: "calc",
                name: result,
                desc: q,
                icon: "function",
                copyText: raw || result
            });
            root.results = withoutCalc;
            root.resultsEpoch++;
        }
    }
}
