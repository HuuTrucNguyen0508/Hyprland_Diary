# T1 Approach 1 — host engine dual-rate + dirty skip

Live edits under `/home/theadenkingof/Documents/dashboard/` (service left running; no USB probe).

## Files

- `frame_dirty.py` (new): `palette_identity`, `logical_dirty_key`, `BusyTracker`
- `dashboard.py`: `--idle-interval` / `--interval` (default 1.0), `--busy-interval` (default 0.25); main loop uses busy pick + dirty skip

Unchanged: `CONTENT_ROTATE=0`, stock `DisplayPILImage` rotate path, systemd unit defaults.

## Busy

Busy sleep (`--busy-interval`, default 0.25s) when:

1. Speedtest overlay is visible (`SpeedtestState.visible`), or
2. Scheme/palette identity (name + colour hash) changed within the last 8s

Otherwise idle sleep (`--idle-interval` / `--interval`, default 1.0s).

## Dirty skip

Before render/USB, build a logical fingerprint:

- scheme name + content hash
- speedtest `(active, phase, down, up, error, until)`
- clock `%H:%M`
- rounded stats: CPU/GPU/RAM/disk (+ volume) % nearest 1; net kbps nearest 0.1; temps nearest 1

If equal to last sent fingerprint: skip `render*` and `DisplayPILImage`, still sleep the chosen interval.

## Deploy note

`turzx-dashboard.service` was not stopped or restarted. Restart the unit when you want the live panel to pick up this code.
