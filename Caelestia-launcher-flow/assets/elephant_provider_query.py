#!/usr/bin/env python3
"""Query an Elephant provider and print JSON hits."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys

ITEM_START = re.compile(r"\bitem:\{")
FIELD_RE = {
    "id": re.compile(r'\bidentifier:"([^"]*)"'),
    "text": re.compile(r'\btext:"([^"]*)"'),
    "subtext": re.compile(r'\bsubtext:"([^"]*)"'),
    "icon": re.compile(r'\bicon:"([^"]*)"'),
    "provider": re.compile(r'\bprovider:"([^"]*)"'),
    "score": re.compile(r"\bscore:(\d+)"),
}


def split_items(blob: str) -> list[str]:
    starts = [m.start() for m in ITEM_START.finditer(blob)]
    if not starts:
        return []
    blocks: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(blob)
        # trim to matching braces roughly: from item:{ ... }
        chunk = blob[start:end]
        # cut at qid if present after the item
        qid = chunk.find("}  qid:")
        if qid != -1:
            chunk = chunk[: qid + 1]
        blocks.append(chunk)
    return blocks


def parse_item(block: str) -> dict | None:
    text_m = FIELD_RE["text"].search(block)
    id_m = FIELD_RE["id"].search(block)
    if not text_m or not id_m:
        return None
    score_m = FIELD_RE["score"].search(block)
    sub_m = FIELD_RE["subtext"].search(block)
    icon_m = FIELD_RE["icon"].search(block)
    prov_m = FIELD_RE["provider"].search(block)
    return {
        "id": id_m.group(1),
        "text": text_m.group(1),
        "subtext": sub_m.group(1) if sub_m else "",
        "icon": icon_m.group(1) if icon_m else "",
        "provider": prov_m.group(1) if prov_m else "",
        "score": int(score_m.group(1)) if score_m else 0,
    }


def query_provider(provider: str, query: str, limit: int) -> list[dict]:
    if not shutil.which("elephant"):
        return []
    try:
        proc = subprocess.run(
            ["elephant", "query", f"{provider};{query};{limit}"],
            capture_output=True,
            text=True,
            timeout=1.5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    if not proc.stdout.strip():
        return []

    items: list[dict] = []
    for block in split_items(proc.stdout):
        item = parse_item(block)
        if item:
            items.append(item)
    items.sort(key=lambda i: i["score"], reverse=True)
    return items[:limit]


def main() -> int:
    if len(sys.argv) < 3:
        print("[]")
        return 0

    provider = sys.argv[1].strip()
    query = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 8

    if not provider:
        print("[]")
        return 0

    print(json.dumps(query_provider(provider, query, limit), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
