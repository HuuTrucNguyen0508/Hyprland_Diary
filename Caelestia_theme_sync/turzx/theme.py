"""Load Caelestia's current colour scheme from ~/.local/state/caelestia/scheme.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

Rgb = tuple[int, int, int]

CAELESTIA_SCHEME = Path.home() / ".local/state/caelestia/scheme.json"

# Everforest Dark Medium — used if Caelestia scheme is missing
_FALLBACK = {
    "bg": (45, 53, 59),
    "panel": (52, 63, 68),
    "panel_border": (71, 82, 88),
    "bar_track": (61, 72, 77),
    "spark_bg": (35, 42, 46),
    "text": (211, 198, 170),
    "muted": (133, 146, 137),
    "accent": (167, 192, 128),
    "cpu": (127, 187, 179),
    "gpu": (167, 192, 128),
    "ram": (214, 153, 182),
    "disk": (230, 152, 117),
    "net_down": (131, 192, 146),
    "net_up": (219, 188, 127),
}


@dataclass(frozen=True)
class Palette:
    bg: Rgb
    panel: Rgb
    panel_border: Rgb
    bar_track: Rgb
    spark_bg: Rgb
    text: Rgb
    muted: Rgb
    accent: Rgb
    cpu: Rgb
    gpu: Rgb
    ram: Rgb
    disk: Rgb
    net_down: Rgb
    net_up: Rgb
    name: str = "fallback"


def hex_to_rgb(value: str) -> Rgb:
    text = value.strip().lstrip("#")
    if text.startswith("0x"):
        text = text[2:]
    if len(text) != 6:
        raise ValueError(f"bad colour {value!r}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def _pick(colours: dict[str, str], *keys: str, fallback: Rgb) -> Rgb:
    for key in keys:
        raw = colours.get(key)
        if raw:
            try:
                return hex_to_rgb(str(raw))
            except ValueError:
                continue
    return fallback


def palette_from_caelestia(colours: dict[str, str], *, name: str) -> Palette:
    return Palette(
        bg=_pick(colours, "base", "background", "surface", fallback=_FALLBACK["bg"]),
        panel=_pick(colours, "surfaceContainer", "surface0", "surfaceContainerLow", fallback=_FALLBACK["panel"]),
        panel_border=_pick(colours, "outlineVariant", "overlay0", "outline", fallback=_FALLBACK["panel_border"]),
        bar_track=_pick(colours, "surface1", "surface2", "surfaceBright", fallback=_FALLBACK["bar_track"]),
        spark_bg=_pick(colours, "crust", "mantle", "surfaceDim", fallback=_FALLBACK["spark_bg"]),
        text=_pick(colours, "text", "onSurface", "onBackground", fallback=_FALLBACK["text"]),
        muted=_pick(colours, "subtext1", "onSurfaceVariant", "subtext0", fallback=_FALLBACK["muted"]),
        accent=_pick(colours, "primary", "green", fallback=_FALLBACK["accent"]),
        cpu=_pick(colours, "blue", "sapphire", "term4", fallback=_FALLBACK["cpu"]),
        gpu=_pick(colours, "green", "term2", "success", fallback=_FALLBACK["gpu"]),
        ram=_pick(colours, "mauve", "lavender", "pink", fallback=_FALLBACK["ram"]),
        disk=_pick(colours, "peach", "error", "maroon", fallback=_FALLBACK["disk"]),
        net_down=_pick(colours, "teal", "sky", "sapphire", fallback=_FALLBACK["net_down"]),
        net_up=_pick(colours, "yellow", "pink", "tertiary", fallback=_FALLBACK["net_up"]),
        name=name,
    )


def fallback_palette() -> Palette:
    return Palette(name="everforest-fallback", **_FALLBACK)


def load_caelestia_palette(path: Path = CAELESTIA_SCHEME) -> Palette:
    if not path.is_file():
        return fallback_palette()
    data = json.loads(path.read_text(encoding="utf-8"))
    colours = data.get("colours") or data.get("colors") or {}
    if not isinstance(colours, dict) or not colours:
        return fallback_palette()
    name = str(data.get("name") or "caelestia")
    flavour = data.get("flavour")
    mode = data.get("mode")
    label = name if not flavour else f"{name}/{flavour}/{mode or ''}".rstrip("/")
    return palette_from_caelestia({str(k): str(v) for k, v in colours.items()}, name=label)


class SchemeWatcher:
    """Reload palette when Caelestia scheme.json mtime changes."""

    def __init__(self, path: Path = CAELESTIA_SCHEME) -> None:
        self.path = path
        self._mtime: float | None = None
        self.palette = load_caelestia_palette(path)

    def poll(self) -> Palette:
        try:
            mtime = self.path.stat().st_mtime if self.path.is_file() else None
        except OSError:
            mtime = None
        if mtime != self._mtime:
            self._mtime = mtime
            self.palette = load_caelestia_palette(self.path)
        return self.palette
