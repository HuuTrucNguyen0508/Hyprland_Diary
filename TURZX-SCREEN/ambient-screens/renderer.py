"""PIL renderer — TURZX 8\" landscape dashboard (1280x800)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from speedtest_state import SpeedtestState
from stats import DashboardStats, PICTURE_CARD_PATH, VolumeStats
from term_capture import TermFrame, COLS as TERM_COLS, ROWS as TERM_ROWS
from theme import Palette, fallback_palette

WIDTH = 1280
HEIGHT = 800

# Fallback aliases so letterbox / older imports still have a colour
_FALLBACK = fallback_palette()
BG = _FALLBACK.bg
PANEL = _FALLBACK.panel
PANEL_BORDER = _FALLBACK.panel_border
BAR_TRACK = _FALLBACK.bar_track
SPARK_BG = _FALLBACK.spark_bg
TEXT = _FALLBACK.text
MUTED = _FALLBACK.muted
ACCENT = _FALLBACK.accent
CPU_COLOR = _FALLBACK.cpu
GPU_COLOR = _FALLBACK.gpu
RAM_COLOR = _FALLBACK.ram
DISK_COLOR = _FALLBACK.disk
NET_DOWN = _FALLBACK.net_down
NET_UP = _FALLBACK.net_up

MARGIN = 20
MARGIN_LEFT = 20
HEADER_H = 56
GAP = 16


class DashboardRenderer:
    def __init__(self, font_dir: Path, palette: Palette | None = None) -> None:
        self.font_dir = font_dir
        self.palette = palette or fallback_palette()
        self._fonts = self._load_fonts()
        self._picture_path = PICTURE_CARD_PATH
        self._picture_mtime: float | None = None
        self._picture_image: Image.Image | None = None

    def _load_picture(self) -> Image.Image | None:
        path = self._picture_path
        try:
            mtime = path.stat().st_mtime if path.is_file() else None
        except OSError:
            mtime = None
        if mtime != self._picture_mtime:
            self._picture_mtime = mtime
            self._picture_image = None
            if mtime is not None:
                try:
                    image = Image.open(path).convert("RGBA")
                    pixels = image.load()
                    width, height = image.size
                    for py in range(height):
                        for px in range(width):
                            r, g, b, a = pixels[px, py]
                            if a and r < 40 and g < 40 and b < 40:
                                pixels[px, py] = (r, g, b, 0)
                    self._picture_image = image
                except OSError:
                    self._picture_image = None
        return self._picture_image

    def _load_font(self, name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype(str(self.font_dir / name), size)
        except OSError:
            return ImageFont.load_default()

    def _load_fonts(self) -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
        return {
            "title": self._load_font("jetbrains-mono/JetBrainsMono-Bold.ttf", 26),
            "subtitle": self._load_font("roboto/Roboto-Regular.ttf", 20),
            "label": self._load_font("roboto/Roboto-Bold.ttf", 18),
            "device": self._load_font("roboto/Roboto-Bold.ttf", 20),
            "value_lg": self._load_font("jetbrains-mono/JetBrainsMono-Bold.ttf", 48),
            "value_xl": self._load_font("jetbrains-mono/JetBrainsMono-Bold.ttf", 72),
            "value_md": self._load_font("jetbrains-mono/JetBrainsMono-Bold.ttf", 30),
            "value_sm": self._load_font("jetbrains-mono/JetBrainsMono-Regular.ttf", 20),
            "mono_xs": self._load_font("jetbrains-mono/JetBrainsMono-Regular.ttf", 13),
        }

    def render_speedtest(self, state: SpeedtestState) -> Image.Image:
        """Fullscreen dual-gauge view while a speedtest is running or holding."""
        p = self.palette
        image = Image.new("RGB", (WIDTH, HEIGHT), p.bg)
        draw = ImageDraw.Draw(image)

        title = "SPEEDTEST"
        if state.phase == "down":
            subtitle = "DOWNLOAD"
        elif state.phase == "up":
            subtitle = "UPLOAD"
        elif state.error:
            subtitle = "FAILED"
        elif state.active:
            subtitle = "RUNNING"
        else:
            subtitle = "DONE"

        draw.text((WIDTH // 2, 48), title, font=self._fonts["title"], fill=p.muted, anchor="mt")
        draw.text((WIDTH // 2, 88), subtitle, font=self._fonts["label"], fill=p.accent, anchor="mt")

        gauge_r = 160
        gap = 120
        cy = HEIGHT // 2 + 20
        left_cx = WIDTH // 2 - gap // 2 - gauge_r
        right_cx = WIDTH // 2 + gap // 2 + gauge_r
        scale = self._speedtest_scale(state.download_mbps, state.upload_mbps)

        self._draw_speed_gauge(
            draw,
            cx=left_cx,
            cy=cy,
            radius=gauge_r,
            value=state.download_mbps,
            label="DOWNLOAD",
            color=p.net_down,
            live=state.phase == "down",
            scale=scale,
        )
        self._draw_speed_gauge(
            draw,
            cx=right_cx,
            cy=cy,
            radius=gauge_r,
            value=state.upload_mbps,
            label="UPLOAD",
            color=p.net_up,
            live=state.phase == "up",
            scale=scale,
        )

        if state.error:
            draw.text(
                (WIDTH // 2, HEIGHT - 56),
                state.error[:80],
                font=self._fonts["value_sm"],
                fill=p.disk,
                anchor="mt",
            )

        return image

    def render_terminal(self, frame: TermFrame) -> Image.Image:
        """Fullscreen colour terminal grid stretched to the panel."""
        p = self.palette
        image = Image.new("RGB", (WIDTH, HEIGHT), p.bg)
        draw = ImageDraw.Draw(image)

        if not frame.rows:
            label = frame.label or "ambient"
            draw.text(
                (WIDTH // 2, HEIGHT // 2),
                f"Starting {label}…",
                font=self._fonts["value_sm"],
                fill=p.muted,
                anchor="mm",
            )
            return image

        cols = frame.cols or TERM_COLS
        grid_rows = frame.grid_rows or TERM_ROWS
        cell_w = WIDTH // cols
        cell_h = HEIGHT // grid_rows
        font_size = max(6, min(cell_w - 1, cell_h - 2))
        font = self._load_font("jetbrains-mono/JetBrainsMono-Regular.ttf", font_size)

        for row_idx, row in enumerate(frame.rows[:grid_rows]):
            y0 = row_idx * cell_h
            y1 = y0 + cell_h
            if y0 >= HEIGHT:
                break
            for col_idx, cell in enumerate(row[:cols]):
                x0 = col_idx * cell_w
                x1 = x0 + cell_w
                if x0 >= WIDTH:
                    break
                bg = cell.bg
                draw.rectangle((x0, y0, x1, y1), fill=bg)
                if cell.ch == " ":
                    continue
                ch_w = font.getlength(cell.ch)
                tx = x0 + max(0, (cell_w - ch_w) / 2)
                ty = y0 + max(0, (cell_h - font_size) / 2) - 1
                draw.text((tx, ty), cell.ch, font=font, fill=cell.fg)

        return image

    @staticmethod
    def _speedtest_scale(down: float, up: float) -> float:
        peak = max(down, up, 1.0)
        for stop in (100, 250, 500, 1000, 2500, 5000, 10000):
            if peak <= stop * 0.92:
                return float(stop)
        return 10000.0

    @staticmethod
    def _format_mbps(value: float) -> str:
        if value < 10:
            return f"{value:.1f}"
        return f"{value:.0f}"

    def _draw_speed_gauge(
        self,
        draw: ImageDraw.ImageDraw,
        *,
        cx: int,
        cy: int,
        radius: int,
        value: float,
        label: str,
        color: tuple[int, int, int],
        live: bool,
        scale: float,
    ) -> None:
        p = self.palette
        track = p.bar_track
        # Open 270° arc with gap at bottom (PIL angles: 0=3 o'clock, CCW)
        start = 135
        end = 135 + 270
        bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
        width = 10
        draw.arc(bbox, start=start, end=end, fill=track, width=width)

        fraction = 0.0 if scale <= 0 else max(0.0, min(1.0, value / scale))
        if fraction > 0.004:
            draw.arc(bbox, start=start, end=start + 270 * fraction, fill=color, width=width)

        # Tick marks (PIL angles: 0 = east, CCW)
        for i in range(46):
            deg = start + 270 * (i / 45)
            major = i % 5 == 0
            inner = radius - (22 if major else 14)
            outer = radius - 8
            rad = math.radians(deg)
            x0 = cx + inner * math.cos(rad)
            y0 = cy + inner * math.sin(rad)
            x1 = cx + outer * math.cos(rad)
            y1 = cy + outer * math.sin(rad)
            tick_color = p.muted if major else p.panel_border
            draw.line((x0, y0, x1, y1), fill=tick_color, width=2 if major else 1)

        # Needle
        needle_deg = start + 270 * fraction
        needle_len = radius * 0.72
        nx = cx + needle_len * math.cos(math.radians(needle_deg))
        ny = cy + needle_len * math.sin(math.radians(needle_deg))
        draw.line((cx, cy, nx, ny), fill=color if (live or value > 0) else p.muted, width=3)
        draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=color if (live or value > 0) else p.muted)

        reading = self._format_mbps(value)
        draw.text((cx, cy + 36), reading, font=self._fonts["value_xl"], fill=p.text, anchor="mt")
        draw.text((cx, cy + 110), "Mbps", font=self._fonts["value_sm"], fill=p.muted, anchor="mt")
        draw.text((cx, cy + radius + 28), label, font=self._fonts["label"], fill=p.muted, anchor="mt")

    def render(self, stats: DashboardStats) -> Image.Image:
        p = self.palette
        image = Image.new("RGB", (WIDTH, HEIGHT), p.bg)
        draw = ImageDraw.Draw(image)

        top = MARGIN
        self._draw_header(draw, stats, y=top)

        # One shared metrics plate (CPU/GPU/RAM/picture). Separate cards used to share a
        # bottom edge that H.264 turned into a full-width bar through the sparklines.
        strip_top = top + HEADER_H + GAP
        strip_h = 300
        strip_left = MARGIN_LEFT
        strip_right = WIDTH - MARGIN
        self._rounded_rect(
            draw,
            (strip_left, strip_top, strip_right, strip_top + strip_h),
            14,
            p.panel,
            p.panel_border,
        )

        cells = 4
        strip_w = strip_right - strip_left
        cell_w = strip_w // cells
        metrics = [
            ("CPU", stats.cpu_name, p.cpu, stats.cpu_percent, self._cpu_detail(stats), stats.cpu_history),
            ("GPU", stats.gpu_name, p.gpu, stats.gpu_percent, self._gpu_detail(stats), stats.gpu_history),
            ("RAM", stats.ram_name, p.ram, stats.ram_percent, f"{stats.ram_used_gb:.1f} / {stats.ram_total_gb:.0f} GB", stats.ram_history),
        ]
        for i, (title, device, color, pct, detail, history) in enumerate(metrics):
            x = strip_left + i * cell_w
            self._draw_metric_cell(
                draw,
                x=x,
                y=strip_top,
                w=cell_w,
                h=strip_h,
                title=title,
                device=device,
                color=color,
                percent=pct,
                detail=detail,
                history=history,
            )
        self._draw_picture_cell(
            draw,
            x=strip_left + 3 * cell_w,
            y=strip_top,
            w=strip_right - (strip_left + 3 * cell_w),
            h=strip_h,
        )
        for i in range(1, cells):
            x = strip_left + i * cell_w
            draw.line(
                (x, strip_top + 14, x, strip_top + strip_h - 14),
                fill=p.panel_border,
                width=1,
            )

        panels_top = strip_top + strip_h + GAP
        panels_h = HEIGHT - panels_top - MARGIN
        panel_w = (WIDTH - MARGIN_LEFT - MARGIN - GAP * 2) // 3

        self._draw_storage_panel(draw, stats, x=MARGIN_LEFT, y=panels_top, w=panel_w, h=panels_h)
        self._draw_bonsai_panel(draw, stats, x=MARGIN_LEFT + panel_w + GAP, y=panels_top, w=panel_w, h=panels_h)
        self._draw_weather_panel(draw, stats, x=MARGIN_LEFT + 2 * (panel_w + GAP), y=panels_top, w=panel_w, h=panels_h)
        return image

    def _rounded_rect(self, draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int],
                      radius: int, fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None) -> None:
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=1)

    def _draw_header(self, draw: ImageDraw.ImageDraw, stats: DashboardStats, *, y: int) -> None:
        p = self.palette
        self._rounded_rect(draw, (MARGIN_LEFT, y, WIDTH - MARGIN, y + HEADER_H), 12, p.panel, p.panel_border)
        draw.text((MARGIN_LEFT + 16, y + 14), "The Aden Kingof", font=self._fonts["title"], fill=p.accent)
        draw.text((WIDTH - MARGIN - 16, y + 16), stats.clock, font=self._fonts["subtitle"], fill=p.text, anchor="ra")

    def _draw_metric_cell(
        self,
        draw: ImageDraw.ImageDraw,
        *,
        x: int,
        y: int,
        w: int,
        h: int,
        title: str,
        device: str,
        color: tuple[int, int, int],
        percent: float | None,
        detail: str,
        history: list[float],
    ) -> None:
        """Metric block inside the shared top plate (no own outer border)."""
        p = self.palette
        draw.text((x + 14, y + 10), title, font=self._fonts["label"], fill=color)
        if device:
            draw.text((x + w - 14, y + 10), device, font=self._fonts["device"], fill=color, anchor="ra")

        value_text = "N/A" if percent is None else f"{percent:.0f}%"
        bar_value = 0 if percent is None else int(percent)
        draw.text((x + 14, y + 40), value_text, font=self._fonts["value_lg"], fill=p.text)
        draw.text((x + 14, y + 96), detail, font=self._fonts["value_sm"], fill=p.muted)

        bar_x, bar_w = x + 14, w - 28
        bar_y = y + 132
        self._rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + 10), 5, p.bar_track)
        fill_w = max(0, int(bar_w * bar_value / 100))
        if fill_w:
            self._rounded_rect(draw, (bar_x, bar_y, bar_x + fill_w, bar_y + 10), 5, color)

        if history:
            # Leave padding above the shared plate bottom so content never sits on the edge.
            self._draw_sparkline(draw, x=bar_x, y=bar_y + 18, w=bar_w, h=h - 168, values=history, color=color)

    def _draw_picture_cell(self, draw: ImageDraw.ImageDraw, *, x: int, y: int, w: int, h: int) -> None:
        """Logo/picture inside the shared top plate (no own outer border)."""
        p = self.palette
        inset = 12
        inner_x, inner_y = x + inset, y + inset
        inner_w, inner_h = w - inset * 2, h - inset * 2
        picture = self._load_picture()
        if picture is None:
            draw.text((x + 14, y + 14), "PICTURE", font=self._fonts["label"], fill=p.text)
            draw.text((x + 14, y + 48), "4.png missing", font=self._fonts["value_sm"], fill=p.muted)
            return
        src_w, src_h = picture.size
        scale = min(inner_w / src_w, inner_h / src_h)
        fit_w = max(1, round(src_w * scale))
        fit_h = max(1, round(src_h * scale))
        resized = picture.resize((fit_w, fit_h), Image.Resampling.LANCZOS)
        paste_x = inner_x + (inner_w - fit_w) // 2
        paste_y = inner_y + (inner_h - fit_h) // 2
        draw._image.paste(resized, (paste_x, paste_y), resized)

    def _draw_storage_panel(self, draw: ImageDraw.ImageDraw, stats: DashboardStats,
                            *, x: int, y: int, w: int, h: int) -> None:
        p = self.palette
        self._rounded_rect(draw, (x, y, x + w, y + h), 14, p.panel, p.panel_border)
        draw.text((x + 14, y + 10), "STORAGE", font=self._fonts["label"], fill=p.text)
        volumes = [stats.ssd, stats.nvme, stats.hdd]
        row_y = y + 46
        step = max(56, (h - 54) // len(volumes))
        for volume in volumes:
            self._draw_volume_row(draw, volume, x=x + 14, y=row_y, w=w - 28, color=p.disk)
            row_y += step

    def _draw_volume_row(
        self,
        draw: ImageDraw.ImageDraw,
        volume: VolumeStats,
        *,
        x: int,
        y: int,
        w: int,
        color: tuple[int, int, int],
    ) -> None:
        p = self.palette
        draw.text((x, y), volume.label, font=self._fonts["value_sm"], fill=color)
        if volume.name:
            draw.text((x + w, y), volume.name, font=self._fonts["device"], fill=p.muted, anchor="ra")
        if not volume.mounted:
            draw.text((x, y + 24), "Not mounted", font=self._fonts["value_sm"], fill=p.muted)
            return
        detail = f"{volume.used_gb:.0f} / {volume.total_gb:.0f} GB"
        pct_text = f"{volume.percent:.0f}%"
        draw.text((x, y + 24), detail, font=self._fonts["value_sm"], fill=p.muted)
        draw.text((x + w, y + 24), pct_text, font=self._fonts["value_sm"], fill=p.text, anchor="ra")
        bar_y = y + 48
        self._rounded_rect(draw, (x, bar_y, x + w, bar_y + 8), 4, p.bar_track)
        fill_w = max(0, int(w * volume.percent / 100))
        if fill_w:
            self._rounded_rect(draw, (x, bar_y, x + fill_w, bar_y + 8), 4, color)

    def _draw_bonsai_panel(self, draw: ImageDraw.ImageDraw, stats: DashboardStats,
                           *, x: int, y: int, w: int, h: int) -> None:
        p = self.palette
        self._rounded_rect(draw, (x, y, x + w, y + h), 14, p.panel, p.panel_border)
        draw.text((x + 14, y + 10), "BONSAI", font=self._fonts["label"], fill=p.text)
        art_top = y + 38
        art_h = h - 48
        if not stats.bonsai_lines:
            draw.text((x + 14, art_top + 8), "rbonsai -li", font=self._fonts["value_sm"], fill=p.muted)
            draw.text((x + 14, art_top + 34), "Starting…", font=self._fonts["value_sm"], fill=p.muted)
            return
        font = self._fonts["mono_xs"]
        line_h = 14
        max_lines = max(1, art_h // line_h)
        lines = stats.bonsai_lines[-max_lines:]
        block_h = len(lines) * line_h
        start_y = art_top + art_h - block_h
        clip_cols = max(8, w // 8)
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            clipped = line[-clip_cols:]
            draw.text((x + 14, start_y + i * line_h), clipped, font=font, fill=p.accent)

    def _draw_sparkline(self, draw: ImageDraw.ImageDraw, *, x: int, y: int, w: int, h: int,
                        values: list[float], color: tuple[int, int, int]) -> None:
        if len(values) < 2 or h < 16:
            return
        self._rounded_rect(draw, (x, y, x + w, y + h), 8, self.palette.spark_bg)
        step = w / max(len(values) - 1, 1)
        points = [
            (x + int(i * step), y + h - int((v / 100.0) * (h - 6)) - 3)
            for i, v in enumerate(values)
        ]
        draw.line(points, fill=color, width=2, joint="curve")

    def _draw_weather_panel(self, draw: ImageDraw.ImageDraw, stats: DashboardStats,
                            *, x: int, y: int, w: int, h: int) -> None:
        p = self.palette
        self._rounded_rect(draw, (x, y, x + w, y + h), 14, p.panel, p.panel_border)
        draw.text((x + 14, y + 10), "WEATHER", font=self._fonts["label"], fill=p.text)

        place = stats.weather_city
        if stats.weather_country:
            place = f"{stats.weather_city}, {stats.weather_country}" if stats.weather_city else stats.weather_country
        if place:
            draw.text((x + w - 14, y + 10), place, font=self._fonts["device"], fill=p.accent, anchor="ra")

        if stats.weather_error:
            draw.text((x + 14, y + 56), "—", font=self._fonts["value_lg"], fill=p.muted)
            draw.text((x + 14, y + 112), stats.weather_error, font=self._fonts["value_sm"], fill=p.muted)
            return

        if stats.weather_icon:
            icon_size = 52
            icon_cx = x + w - 14 - icon_size // 2
            icon_cy = y + 44 + icon_size // 2
            self._draw_weather_icon(
                draw, stats.weather_icon, cx=icon_cx, cy=icon_cy, size=icon_size, color=p.accent, muted=p.muted,
            )

        if stats.weather_temp_c is not None:
            draw.text((x + 14, y + 44), f"{stats.weather_temp_c:.0f}°C", font=self._fonts["value_lg"], fill=p.text)
        else:
            draw.text((x + 14, y + 44), "N/A", font=self._fonts["value_lg"], fill=p.muted)

        if stats.weather_description:
            draw.text((x + 14, y + 104), stats.weather_description, font=self._fonts["value_sm"], fill=p.muted)

        rows = [
            ("Feels like", f"{stats.weather_feels_like_c:.0f}°C" if stats.weather_feels_like_c is not None else "N/A"),
            ("Humidity", f"{stats.weather_humidity}%" if stats.weather_humidity is not None else "N/A"),
            ("Wind", f"{stats.weather_wind_kmh:.0f} km/h" if stats.weather_wind_kmh is not None else "N/A"),
        ]
        row_y = y + 140
        step = max(30, (h - 150) // len(rows))
        for label, value in rows:
            draw.text((x + 14, row_y), label, font=self._fonts["value_sm"], fill=p.muted)
            draw.text((x + w - 14, row_y), value, font=self._fonts["value_sm"], fill=p.text, anchor="ra")
            row_y += step

    def _draw_weather_icon(
        self,
        draw: ImageDraw.ImageDraw,
        icon: str,
        *,
        cx: int,
        cy: int,
        size: int,
        color: tuple[int, int, int],
        muted: tuple[int, int, int],
    ) -> None:
        """Vector weather pictogram — bundled fonts lack emoji/weather glyphs."""
        family = icon[:2] if len(icon) >= 2 else "01"
        is_day = icon.endswith("d")

        def cloud(left: int, top: int, width: int, height: int, fill: tuple[int, int, int]) -> None:
            puff_w = width // 2
            puff_h = max(height // 2, 8)
            draw.ellipse((left, top + height // 3, left + puff_w, top + height // 3 + puff_h), fill=fill)
            draw.ellipse(
                (left + width // 4, top, left + width // 4 + puff_w, top + puff_h + height // 5),
                fill=fill,
            )
            draw.ellipse(
                (left + width // 2, top + height // 5, left + width // 2 + puff_w, top + height // 5 + puff_h),
                fill=fill,
            )
            draw.rectangle((left + width // 8, top + height // 2, left + width, top + height), fill=fill)

        def sun(center_x: int, center_y: int, radius: int, fill: tuple[int, int, int]) -> None:
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                fill=fill,
            )
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                inner = radius + 3
                outer = radius + 9
                x1 = center_x + int(math.cos(rad) * inner)
                y1 = center_y + int(math.sin(rad) * inner)
                x2 = center_x + int(math.cos(rad) * outer)
                y2 = center_y + int(math.sin(rad) * outer)
                draw.line((x1, y1, x2, y2), fill=fill, width=2)

        def moon(center_x: int, center_y: int, radius: int, fill: tuple[int, int, int]) -> None:
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                fill=fill,
            )
            offset = max(radius // 2, 6)
            draw.ellipse(
                (
                    center_x - radius + offset,
                    center_y - radius - 2,
                    center_x + radius + offset,
                    center_y + radius - 2,
                ),
                fill=self.palette.panel,
            )

        def rain_lines(left: int, top: int, width: int, count: int, fill: tuple[int, int, int]) -> None:
            step = max(width // max(count, 1), 6)
            for i in range(count):
                rx = left + 6 + i * step
                draw.line((rx, top, rx - 3, top + 10), fill=fill, width=2)

        def lightning(left: int, top: int, fill: tuple[int, int, int]) -> None:
            draw.polygon(
                [(left + 8, top), (left + 2, top + 12), (left + 9, top + 12), (left + 4, top + 24), (left + 16, top + 10), (left + 9, top + 10)],
                fill=fill,
            )

        def snowflake(center_x: int, center_y: int, radius: int, fill: tuple[int, int, int]) -> None:
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                x2 = center_x + int(math.cos(rad) * radius)
                y2 = center_y + int(math.sin(rad) * radius)
                draw.line((center_x, center_y, x2, y2), fill=fill, width=2)

        half = size // 2
        left = cx - half
        top = cy - half

        if family == "01":
            if is_day:
                sun(cx, cy, half // 2, color)
            else:
                moon(cx, cy, half // 2, color)
            return

        if family == "02":
            if is_day:
                sun(cx - half // 3, cy - half // 4, half // 4, color)
            cloud(left, top + half // 5, size - 4, half, muted)
            return

        if family in {"03", "04"}:
            cloud(left, top + half // 6, size - 4, half + 4, muted)
            return

        if family in {"09", "10"}:
            cloud(left, top, size - 4, half, muted)
            rain_lines(left + 4, top + half + 2, size - 8, 4, color)
            if family == "10" and is_day:
                sun(cx + half // 4, cy - half // 3, half // 5, color)
            return

        if family == "11":
            cloud(left, top, size - 8, half, muted)
            lightning(left + half // 2, top + half // 2, color)
            return

        if family == "13":
            snowflake(cx, cy, half // 2, color)
            return

        if family == "50":
            for i in range(3):
                y = top + 10 + i * 12
                draw.line((left + 6, y, left + size - 6, y), fill=muted, width=2)
            return

        cloud(left, top + half // 6, size - 4, half + 4, muted)

    def _stat_line(self, draw: ImageDraw.ImageDraw, x: int, y: int, label: str, value: str,
                   color: tuple[int, int, int], panel_w: int) -> None:
        draw.text((x, y), label, font=self._fonts["value_sm"], fill=self.palette.muted)
        draw.text((x, y + 24), value, font=self._fonts["value_md"], fill=color)

    @staticmethod
    def _cpu_detail(stats: DashboardStats) -> str:
        parts = []
        if stats.cpu_temp is not None:
            parts.append(f"{stats.cpu_temp:.0f}°C")
        if stats.cpu_freq_mhz is not None:
            parts.append(f"{stats.cpu_freq_mhz:.0f} MHz")
        return "  ·  ".join(parts) if parts else "—"

    @staticmethod
    def _gpu_detail(stats: DashboardStats) -> str:
        if stats.gpu_vram_used_mb is None or stats.gpu_vram_total_mb is None:
            return f"{stats.gpu_temp:.0f}°C" if stats.gpu_temp is not None else "No data"
        return f"{stats.gpu_vram_used_mb / 1024:.1f} / {stats.gpu_vram_total_mb / 1024:.0f} GB VRAM"

    @staticmethod
    def _format_speed(kbps: float) -> str:
        return f"{kbps / 1024:.1f} MB/s" if kbps >= 1024 else f"{kbps:.0f} KB/s"

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        days, rem = divmod(int(seconds), 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        if days:
            return f"{days}d {hours}h {minutes}m"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
