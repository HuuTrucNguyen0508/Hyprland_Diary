# T3 — Approach 1 USB smoke

**Verdict: PASS**

## Procedure

1. Stopped `turzx-dashboard.service` (exclusive USB).
2. Ran `/home/theadenkingof/Documents/dashboard/turzx_approach1_smoke.py` (no H.264).
3. Coordinator confirmed glass upright (`upright-pass`).
4. Restarted service; journal shows `SEND: (800, 1280) … LANDSCAPE`, process active.

## Results

| Phase | Result |
|-------|--------|
| Upright stock path | PASS — `CONTENT_ROTATE=0`, `Orientation.LANDSCAPE`, wire 800×1280 |
| Idle dirty-skip | PASS — 1 send, 2 skips, intervals all 1.0s (frozen fingerprint) |
| Busy scheme touch | PASS — intervals all 0.25s after palette identity change |
| Busy speedtest | PASS — 4 sends @ 0.25s while overlay visible |
| Service restore | PASS — active, sync + brightness + first SEND |

Raw JSON: `artifacts/t3-approach1-usb-smoke.json`
