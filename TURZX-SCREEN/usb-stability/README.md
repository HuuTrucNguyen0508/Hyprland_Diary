# TURZX USB resets on game open/close

The panel can go black when a game starts or stops even if the cable never moves. That is a real USB re-enumerate (`1cbe:0080` disconnect + new device number), not a loose plug.

## What we saw

- Ambient was pushing ~3–4 full JPEG frames per second (`--ambient-interval 0`).
- The panel shares hub `1-5` with USB audio. Parent hub had been on `power/control=auto`.
- Kernel log: `usb 1-5.1: USB disconnect` then immediate re-plug. Dashboard kept a dead handle until reconnect logic ran.
- Auto game-mode flips (ambient ↔ stats) lined up with the freezes.

## What the dashboard does now

Live code: `~/Documents/dashboard/dashboard.py`

- Always-on stats at ~1 Hz. Speedtest overlay only (`Super+Shift+F`).
- Ambient, peek latch, and game-mode view switching are unused. JPEG flood plus view flips was resetting the panel.
- If USB is missing at start, the service stays up and retries with backoff (does not crash-loop on `USB device not found`).
- On errno 19 mid-run, drop the handle and reopen the same way.
- 0.35 s settle when switching stats ↔ speedtest.

Restart:

```bash
systemctl --user restart turzx-dashboard.service
```

Journal should show `views=stats,speedtest (ambient off)` then `view - -> stats`.

## Hub autosuspend (one-time, needs sudo)

Rule copy: [`99-turzx-usb-power.rules`](99-turzx-usb-power.rules)

```bash
sudo cp ~/Documents/Code/Hyprland_Diary/TURZX-SCREEN/usb-stability/99-turzx-usb-power.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger -c add -s usb -a idVendor=1cbe -a idProduct=0080
# or immediate:
echo on | sudo tee /sys/bus/usb/devices/1-5/power/control
echo on | sudo tee /sys/bus/usb/devices/1-5.1/power/control
```

## Quick check after a freeze

```bash
journalctl -k --since '10 min ago' | rg '1-5.1|1cbe'
journalctl --user -u turzx-dashboard.service --since '10 min ago' | rg 'view |USB |reconnected'
```
