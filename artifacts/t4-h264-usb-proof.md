# T4 — H.264 USB proof

**Verdict for live H.264 follow-up: NO-GO pending visual**

Gate bar = paint + latency + sustained no-wedge.

| Gate | Score |
|------|-------|
| Paint full glass | FAIL / unverified — coordinator `cannot-see` |
| Start latency | PASS — 107.68 ms to first chunk complete |
| Sustained no-wedge | PASS — 7/7 chunks, 1 flow wait, STOP + still restore, dashboard restarted clean |

## Run

1. Stopped `turzx-dashboard.service`
2. `turzx_h264_probe.py --usb --seconds 3 --fps 25`
3. Copied results into `TURZX-SCREEN/refresh-upgrade-spike/`
4. Restarted service — active, `SEND: (800, 1280) … LANDSCAPE`

Raw: `TURZX-SCREEN/refresh-upgrade-spike/h264_probe_results.json`
