#!/usr/bin/env python3
"""Non-destructive TUR_USB storage probe (cmd 100).

Confirms this panel reports mmc-style card totals without writing files or
flashing. Soft restart (cmd 11) is opt-in via --restart (default off).

Stop turzx-dashboard.service first (USB exclusive):

  systemctl --user stop turzx-dashboard.service
  ~/Documents/dashboard/.venv/bin/python turzx_storage_probe.py
  systemctl --user start turzx-dashboard.service
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TURING_ROOT = Path.home() / "Documents" / "turing-smart-screen-python"
sys.path.insert(0, str(TURING_ROOT))

from library.lcd.lcd_comm_turing_usb import (  # noqa: E402
    PRODUCT_ID,
    VENDOR_ID,
    build_command_packet_header,
    encrypt_command_packet,
    find_usb_device,
    format_bytes,
    send_restart_device_command,
    write_to_device,
)

HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "storage_probe_results.json"
TARGET_PID = 0x0080
CMD_REFRESH_STORAGE = 100
SERVICE = "turzx-dashboard.service"


def dashboard_service_active() -> bool:
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", SERVICE],
            check=False,
        )
        return r.returncode == 0
    except OSError:
        return False


def parse_storage(response: bytes | None) -> dict:
    if response is None or len(response) < 20:
        return {
            "ok": False,
            "error": "no response or short packet",
            "response_len": 0 if response is None else len(response),
        }
    total_raw = int.from_bytes(response[8:12], byteorder="little")
    used_raw = int.from_bytes(response[12:16], byteorder="little")
    valid_raw = int.from_bytes(response[16:20], byteorder="little")
    return {
        "ok": True,
        "total_raw": total_raw,
        "used_raw": used_raw,
        "valid_raw": valid_raw,
        "total": format_bytes(total_raw),
        "used": format_bytes(used_raw),
        "valid": format_bytes(valid_raw),
        "response_len": len(response),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TURZX cmd-100 storage probe (read-only)")
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Also send soft restart cmd 11 after storage read (default: off)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON,
        help=f"Results JSON (default: {DEFAULT_JSON})",
    )
    parser.add_argument(
        "--allow-busy",
        action="store_true",
        help="Run even if turzx-dashboard.service is active (usually fails)",
    )
    args = parser.parse_args()

    results: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "vid": f"{VENDOR_ID:04x}",
        "target_pid": f"{TARGET_PID:04x}",
        "cmd": CMD_REFRESH_STORAGE,
        "restart_used": bool(args.restart),
    }

    if dashboard_service_active() and not args.allow_busy:
        msg = (
            f"{SERVICE} is active and holds USB. "
            f"Stop it first: systemctl --user stop {SERVICE}"
        )
        print(f"ERROR: {msg}", file=sys.stderr)
        results["ok"] = False
        results["error"] = msg
        args.json_out.write_text(json.dumps(results, indent=2) + "\n")
        return 2

    try:
        dev, dev_pid = find_usb_device()
    except Exception as exc:
        results["ok"] = False
        results["error"] = repr(exc)
        print(f"ERROR: open USB failed: {exc}", file=sys.stderr)
        args.json_out.write_text(json.dumps(results, indent=2) + "\n")
        return 1

    results["dev_pid"] = f"{dev_pid:04x}"
    results["product_wh"] = list(PRODUCT_ID.get(dev_pid, (None, None)))
    if dev_pid != TARGET_PID:
        print(
            f"WARNING: found PID 0x{dev_pid:04x}, expected 0x{TARGET_PID:04x}",
            file=sys.stderr,
        )

    print(f"Sending Refresh Storage Command (ID {CMD_REFRESH_STORAGE})...")
    t0 = time.perf_counter()
    response = write_to_device(
        dev, encrypt_command_packet(build_command_packet_header(CMD_REFRESH_STORAGE))
    )
    results["usb_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    storage = parse_storage(response)
    results["storage"] = storage
    results["ok"] = bool(storage.get("ok"))

    if storage.get("ok"):
        print(f"  Card Total = {storage['total']} ({storage['total_raw']})")
        print(f"  Card Used  = {storage['used']} ({storage['used_raw']})")
        print(f"  Card Valid = {storage['valid']} ({storage['valid_raw']})")
    else:
        print(f"ERROR: storage parse failed: {storage.get('error')}", file=sys.stderr)

    if args.restart:
        print("Sending Restart Command (ID 11)...")
        try:
            send_restart_device_command(dev)
            results["restart_ok"] = True
        except Exception as exc:
            results["restart_ok"] = False
            results["restart_error"] = repr(exc)
            print(f"WARNING: restart failed: {exc}", file=sys.stderr)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Wrote {args.json_out}")
    return 0 if results.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
