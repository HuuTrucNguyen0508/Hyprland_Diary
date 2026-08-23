# TURZX custom firmware explore

Research on whether custom panel firmware is realistic on this hardware. Spoiler: host-side tricks were enough; flashing the daily-driver panel was not worth the brick risk.

Aug 2026. Can we flash custom firmware on this 8" TUR_USB panel (`1cbe:0080`), and would it help the live dashboard?

**Short answer:** No for the panel you actually use. Host-side wins (dual-rate JPEG, opt-in H.264) are enough. Firmware RE needs a spare unit and is brick-risky with no known recovery image.

## Start here

Do not flash the production panel. `turzx-dashboard.service` depends on stock firmware behaviour.

| If you want | Do this instead |
|-------------|-----------------|
| Snappier glass | Opt-in H.264: [host-engine-refresh](../host-engine-refresh/) |
| Always-on low CPU | JPEG dual-rate (boot default) |
| Storage probe | `turzx_storage_probe.py` in this folder (stop service first) |
| Open the case | Spare hardware only |

Researched 2026-08-22. No teardown on the live unit yet.

Related: [Process/](../Process/), [refresh-upgrade-spike/](../refresh-upgrade-spike/), [host-engine-refresh/](../host-engine-refresh/).

## Verdict

**Custom firmware is not a practical next step for this live setup.** Feasibility as a long RE project is "maybe, after a teardown and a spare panel." Feasibility as something that improves refresh without risking the working dashboard is **low**.

What exists today is reverse-engineered **host** protocol (DES-CBC bulk USB, JPEG/PNG/H.264). Nobody has published open panel firmware, a flash tool, a bootloader unlock, or a confirmed SoC + pinout for the TUR_USB family. The refresh wins you already measured (dual-rate JPEG ~5 fps ceiling, H.264 clip/live path) are host-side and leave stock firmware alone.

If the goal is snappier glass with minimal blast radius, keep investing in the opt-in H.264 host path. Treat firmware as a separate, spare-hardware track only.

## Hardware identity

### Confirmed on this machine (2026-08-22)

```text
lsusb -d 1cbe:0080
# Bus 001 Device 004: ID 1cbe:0080 Luminary Micro Inc. TURZX1.0
```

