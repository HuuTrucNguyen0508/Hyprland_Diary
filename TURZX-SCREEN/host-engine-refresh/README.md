# TURZX host-engine refresh

Dual-rate JPEG/PNG host loop, shared top-plate UI, ASAP speedtest gauges, and an opt-in H.264 live experiment. Built on top of the [refresh upgrade spike](../refresh-upgrade-spike/) (full-frame USB ceiling ~5 fps; dirty-rect USB is a no-go on the public library path).

Live code lives under `~/Documents/dashboard`. Prefer those paths if this folder drifts.

![Shared top-plate preview](preview-shared-plate.png)

## What shipped (always-on)

### Dual-rate + logical dirty skip

`dashboard.py` + `frame_dirty.py`:

| Mode | Interval | Dirty skip |
|------|----------|------------|
| Idle | 1.0 s (`--idle-interval` / `--interval`) | Yes |
| Scheme/palette burst (8 s) | 0.25 s (`--busy-interval`) | Yes |
| Speedtest gauges visible | **0** (`--speedtest-interval`, ASAP) | **No** |

Busy burst triggers when the Caelestia scheme identity changes. Speedtest uses flat-out full frames so the needles move as fast as USB allows (~4.7–5 fps measured earlier). Idle stays low-CPU.

Dirty fingerprint: scheme name/hash, speedtest fields, clock `%H:%M`, rounded stats (percents nearest 1, net nearest 0.1, temps nearest 1). Unchanged → skip `render` + `DisplayPILImage`, still sleep.

Orientation unchanged: `CONTENT_ROTATE = 0`, `Orientation.LANDSCAPE`, stock library USB `ROTATE_270` → wire **800×1280**. Do not skip library rotate.

### Shared metrics plate (mid-bar fix)

`renderer.py` draws CPU / GPU / RAM / picture as **one** rounded plate with vertical dividers. Four separate cards used to share a bottom edge; H.264 turned that into a full-width rule through the sparklines and logo. Normal gutter between the top plate and Storage/Bonsai/Weather stays.

### Service

```bash
systemctl --user restart turzx-dashboard.service
```

Unit copy: [`turzx-dashboard.service`](turzx-dashboard.service). Live unit: `~/.config/systemd/user/turzx-dashboard.service` (plus `PYTHONUNBUFFERED=1` drop-in).

## H.264 (opt-in experiment only)

Not wired into the user service. Clip path and live encoder are documented in [refresh-upgrade-spike](../refresh-upgrade-spike/). Copies here for convenience:

- [`turzx_h264_live.py`](turzx_h264_live.py) — live dashboard → ffmpeg (default libx264) → Annex-B chunks
- [`h264_usb.py`](h264_usb.py) — preamble / negotiate / PLAY / STOP helpers

```bash
systemctl --user stop turzx-dashboard.service
cd ~/Documents/dashboard && .venv/bin/python turzx_h264_live.py --seconds 12 --fps 15
systemctl --user start turzx-dashboard.service
```

USB is exclusive. Encode at wire **800×1280** (ROTATE_270 of the 1280×800 layout). Live path still has ~0.5 s first-paint latency and burns an encoder; keep JPEG dual-rate for boot/always-on unless you promote this later.

## Live paths

| Piece | Path |
|-------|------|
| Loop | `~/Documents/dashboard/dashboard.py` |
| Dirty / busy helpers | `~/Documents/dashboard/frame_dirty.py` |
| Layout / shared plate | `~/Documents/dashboard/renderer.py` |
| Orientation constants | `~/Documents/dashboard/turzx_screen.py` |
| Speedtest state | `~/Documents/dashboard/speedtest_state.py` |
| User service | `~/.config/systemd/user/turzx-dashboard.service` |
| Spike / H.264 inventory | [`../refresh-upgrade-spike/`](../refresh-upgrade-spike/) |
| Speedtest bind + engine | [`../../Speedtest-widget/`](../../Speedtest-widget/) |

## Copies in this folder

| File | Role |
|------|------|
| `dashboard.py` | Dual-rate loop, ASAP speedtest |
| `frame_dirty.py` | Fingerprint + scheme burst |
| `renderer.py` | Shared top plate + gauges |
| `turzx-dashboard.service` | Unit snapshot |
| `turzx_h264_live.py` / `h264_usb.py` | Opt-in H.264 experiment |
| `preview-shared-plate.png` | Layout preview after plate redesign |

## Related

- [What made TURZX work](../Process/) — orientation / stock rotate
- [Refresh upgrade spike](../refresh-upgrade-spike/) — fps ceiling, H.264 go bar, probe scripts
- [Speedtest widget](../../Speedtest-widget/) — Super+Shift+F engine and state JSON
