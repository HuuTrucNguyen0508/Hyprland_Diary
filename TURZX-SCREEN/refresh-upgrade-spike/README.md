# TURZX refresh upgrade spike

Benchmark notes: how fast can this USB panel refresh when you send full JPEG frames? Useful if you are wondering whether partial updates or firmware changes are worth chasing.

Aug 2026. Can this TURZX (`1cbe:0080`) get a snappier refresh, or are we stuck uploading full compressed frames?

**Short answer:** ~5 fps full-frame JPEG ceiling on USB. Dirty-rect on the public library path is a no-go. H.264 on stock firmware works and became the opt-in live encoder. Shipped dual-rate + dirty skip: [host-engine-refresh](../host-engine-refresh/).

## Start here

Stop the dashboard before any USB probe. Port is exclusive.

```bash
systemctl --user stop turzx-dashboard.service
cd ~/Documents/dashboard && .venv/bin/python turzx_refresh_probe.py --frames 15
systemctl --user start turzx-dashboard.service
```

| Question | Answer |
|----------|--------|
| Faster always-on JPEG? | Dual-rate + dirty skip (~1 Hz idle, burst 0.25 s) |
| Partial USB updates? | No on public `DisplayPILImage` path |
| Smooth high refresh? | H.264 cmds 17/121/122/123; opt-in `turzx_h264_live.py` |
| Custom panel firmware? | See [custom-firmware-explore](../custom-firmware-explore/) — not worth it on the live unit |

First ceiling probe: 2026-08-21. Dual-rate + H.264 USB: 2026-08-22.

## Verdict

**True partial / dirty-rect USB: no-go** on the public library path. `DisplayPILImage(x, y)` pastes on the host into `current_state`, then always ships the whole 1280×800 canvas as PNG/JPEG. A 200×120 patch still produced a ~12 KB full-canvas PNG (`image_wh=1280x800`). A lone small JPEG is not a documented positioned blit.

**Soft full-frame bump (about 1 Hz → 2–4 Hz): go.** ASAP full frames held ~4.7 fps. Median ~211 ms/frame (~193 ms USB, ~14 ms encode). Encode is cheap; USB is the pipe. We miss a clean ≥5 fps bar, so 10–15 fps “monitor UI” full-frame is out. 0.25–0.5 s sleeps are still inside measured capability.

**`send_frame_rate_command` (cmd 15): no effect** on JPEG/PNG slideshow fps (10 / 25 / 60 all ~4.75 fps ASAP). That knob is for the H.264 path.

**Approach 1 (dual-rate + logical dirty skip): shipped and USB-smoked.** Live dashboard at `~/Documents/dashboard` (`dashboard.py`, `frame_dirty.py`). Idle stays 1.0 s by default; busy drops to 0.25 s. Unchanged fingerprint skips render + USB. Stock `LANDSCAPE` + `CONTENT_ROTATE=0` (library still rotates 270° to wire 800×1280). Systemd unit defaults unchanged. Top metrics are one shared plate (vertical dividers) so H.264 no longer gets a full-width bar through the sparklines.

**Approach 2 (H.264 USB clip path): go.** Watched 8s @25fps push (2026-08-22): full-glass paint, smooth, no jitter; start latency ~107 ms; STOP restored still; dashboard service came back. Library chunk cmds are enough for a follow-up live-encoder experiment. Dual-rate JPEG/PNG stays the always-on path until that lands.

**Live H.264 encoder experiment: works (opt-in).** Script `turzx_h264_live.py` (also under this spike folder): render dashboard → ROTATE_270 to wire 800×1280 → ffmpeg `h264_nvenc` (fallback libx264) → PLAY_H264_CHUNK. Not wired into `turzx-dashboard.service`. First usable glass ~0.8–0.9 s after start; ~15 fps encode; restore still on exit.

## Approach 1: dual-rate + logical dirty (2026-08-22)

Code: `~/Documents/dashboard/dashboard.py`, `~/Documents/dashboard/frame_dirty.py`. Smoke: `turzx_approach1_smoke.py` (not copied here; results summarized below).

### Behaviour

| Knob | Default | Role |
|------|--------:|------|
| `--idle-interval` / `--interval` | 1.0 s | Sleep when idle |
| `--busy-interval` | 0.25 s | Sleep when busy |

Busy when speedtest overlay is visible (`SpeedtestState.visible`), or when scheme/palette identity (name + colour hash) changed within the last 8 s.

Before render/USB, fingerprint:

- scheme name + content hash
- speedtest `(active, phase, down, up, error, until)`
- clock `%H:%M`
- rounded stats: CPU/GPU/RAM/disk (+ volumes) % nearest 1; net kbps nearest 0.1; temps nearest 1

Same as last sent → skip `render*` and `DisplayPILImage`, still sleep the chosen interval.

### USB smoke (PASS)

Exclusive USB, stock rotate, then service restored.

| Phase | Result |
|-------|--------|
| Upright stock path | PASS — `CONTENT_ROTATE=0`, `Orientation.LANDSCAPE`, wire 800×1280 |
| Idle dirty-skip | PASS — 1 send, 2 skips, intervals all 1.0 s (frozen fingerprint) |
| Busy scheme touch | PASS — intervals all 0.25 s after palette identity change |
| Busy speedtest | PASS — 4 sends @ 0.25 s while overlay visible |
| Service restore | PASS — active, journal `SEND: (800, 1280) … LANDSCAPE` |

