#!/usr/bin/env python3
"""Query Elephant files provider; fall back to fd on common roots. Print JSON."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

ITEM_RE = re.compile(
    r'identifier:"([^"]+)".*?text:"([^"]+)".*?score:(\d+)',
    re.DOTALL,
)


def elephant_query(query: str, limit: int) -> list[dict]:
    if not shutil.which("elephant"):
        return []
    try:
        proc = subprocess.run(
            ["elephant", "query", f"files;{query};{limit}"],
            capture_output=True,
            text=True,
            timeout=1.5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    # Elephant panics on empty result sets; treat that as no hits.
    if not proc.stdout.strip():
        return []

    items: list[dict] = []
    for ident, path, score in ITEM_RE.findall(proc.stdout):
        items.append({"id": ident, "path": path, "score": int(score)})
    items.sort(key=lambda i: i["score"], reverse=True)
    return items[:limit]


def search_roots() -> list[str]:
    # Avoid scanning full $HOME here; that is too slow for a launcher keystroke.
    # Elephant covers the broad index; fd only covers common project/config trees.
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".config"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "orca"),
        os.path.join(home, "Projects"),
        os.path.join(home, "code"),
        os.path.join(home, "Code"),
    ]
    roots: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        if path in seen or not os.path.isdir(path):
            continue
        seen.add(path)
        roots.append(path)
    return roots


def fd_query(query: str, limit: int) -> list[dict]:
    if not shutil.which("fd"):
        return []

    roots = search_roots()
    # Prefer exact basename; fd regex, case-insensitive.
    pattern = re.escape(query)
    cmd = [
        "fd",
        "--hidden",
        "--color=never",
        "--max-results",
        str(limit),
        "--exclude",
        ".git",
        "--exclude",
        "node_modules",
        "--exclude",
        ".cache",
        "--exclude",
        "go/pkg",
        "--exclude",
        ".local/share/Trash",
        pattern,
        *roots,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2.5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    items: list[dict] = []
    for idx, line in enumerate(proc.stdout.splitlines()):
        path = line.strip()
        if not path:
            continue
        base = os.path.basename(path)
        score = 1000 if base.lower() == query.lower() else max(1, 500 - idx)
        items.append({"id": f"fd-{idx}", "path": path, "score": score})
    items.sort(key=lambda i: i["score"], reverse=True)
    return items[:limit]


def main() -> int:
    if len(sys.argv) < 2:
        print("[]")
        return 0

    query = sys.argv[1].strip()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    if len(query) < 2:
        print("[]")
        return 0

    items = fd_query(query, limit)
    seen = {i["path"] for i in items}
    for item in elephant_query(query, limit):
        if item["path"] in seen:
            continue
        items.append(item)
        seen.add(item["path"])
        if len(items) >= limit:
            break

    items.sort(key=lambda i: i["score"], reverse=True)
    print(json.dumps(items[:limit], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
