"""Shared TUR_USB H.264 chunk helpers (preamble / negotiate / PLAY / STOP)."""

from __future__ import annotations

import time
from pathlib import Path

from library.lcd.lcd_comm_turing_usb import (
    CMD_GET_H264_CHUNK_SIZE,
    CMD_GET_STREAM_STATUS,
    CMD_PLAY_H264_CHUNK,
    CMD_STOP_STREAM,
    build_command_packet_header,
    clear_image,
    delay,
    encrypt_command_packet,
    send_brightness_command,
    send_frame_rate_command,
    write_to_device,
)

DEFAULT_CHUNK = 202752
WIRE_W, WIRE_H = 800, 1280


def negotiate_chunk_size(dev) -> int:
    resp = write_to_device(dev, encrypt_command_packet(build_command_packet_header(CMD_GET_H264_CHUNK_SIZE)))
    chunk_size = DEFAULT_CHUNK
    if resp and len(resp) >= 12:
        negotiated = int.from_bytes(resp[8:12], byteorder="big", signed=False)
        if 0 < negotiated <= 1024 * 1024:
            chunk_size = negotiated
    return chunk_size


def video_preamble(dev, *, frame_rate: int, brightness_device: int = 32) -> None:
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(111)))
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(112)))
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(13)))
    send_brightness_command(dev, brightness_device)
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(41)))
    clear_image(dev)
    send_frame_rate_command(dev, frame_rate)


def play_chunk(dev, data: bytes, *, is_last: bool = False) -> bytes | None:
    chunksize = len(data)
    cmd_packet = build_command_packet_header(CMD_PLAY_H264_CHUNK)
    cmd_packet[8] = (chunksize >> 24) & 0xFF
    cmd_packet[9] = (chunksize >> 16) & 0xFF
    cmd_packet[10] = (chunksize >> 8) & 0xFF
    cmd_packet[11] = chunksize & 0xFF
    if is_last:
        cmd_packet[12] = 1
    return write_to_device(dev, encrypt_command_packet(cmd_packet) + data)


def flow_control(dev, response) -> bool:
    """Return True if a wait was inserted."""
    if response is None:
        delay(dev, 2)
        return True
    st = write_to_device(dev, encrypt_command_packet(build_command_packet_header(CMD_GET_STREAM_STATUS)))
    if st and len(st) > 8 and st[8] > 3:
        delay(dev, 2)
        return True
    return False


def stop_stream(dev) -> None:
    write_to_device(dev, encrypt_command_packet(build_command_packet_header(CMD_STOP_STREAM)))


def push_bytes(
    dev,
    data: bytes,
    *,
    chunk_size: int,
    is_last: bool = False,
) -> dict:
    """Push a byte blob as one or more PLAY chunks. Last slice gets is_last if requested."""
    offset = 0
    chunks = 0
    flow_waits = 0
    t0 = time.perf_counter()
    while offset < len(data):
        end = min(offset + chunk_size, len(data))
        piece = data[offset:end]
        last = is_last and end == len(data)
        resp = play_chunk(dev, piece, is_last=last)
        chunks += 1
        if flow_control(dev, resp):
            flow_waits += 1
        offset = end
    return {
        "bytes": len(data),
        "chunks": chunks,
        "flow_waits": flow_waits,
        "wall_s": round(time.perf_counter() - t0, 4),
    }
