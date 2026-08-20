# TURZX 8" screen: what actually made it work

USB `1cbe:0080` TURZX1.0, 8" panel, mounted landscape-wide. Custom dashboard at `~/Documents/dashboard`. USB driver / protocol code comes from [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) (local clone at `~/Documents/turing-smart-screen-python`, TUR_USB revision).

This screen lied to me a lot.

![Working TURZX dashboard preview](../Photo/preview.png)

## Hardware facts that are easy to get wrong

- The USB product table still reports native portrait as 800×1280.
- On this unit, the library's portrait / landscape names do not match what you see on the glass.
- Send a 1280×800 image into an 800×1280 buffer (or the reverse) and you get crop, wrap, a vertical seam, duplicated panels. A mess.
- Stock `turing-smart-screen-python` `DisplayPILImage` rotated the image before USB send (`LANDSCAPE` → 270°, `PORTRAIT` → 180°, and so on). That fought the dashboard's own rotation on this panel.

## Working path

1. Draw the dashboard at 1280×800 (`renderer.py`).
2. Flip content 180° in `dashboard.py` (`CONTENT_ROTATE = 180`) so text is upright on this mount.
3. Send a 1280×800 frame with `Orientation.LANDSCAPE`.
4. Do not zoom or crop (`DEFAULT_ZOOM = 1.0`, `DEFAULT_FIT = 1.0`, crop anchor `center`).

```bash
cd ~/Documents/dashboard
.venv/bin/python dashboard.py
```

## Change 1: disable library USB rotation

File: `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py`  
Function: `LcdCommTuringUSB.DisplayPILImage`

Stock code rotated `current_state` depending on orientation, then sent that. On this TURZX that inverted or cropped the picture.

Comment out those `transpose(...)` branches and always send the buffer as-is:

```python
base_image = self.current_state
```

`SetOrientation()` still picks canvas size (1280×800 vs 800×1280). The dashboard owns flip and scale.

There is a leftover debug `print("SEND:", ...)` in the same function. Not required for display.

Stock `main.py` / `8inchTheme2` expect the old rotation. Revert this patch if you run the official theme again.

## Change 2: send landscape 1280×800 from the dashboard

File: `~/Documents/dashboard/turzx_screen.py`

| Setting | Value | Why |
|---|---|---|
| `NATIVE_WIDTH` / `NATIVE_HEIGHT` | 1280 × 800 | Canvas sent to the LCD |
| `LCD_ORIENTATION` | `Orientation.LANDSCAPE` | Matches that canvas |
| `CONTENT_ROTATE` | 180 | Upright on this mount |
| `DEFAULT_SCALE` | `letterbox` | Keep aspect ratio |
| `DEFAULT_ZOOM` | 1.0 | Zoom > 1 crops edges |
| `DEFAULT_FIT` | 1.0 | Fill the 1280×800 canvas |
| `DEFAULT_CROP_ANCHOR` | `center` | No corner crop |

`LcdCommTuringUSB.__init__` still overwrites width/height from `PRODUCT_ID` (800×1280 for `0x0080`). Orientation `LANDSCAPE` swaps those via `get_width()` / `get_height()`, so the send buffer is 1280×800.

## Change 3: keep the layout wide

Files: `~/Documents/dashboard/renderer.py`, `dashboard.py`

Layout stays 1280×800 (header + 4 metric cards + Network / System / Activity). Do not rebuild a portrait UI for 800×1280. That looked "correctly filled" and was still the wrong orientation.

Do not letterbox a 1280×800 frame into 800×1280 as the main path either. Bars, half-screen content, or stretch distortion.

`--nudge-x/y`, `--fit`, and `--zoom` are still there for fine-tuning. The defaults above are the working set.

## What failed

| Approach | Result |
|---|---|
| `REVERSE_PORTRAIT` + 800×1280 send of a 1280×800 image | Wrap / split / missing cards |
| Library `PORTRAIT` for "correct red top-left" in diag | Tall buffer → dashboard shown as portrait |
| `--zoom 1.2` + crop `top-right` after 1280×800 LANDSCAPE | Top and right of the dashboard cut off |
| Fractional `--offset-y` (e.g. 0.5) | Jumped to a clamp ("dead zone"); tiny positives pinned to the top |
| `--offset-x` while letterbox filled 800px width | No real horizontal move; edges clipped |
| Stretch 1280×800 → 800×1280 | Full screen but distorted; still "wide on a tall panel" |

`turzx_diag.py` with `PORTRAIT` often put the red corner at physical top-left. That orientation is still the wrong canvas for a landscape dashboard.

## Positioning rules if you nudge later

- Integer pixel `--nudge-x` / `--nudge-y` from center. Not fractional offsets.
- Keep `--zoom 1.0` unless you accept cropped edges.
- `--fit` below 1.0 shrinks the image and adds margin. Not needed for the working layout.

## Paths

| Piece | Path |
|---|---|
| Dashboard | `~/Documents/dashboard/` |
| Screen defaults | `~/Documents/dashboard/turzx_screen.py` |
| Layout | `~/Documents/dashboard/renderer.py` |
| USB library (patched) | `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py` |
| Official config (reference) | `~/Documents/turing-smart-screen-python/config.yaml` — `REVISION: TUR_USB`, theme `8inchTheme2` |
| Boot daemon | `~/.config/systemd/user/turzx-dashboard.service` |

## Boot daemon

`turzx-dashboard.service` starts after login, and at boot if lingering is on. It waits on `network-online.target` so the weather card does not race DNS. It conflicts with the old `turing-smart-screen.service` because the USB device is exclusive.

```bash
systemctl --user daemon-reload
systemctl --user enable --now turzx-dashboard.service
loginctl enable-linger "$USER"   # start at boot, before login
```

```bash
systemctl --user status turzx-dashboard.service
systemctl --user restart turzx-dashboard.service
systemctl --user stop turzx-dashboard.service
journalctl --user -u turzx-dashboard.service -f
```

Do not run `python dashboard.py` by hand while the service is active. USB busy.

## Brightness

Lives in `~/.config/turzx/config.json`. Picked up within ~1s, no restart:

```bash
python ~/Documents/dashboard/turzx-ctl.py brightness 40
# or
echo '{"brightness": 40}' > ~/.config/turzx/config.json
```

## Caelestia colours

Palette sync (reads `~/.local/state/caelestia/scheme.json` each frame) lives with the other theme notes:

[TURZX follows Caelestia](../../Caelestia_theme_sync/turzx/)

## Copies in this folder

| File | Live path |
|------|-----------|
| `turzx-dashboard.service` | `~/.config/systemd/user/turzx-dashboard.service` |
| `turzx_screen.py` | `~/Documents/dashboard/turzx_screen.py` |
| `lcd_comm_turing_usb.py` | `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py` |
| `config.yaml` | `~/Documents/turing-smart-screen-python/config.yaml` |
| `turzx-config.json` | `~/.config/turzx/config.json` |
