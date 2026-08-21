# H.264 inventory (Approach 2) — T2 gate note

Source: `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py`.
Probe skeleton (no USB by default): `~/Documents/dashboard/turzx_h264_probe.py`.

## Command map

| Cmd | Name | Role |
|----:|------|------|
| 17 | `CMD_GET_H264_CHUNK_SIZE` | Negotiate max Annex-B chunk. Response bytes 8–11 big-endian. Fallback in code: **202752**. Cap check: `0 < n ≤ 1 MiB`. |
| 15 | frame rate (video path) | `send_frame_rate_command`: byte 8 = fps. `send_video` hardcodes **25**. Prior JPEG spike showed cmd 15 does nothing for PNG/JPEG slideshow; it belongs here. |
| 121 | `CMD_PLAY_H264_CHUNK` | Header size in bytes 8–11 (BE). Byte 12 = 1 on last chunk of file. Payload = encrypted 512-byte cmd + raw Annex-B bytes. |
| 122 | `CMD_GET_STREAM_STATUS` | Flow control. Queue depth in `resp[8]`. `send_video` waits via `delay()` when depth **> 3** or when PLAY response is `None`. (`delay` also *is* cmd 122; the print string says "Delay Command".) |
| 123 | `CMD_STOP_STREAM` | Always sent in `send_video` `finally`. Probe must call this on exit/interrupt. |

## `send_video()` framing

1. `extract_h264_from_mp4`: prefer ffmpeg `-c:v copy -bsf:v h264_mp4toannexb -f h264`; else pure-Python MP4 → Annex-B with SPS/PPS start codes (`00 00 00 01`), optional repeat on sync samples.
2. Preamble (before chunks): cmds **111, 112, 13**, brightness **14**, **41**, `clear_image` (**102**), frame rate **15**=25.
3. Negotiate chunk size (17).
4. Read file in `chunk_size` slices → PLAY_H264_CHUNK (121) + flow-control poll (122).
5. Optional loop of the whole `.h264` file.
6. STOP_STREAM (123).

No host-side rotate on this path. JPEG/PNG `DisplayPILImage` rotates **270°** for `Orientation.LANDSCAPE` so the wire is **800×1280**. H.264 must be encoded at that wire size (or it will look sideways / strip + leftover wallpaper like raw landscape stills).

## Library-first path: sound enough to USB-test?

Yes, for a bounded proof. The chunk negotiate / PLAY / status / STOP sequence is complete and already used by the vendor sample path. ffmpeg + Annex-B matches what `extract_h264_from_mp4` produces. The probe mirrors that loop with timing hooks and restores a still after STOP.

## Risks

- **Orientation mistake**: encoding 1280×800 without the stock 270° transform will mis-paint the glass.
- **Preamble side effects**: cmds 111/112/13/41 and `clear_image` are opaque; may disturb brightness or leave a blank frame if restore fails.
- **USB exclusive**: must stop `turzx-dashboard.service` first; a hung stream without STOP_STREAM may need a replug or dashboard restart.
- **Flow-control stalls**: aggressive push with queue depth >3 burns time in `delay()`; sustained MiB/s may look worse than peak chunk write.
- **Decoder limits**: baseline / yuv420p / no B-frames is the safe guess; untested profiles may fail silently on glass.
- **Not a live dashboard encoder**: this path plays a prebuilt clip. Live UI-as-H.264 needs a continuous encoder + chunker; T4 only proves the pipe.

## Gate recommendation for T4 (USB proof)

**GO** for a short, supervised USB run of the skeleton (`--usb`, ~2–3 s clip, stop dashboard first, restart after).

Success criteria for T4: Annex-B appears upright on glass, START latency + sustained push numbers land in JSON, STOP_STREAM + still restore leave the panel usable, dashboard service comes back clean.

**No-go** only if T4 shows decode refusal, permanent hang after STOP, or orientation that cannot be fixed by wire-size encoding. Do not treat H.264 as the dashboard redesign until T4 passes; dual-rate full-frame JPEG/PNG remains the low-risk snappiness path from the prior spike.

## T4 result (2026-08-22)

First USB run: instrumentation OK (`start_latency_ms=107.68`, 7 chunks, STOP + still), paint unconfirmed.

Watched re-run: `--usb --seconds 8 --fps 25`. Metrics `start_latency_ms=107.21`, 18 chunks, 5 flow waits, STOP restored. Eyes on panel: **full paint, smooth, no jitter**.

**Live H.264 encoder follow-up: GO** (clip path proven). See spike README Approach 2.
