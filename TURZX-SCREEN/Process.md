# TURZX 8" screen — what actually made it work

Hardware: USB `1cbe:0080` TURZX1.0, 8" panel.  
Software: custom dashboard at `~/Documents/dashboard`, driver library at `~/Documents/turing-smart-screen-python`.  
Physical mount: landscape (wide).

## Hardware facts (easy to get wrong)

- The USB product table still reports native portrait as **800×1280**.
- On this unit, the library’s **portrait / landscape names do not match** what you see on the glass.
- Sending a **1280×800** image into an **800×1280** buffer (or the reverse) causes crop, wrap, a vertical seam, and duplicated panels.
- Official `turing-smart-screen-python` `DisplayPILImage` used to rotate the image before USB send (`LANDSCAPE` → 270°, `PORTRAIT` → 180°, etc.). That extra rotation fought the dashboard’s own rotation on this screen.

## Final working path

1. Draw the dashboard at **1280×800** (`renderer.py`).
2. Flip content **180°** in `dashboard.py` (`CONTENT_ROTATE = 180`) so text is upright on this mount.
3. Send a **1280×800** frame with `Orientation.LANDSCAPE`.
4. Do **not** zoom/crop (`DEFAULT_ZOOM = 1.0`, `DEFAULT_FIT = 1.0`, crop anchor `center`).

Run:

```bash
cd ~/Documents/dashboard
.venv/bin/python dashboard.py
```

## Change 1 — disable library USB rotation

**File:** `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py`  
**Function:** `LcdCommTuringUSB.DisplayPILImage`

Stock code rotated `current_state` depending on orientation, then sent that. On this TURZX that inverted or cropped the picture.

**Change:** comment out those `transpose(...)` branches and always send the buffer as-is:

```python
base_image = self.current_state
```

`SetOrientation()` still picks canvas size (`1280×800` vs `800×1280`). The dashboard owns flip/scale.

A debug `print("SEND:", ...)` was left in the same function; it is not required for display.

**Note:** stock `main.py` / `8inchTheme2` expect the old rotation. Revert this patch if you run the official theme again.

## Change 2 — send landscape 1280×800 from the dashboard

**File:** `~/Documents/dashboard/turzx_screen.py`

Working defaults:

| Setting | Value | Why |
|---|---|---|
| `NATIVE_WIDTH` / `NATIVE_HEIGHT` | 1280 × 800 | Canvas sent to the LCD |
| `LCD_ORIENTATION` | `Orientation.LANDSCAPE` | Matches that canvas |
| `CONTENT_ROTATE` | 180 | Upright on this mount |
| `DEFAULT_SCALE` | `letterbox` | Keep aspect ratio |
| `DEFAULT_ZOOM` | 1.0 | Zoom > 1 crops edges |
| `DEFAULT_FIT` | 1.0 | Fill the 1280×800 canvas |
| `DEFAULT_CROP_ANCHOR` | `center` | No corner crop |

`LcdCommTuringUSB.__init__` still overwrites width/height from `PRODUCT_ID` (`800×1280` for `0x0080`). Orientation `LANDSCAPE` swaps those via `get_width()` / `get_height()`, so the send buffer is 1280×800.

## Change 3 — keep the layout wide; do not stretch into a tall buffer

**Files:** `~/Documents/dashboard/renderer.py`, `dashboard.py`

- Layout is always **1280×800** (header + 4 metric cards + Network / System / Activity).
- Do **not** rebuild a portrait UI for 800×1280. That looked “correctly filled” but was the wrong orientation.
- Do **not** letterbox a 1280×800 frame into 800×1280 as the main path: that left bars, half-screen content, or stretch distortion.

Positioning helpers in `dashboard.py` (`--nudge-x/y`, `--fit`, `--zoom`) remain for fine-tuning. Defaults above are the working set.

## What failed (and why)

| Approach | Result |
|---|---|
| `REVERSE_PORTRAIT` + 800×1280 send of a 1280×800 image | Wrap / split / missing cards |
| Library `PORTRAIT` for “correct red top-left” in diag | Tall buffer → dashboard displayed as portrait |
| `--zoom 1.2` + crop `top-right` after switching to 1280×800 LANDSCAPE | Top and right of the dashboard cut off |
| Fractional `--offset-y` (e.g. 0.5) | Jumped to a clamp (“dead zone”); tiny positive values pinned to the top |
| `--offset-x` while letterbox filled 800px width | No real horizontal move; edges clipped |
| Stretch 1280×800 → 800×1280 | Full screen but distorted; layout still “wide on a tall panel” |

Diag note: `turzx_diag.py` `PORTRAIT` often put the red corner at physical top-left, but that orientation is the **wrong canvas** for a landscape dashboard.

## Positioning rules (if you need to nudge later)

- Use **integer pixel** `--nudge-x` / `--nudge-y` from center, not fractional offsets.
- Keep `--zoom 1.0` unless you accept cropped edges.
- `--fit` below 1.0 shrinks the image and adds margin; it is not required for the working layout.

## Paths

| Piece | Path |
|---|---|
| Dashboard | `~/Documents/dashboard/` |
| Screen defaults | `~/Documents/dashboard/turzx_screen.py` |
| Layout | `~/Documents/dashboard/renderer.py` |
| USB library (patched) | `~/Documents/turing-smart-screen-python/library/lcd/lcd_comm_turing_usb.py` |
| Official config (reference) | `~/Documents/turing-smart-screen-python/config.yaml` — `REVISION: TUR_USB`, theme `8inchTheme2` |
| Boot daemon (user systemd) | `~/.config/systemd/user/turzx-dashboard.service` |

## Boot daemon

User systemd unit `turzx-dashboard.service` starts the dashboard after login (and at boot if lingering is on). It waits on `network-online.target` so the weather card does not race DNS at boot, and conflicts with the old `turing-smart-screen.service` (official `main.py`) because the USB device is exclusive.

```bash
systemctl --user daemon-reload
systemctl --user enable --now turzx-dashboard.service
loginctl enable-linger "$USER"   # start at boot, before login
```

Control:

```bash
systemctl --user status turzx-dashboard.service
systemctl --user restart turzx-dashboard.service
systemctl --user stop turzx-dashboard.service
journalctl --user -u turzx-dashboard.service -f
```

Do not run `python dashboard.py` by hand while the service is active (USB busy).

## Brightness and Caelestia colours

Brightness lives in `~/.config/turzx/config.json` and is picked up within ~1s (no service restart):

```bash
python ~/Documents/dashboard/turzx-ctl.py brightness 40
# or
echo '{"brightness": 40}' > ~/.config/turzx/config.json
```

The dashboard reads `~/.local/state/caelestia/scheme.json` (Caelestia’s current scheme). Wallpaper / `caelestia scheme set` updates that file; the screen follows on the next frame.
