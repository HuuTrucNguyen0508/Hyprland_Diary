#!/usr/bin/env python3
"""List/focus Hyprland windows for the Caelestia launcher (Lua dispatch)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys


def hyprctl_json(cmd: list[str]):
    proc = subprocess.run(
        ["hyprctl", "-j", *cmd],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def list_windows(query: str, limit: int) -> list[dict]:
    clients = hyprctl_json(["clients"])
    if not isinstance(clients, list):
        return []

    q = query.strip().lower()
    scored: list[tuple[int, dict]] = []

    for client in clients:
        if not client.get("mapped", True):
            continue
        if client.get("hidden"):
            continue

        title = str(client.get("title") or "")
        clazz = str(client.get("class") or "")
        initial = str(client.get("initialClass") or "")
        address = str(client.get("address") or "")
        if not address:
            continue

        ws = client.get("workspace") or {}
        ws_name = str(ws.get("name") or ws.get("id") or "")
        hay = f"{title} {clazz} {initial} {ws_name}".lower()

        if q:
            if hay.startswith(q):
                score = 300
            elif f" {q}" in f" {hay}":
                score = 200
            elif q in hay:
                score = 100
            else:
                continue
            if title.lower().startswith(q) or clazz.lower().startswith(q):
                score += 50
        else:
            score = 1

        focus_id = client.get("focusHistoryID")
        if isinstance(focus_id, int):
            score += max(0, 40 - focus_id)

        scored.append(
            (
                score,
                {
                    "address": address,
                    "title": title,
                    "class": clazz,
                    "workspace": ws_name,
                    "score": score,
                },
            )
        )

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def focus_window(address: str) -> int:
    """Focus a window by Hyprland address using Lua dispatchers."""
    if not address or not shutil.which("hyprctl"):
        return 1

    # This Hyprland build uses Lua: classic `dispatch focuswindow` is invalid.
    code = f'hl.dsp.focus({{ window = "address:{address}" }})'
    proc = subprocess.run(
        ["hyprctl", "dispatch", code],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0 and "error" not in out.lower():
        # Best-effort raise in z-order for floating/special cases.
        bring = f'hl.dsp.window.bring_to_top({{ window = "address:{address}" }})'
        subprocess.run(
            ["hyprctl", "dispatch", bring],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return 0

    # Fallback: open special workspace / switch workspace, then focus again.
    clients = hyprctl_json(["clients"]) or []
    match = next((c for c in clients if c.get("address") == address), None)
    if not match:
        return 1

    ws = match.get("workspace") or {}
    ws_name = str(ws.get("name") or "")
    if ws_name.startswith("special:"):
        special = ws_name.split(":", 1)[1]
        subprocess.run(
            ["hyprctl", "dispatch", f'hl.dsp.focus({{ workspace = "special:{special}" }})'],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    elif ws.get("id") is not None and int(ws["id"]) > 0:
        subprocess.run(
            ["hyprctl", "dispatch", f'hl.dsp.focus({{ workspace = {int(ws["id"])} }})'],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )

    proc2 = subprocess.run(
        ["hyprctl", "dispatch", code],
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    out2 = (proc2.stdout or "") + (proc2.stderr or "")
    return 0 if proc2.returncode == 0 and "error" not in out2.lower() else 1


def main() -> int:
    if len(sys.argv) < 2:
        print("[]")
        return 0

    action = sys.argv[1]

    if action == "list":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        print(json.dumps(list_windows(query, limit), ensure_ascii=False))
        return 0

    if action == "focus":
        address = sys.argv[2] if len(sys.argv) > 2 else ""
        return focus_window(address)

    print("[]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
