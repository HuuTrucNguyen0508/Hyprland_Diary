"""TURZX 8\" (1cbe:0080) — send path.

Draw 1280x800 LANDSCAPE. Library rotates 270 before USB so the panel gets 800x1280
(firmware portrait). CONTENT_ROTATE 0 keeps text upright on this mount after that.
"""

from library.lcd.lcd_comm import Orientation

# Panel canvas when using Orientation.LANDSCAPE (matches 1280x800 physical mount)
NATIVE_WIDTH = 1280
NATIVE_HEIGHT = 800

LAYOUT_WIDTH = 1280
LAYOUT_HEIGHT = 800

LCD_ORIENTATION = Orientation.LANDSCAPE
CONTENT_ROTATE = 0
DEFAULT_SCALE = "letterbox"
DEFAULT_ZOOM = 1.0
DEFAULT_FIT = 1.0
DEFAULT_CROP_ANCHOR = "center"

DEFAULT_NUDGE_X = 0
DEFAULT_NUDGE_Y = 0
DEFAULT_CROP_NUDGE_X = 0
DEFAULT_CROP_NUDGE_Y = 0
DEFAULT_BRIGHTNESS = 50