| Fact | Value | Source |
|------|-------|--------|
| VID:PID | `1cbe:0080` | `lsusb`, diary AGENTS.md |
| USB-IF vendor string | Luminary Micro Inc. | `lsusb` (historical TI Stellaris ID; many OEMs reuse it) |
| Product / mfr strings | `TURZX1.0` / `TURZX` | sysfs `/sys/bus/usb/devices/…/product` |
| Speed | USB 2.0 High Speed (480 Mbps) | `lsusb -v` |
| Class | Vendor-specific (255/255/255) | `lsusb -v` |
| Endpoints | Bulk IN `0x81` + Bulk OUT `0x01`, `wMaxPacketSize` 512 | `lsusb -v` |
| MaxPower | 120 mA | `lsusb -v` |
| Protocol family | TUR_USB (not UART/CDC) | [turing-smart-screen-python 3.10.0](https://github.com/mathoudebine/turing-smart-screen-python/releases/tag/3.10.0) |
| Portrait table size | 800×1280 for PID `0x0080` | `PRODUCT_ID` in `lcd_comm_turing_usb.py` |
| Firmware framebuffer | Portrait 800×1280 on the wire | [Process/README.md](../Process/README.md) |

USB-IF name "Luminary Micro" is **not** a chip ID. Do not treat it as "this is a Stellaris MCU."

### What the protocol implies (still not a part number)

TUR_USB devices behave like a small Linux appliance, not a bare 8-bit MCU:

- On-device paths used by upload/play: `/tmp/sdcard/mmcblk0p1/img/` and `…/video/` ([phstudy/turing-smart-screen-cli](https://github.com/phstudy/turing-smart-screen-cli), mirrored in local `lcd_comm_turing_usb.py` `upload_file`).
- Soft restart command ID **11**.
- Storage stats command ID **100** (card total/used/valid).
- File open/write/delete (**38 / 39 / 40**) and play (**98 / 110 / 113**).
- Live H.264 chunk stream (**17 / 15 / 121 / 122 / 123**) that the panel decodes itself ([h264-inventory.md](../refresh-upgrade-spike/h264-inventory.md), [Hal9000AIML/turzx-blue-8.8](https://github.com/Hal9000AIML/turzx-blue-8.8)).

That points at some application SoC + Linux userspace + MMC/SD storage + JPEG and H.264 decode. Exact silicon is **unknown** until someone photographs the PCB.

### Do not confuse with older Turing UART hardware

The project wiki documents **WCH CH552T** for older **3.5" USB-serial** style devices. That is a different generation and protocol path ([Hardware revisions wiki](https://github.com/mathoudebine/turing-smart-screen-python/wiki/Hardware-revisions)).

Older 8.8" units use UART / gadget serial (`0x0525:0xa4a7`, `0x1a86:0xca88`). Newer "v1.x" USB units use `1cbe:00xx` bulk. Community note: same Windows app package ships for both; **PCB markings** are the ground truth ([issue #727](https://github.com/mathoudebine/turing-smart-screen-python/issues/727)).

Some USB 8.8" logs also show a companion interface `1cbe:f000` product `USB-Daemon`, manufacturer `turzx.com`, next to `1cbe:0088` TURZX1.0. This 8" host currently shows only `1cbe:0080` (no `f000` sibling in `lsusb`).

### Display controller / USB bridge

No public teardown naming the LCD controller or a discrete USB bridge for TUR_USB 8". The host only sees one vendor bulk interface. Bridge vs SoC-integrated USB gadget is unknown without opening the case.

## Stock firmware and update path

| Path | What it is | Notes |
|------|------------|-------|
| Official Windows app | Size-specific downloads on [turzx.com](https://www.turzx.com/) (8" app page: [8inch APP](https://www.turzx.com/2025/05/26/8_inch/); backup index: [DirectDownload](https://www.turzx.com/2025/05/27/%E7%9B%B4%E9%93%BE%E4%B8%8B%E8%BD%BDdirectdownload-2/)) | Themes + video folders copy into `TURZX_V3.x`. Closed-source .NET. |
| Forum | [discuz.turzx.com](http://discuz.turzx.com/) | Vendor support; mathoudebine points hardware issues there. |
| TF card format tool | Listed next to app downloads on the DirectDownload page | Storage hygiene, not open firmware. |
| Soft restart | Protocol cmd **11** (`send_restart_device_command`) | Reboots panel firmware; library leaves it disabled on init. |
| Persist settings | Cmd **125** (brightness, startup, rotation, sleep, offline) | "Flash" here means NVRAM settings, not replacing the OS image. |
| UART-era "ROM version" | e.g. `chs_88inch.dev1_rom1.90` on older serial 8.8" ([issue #724](https://github.com/mathoudebine/turing-smart-screen-python/issues/724)) | Different hardware family from this USB 8". |

No public DFU/USB bootloader docs, no open `.img` / `.bin` flash package, and no community "restore stock firmware" guide for TUR_USB turned up in this pass. Official distribution is **apps + themes**, not firmware blobs you can audit.

## Community / open projects

All of these talk to **stock** firmware over USB. None replace it.

| Project | Role | Fits this panel? |
|---------|------|------------------|
| [mathoudebine/turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) | Main host library + system monitor; TUR_USB since 3.10.0 | Yes (`0x0080` in `PRODUCT_ID`) |
| [phstudy/turing-smart-screen-cli](https://github.com/phstudy/turing-smart-screen-cli) | Original USB protocol CLI (sync, storage, PNG, H.264) | Written for `0x0088`; same protocol family as `0x0080` |
| Forks (`habibrehmansg/turing-screen-cli`, `matthewgjohnson/turing-smart-screen-cli`) | Same CLI lineage | Same |
| [RexPhoe/open-turzx](https://github.com/RexPhoe/open-turzx) | Open host dashboard for **2.8"** (`0x0028`); DEVLOG documents DES-CBC | Host only; different PID |
| [Hal9000AIML/turzx-blue-8.8](https://github.com/Hal9000AIML/turzx-blue-8.8) | Host H.264 theme replacement for stock TURZX.exe on 8.8" | Same idea as your live H.264 experiment; still stock FW |
| Thermalright TRCC Linux | Separate product family; some units also show `1cbe:0088` TURZX1.0 ([issue #258](https://github.com/Lexonight1/thermalright-trcc-linux/issues/258)) | Not firmware for this panel |

Local protocol copy used by the diary: `TURZX-SCREEN/Process/lcd_comm_turing_usb.py` (and live clone under `~/Documents/turing-smart-screen-python`).

**Search result:** GitHub code search for TURZX/turing custom firmware / DFU / bootloader flash tooling returned nothing useful. Community energy is protocol + dashboards.

## What firmware could unlock vs what the host already can

| Goal | Host today (stock FW) | Would custom FW help? |
|------|----------------------|------------------------|
| Full-frame JPEG/PNG refresh | ~4.7–5 fps ASAP; USB ~193 ms/frame median ([refresh-upgrade-spike](../refresh-upgrade-spike/)) | Maybe slightly if decode/USB stack is soft, but HS bulk + full canvas is already the bottleneck story |
| Dirty-rect / partial blit | **No** on public library path; `DisplayPILImage(x,y)` still ships full canvas | **Yes**, if you add a real region update command (or find a hidden stock one) |
| Smooth UI | H.264 cmds 17/121/122/123 proven; live encoder opt-in | Already unlocked on stock FW |
| Native landscape FB | Host rotates 270° so wire stays 800×1280 | Convenience only; stock path works |
| Higher USB throughput | USB2 HS, 512 B packets; H.264 sustained ~0.45–0.5 MiB/s in spike | Speculative; need profiling before blaming the pipe |
| Dual-boot / A/B slots | Unknown | Unknown; no evidence either way |

Bottom line from the spike: **stock firmware already has the high-refresh path (H.264).** The missing piece for "snappy always-on dashboard" is a host encoder/service design, not a new panel OS. Custom FW only becomes interesting for true dirty-rect, lower idle power, or fixing orientation without host rotate.

## Minimal-impact development plan

Rule: **never flash the panel that runs `turzx-dashboard.service`.** Explore firmware only after a spare unit exists. Until then, stay on host experiments.

### Parallel to live dashboard (safe now)

1. Keep JPEG dual-rate as the boot/always-on service ([host-engine-refresh](../host-engine-refresh/)).
2. Run H.264 live via toggle (or stop/start sandwich). See [host-engine-refresh H.264](../host-engine-refresh/README.md#h264-opt-in-only-jpeg-remains-boot-default).
3. Storage probe (cmd 100) below: same exclusive-USB sandwich.
4. Prefer a throwaway script under this folder for command probes. Do not edit the live library path casually.
5. Soft restart (cmd 11) is safer than yanking power if the panel wedges; still stop the dashboard first. Probe exposes it as `--restart` (default off).
6. Optional: Windows VM + official 8" TURZX app only when you need a known-good vendor path (themes/storage). Not required for the Linux dashboard.

### Cmd 100 storage probe (done 2026-08-22)

Script: [`turzx_storage_probe.py`](turzx_storage_probe.py). Results: [`storage_probe_results.json`](storage_probe_results.json).

```bash
systemctl --user stop turzx-dashboard.service
cd ~/Documents/Code/Hyprland_Diary/TURZX-SCREEN/custom-firmware-explore
~/Documents/dashboard/.venv/bin/python turzx_storage_probe.py
systemctl --user start turzx-dashboard.service
```

| Field | Result |
|-------|--------|
| PID | `0080` |
| Response | 512 B packet, `ok: true` |
| Card total / used / valid | **0 / 0 / 0** |
| USB round-trip | ~101 ms |
| Restart used | no |

Cmd 100 works on this unit (protocol answers). Raw counters are all zero, so this 8" either has no TF/mmc accounting exposed or an empty card path. That still supports “Linux-shaped storage API” without proving a populated filesystem. No files written; no flash.

### Firmware track (only with a spare panel)

1. Photograph PCB (SoC, flash, LCD connector, UART pads, boot buttons).
2. Dump USB descriptors + any second interface (`f000` USB-Daemon) on that unit.
3. Capture vendor app USB traffic during any "update" UI (Wireshark/usbmon) to see if a real firmware write exists.
4. If Linux userspace is confirmed (shell via UART), explore whether stock update is just a file drop to mmc, not a locked bootloader.
5. Only then talk about custom images / recovery. Assume brick risk until proven otherwise.

## Risks and recovery

| Risk | Severity | Mitigation |
|------|----------|------------|
| Soft lock from aggressive command spam | Medium (seen on 2.8" open-turzx: freeze until replug) | Minimal command sequences; stop dashboard; keep cmd 11 and physical replug ready |
| H.264 hang without STOP (123) | Medium | Always STOP + still restore in `finally`; spike scripts already do this |
| Orientation / leftover TURZX V2 wallpaper | Low–medium | Keep stock library `ROTATE_270`; wire size must stay 800×1280 ([Process](../Process/)) |
| Flashing unknown image | **High / possibly permanent** | Do not flash production panel; no known recovery image |
| Official Windows updater on Linux host | Low (wrong OS) | Use a Windows box/VM if you ever need vendor restore |
| Dual-boot / safe A/B | Unknown | Treat as **absent** until proven |

Recovery for host-side mess: stop probes, `systemctl --user start turzx-dashboard.service`, confirm journal `SEND: (800, 1280) … LANDSCAPE`. Replug USB if the gadget stops answering.

Recovery after a bad flash: **no documented community path.** That alone is why firmware stays off the live unit.

## Open questions / next probes

1. **PCB photo** of this 8" board (SoC marking, flash package, UART header). Highest information density per minute of work.
2. Does this unit expose `1cbe:f000` USB-Daemon under any condition (cold plug, Windows, after cmd 11)?
3. ~~Non-destructive **cmd 100** storage dump~~ **Done (2026-08-22):** cmd 100 answers on `0080`; totals are 0/0/0. See [`storage_probe_results.json`](storage_probe_results.json).
4. Vendor app packet capture: is there a firmware-update command, or only theme/video file writes (38/39)?
5. UART pads: is there a Linux console? That changes the whole "custom firmware" story from bootloader hell to userspace patching.
6. Hidden stock protocol for dirty-rect? UART 5" models had changed-pixel commands ([issue #90](https://github.com/mathoudebine/turing-smart-screen-python/issues/90)); TUR_USB public code does not. Worth a careful RE pass on the Windows binary before writing silicon firmware.
7. Power / thermal under sustained H.264 vs dual-rate JPEG on the always-on desk.

## Sources

### Local

- `TURZX-SCREEN/Process/README.md`, `Process/lcd_comm_turing_usb.py`
- `TURZX-SCREEN/refresh-upgrade-spike/README.md`, `h264-inventory.md`
- `TURZX-SCREEN/host-engine-refresh/README.md`
- `TURZX-SCREEN/custom-firmware-explore/turzx_storage_probe.py`, `storage_probe_results.json`
- Live library: `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py`
- This host USB: `lsusb -d 1cbe:0080`, `lsusb -v -d 1cbe:0080`, sysfs under `/sys/bus/usb/devices/`

### Upstream / vendor

- https://github.com/mathoudebine/turing-smart-screen-python
- https://github.com/mathoudebine/turing-smart-screen-python/releases/tag/3.10.0
- https://github.com/mathoudebine/turing-smart-screen-python/wiki/Hardware-revisions
- https://github.com/mathoudebine/turing-smart-screen-python/issues/727
- https://github.com/mathoudebine/turing-smart-screen-python/issues/724
- https://github.com/mathoudebine/turing-smart-screen-python/issues/90
- https://github.com/phstudy/turing-smart-screen-cli
- https://github.com/RexPhoe/open-turzx
- https://github.com/Hal9000AIML/turzx-blue-8.8
- https://www.turzx.com/2025/05/26/8_inch/
- https://www.turzx.com/2025/05/27/%E7%9B%B4%E9%93%BE%E4%B8%8B%E8%BD%BDdirectdownload-2/
- http://discuz.turzx.com/