## Approach 2: H.264 USB proof (2026-08-22)

Script: [`turzx_h264_probe.py`](turzx_h264_probe.py) (also at `~/Documents/dashboard/turzx_h264_probe.py`). JSON: [`h264_probe_results.json`](h264_probe_results.json). Clip: [`h264_probe_clip.h264`](h264_probe_clip.h264). Command map: [`h264-inventory.md`](h264-inventory.md).

Encode at wire size 800×1280. The H.264 path does not apply the JPEG/PNG host rotate.

```bash
systemctl --user stop turzx-dashboard.service
cd ~/Documents/dashboard && .venv/bin/python turzx_h264_probe.py --usb --seconds 3 --fps 25
systemctl --user start turzx-dashboard.service
```

| Metric | First USB (unwatched) | Watched 8s re-run |
|--------|----------------------:|------------------:|
| Wire encode | 800×1280 @ 25 fps, 3.0 s | 800×1280 @ 25 fps, 8.0 s |
| Clip bytes | 1 263 111 | 3 452 841 |
| Start latency (first chunk done) | 107.68 ms | 107.21 ms |
| Chunks / flow waits | 7 / 1 | 18 / 5 |
| Sustained | 0.495 MiB/s | 0.457 MiB/s |
| Wall push | 2.434 s | 7.203 s |
| STOP + still restore | yes | yes |
| Panel hang after STOP | no | no |
| Full-glass paint (eyes on panel) | not confirmed | **PASS** — smooth, no jitter |

Go bar was paint + latency + sustained no-hang. All three passed on the watched 8s run. **Live H.264 encoder follow-up: go** (clip path proven; live encode still to build).

## Live encoder experiment (2026-08-22)

Opt-in only. Does not replace `turzx-dashboard.service`.

```bash
systemctl --user stop turzx-dashboard.service
cd ~/Documents/dashboard && .venv/bin/python turzx_h264_live.py --seconds 12 --fps 15
systemctl --user start turzx-dashboard.service
```

Helpers: [`h264_usb.py`](h264_usb.py), live runner: [`turzx_h264_live.py`](turzx_h264_live.py). Results: [`h264_live_results.json`](h264_live_results.json).

| Metric | Value |
|--------|------:|
| Encoder | h264_nvenc (auto; libx264 fallback) |
| FPS / wire | 15 / 800×1280 |
| Frames in (10s run) | 108 |
| Chunks / bytes | 24 / ~1.4 MiB |
| Start latency (first USB chunk) | ~854 ms |
| Flow waits | 0 |
| Service restore | yes |

Tradeoff vs dual-rate JPEG: much higher refresh while streaming, but ~0.8 s to first paint, NVENC/ffmpeg always on, and the stream path clears the panel until STOP + still restore. Keep JPEG dual-rate for boot/always-on until you decide to promote this.

## Phase A: full-frame ceiling (2026-08-21)

Script: [`turzx_refresh_probe.py`](turzx_refresh_probe.py). JSON: [`refresh_probe_results.json`](refresh_probe_results.json).

Same orientation family as the dashboard (`LANDSCAPE`, library rotate to wire 800×1280). Simple counter layout; payloads were PNG (~14–15 KB for this sparse pattern).

| Interval | Achieved fps | total median (ms) | encode median (ms) | send median (ms) | payload |
|----------|-------------:|------------------:|-------------------:|-----------------:|--------:|
| 1.0 s | 1.06 | 211 | 14 | 193 | 14689 png |
| 0.5 s | 2.08 | 210 | 14 | 193 | 14689 png |
| 0.25 s | 4.04 | 211 | 14 | 193 | 14689 png |
| 0.1 s | 4.73 | 211 | 14 | 193 | 14689 png |
| ASAP | 4.74 | 211 | 14 | 193 | 14689 png |

Dense real dashboard frames will be larger and may sit a bit under these fps numbers.

## Phase B: partial vs host-composite

| Step | Payload | image_wh | Note |
|------|--------:|----------|------|
| Full solid green | 11106 png | 1280×800 | Baseline full canvas |
| `DisplayPILImage(patch, 100, 100)` | 12523 png | 1280×800 | Host composite; USB still full frame (ratio 1.13×) |
| Raw 200×120 JPEG alone | 2585 jpeg | 200×120 | Not a library region update |

Glass during the run: library paste kept the green field and added the red patch on the host. That is not device-side partial USB.

## Phase C: frame-rate command

| cmd 15 value | ASAP fps after |
|-------------:|---------------:|
| 10 | 4.75 |
| 25 | 4.75 |
| 60 | 4.74 |

No meaningful spread. Ignore cmd 15 for the dashboard slideshow.

## Protocol notes

- Upload cmds: JPEG 101, PNG 102 (`send_pil_image_auto` prefers PNG under the size cap).
- Older serial Turing revisions do RGB565 rectangles; `lcd_comm_turing_usb.py` is not that path.
- H.264 uses cmds 17 / 15 / 121 / 122 / 123. See [`h264-inventory.md`](h264-inventory.md).
