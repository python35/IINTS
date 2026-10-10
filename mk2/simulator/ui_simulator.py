#!/usr/bin/env python3
"""Desktop simulator for the IINTS 240x240 MicroPython interface.

The simulator executes the drawing functions from the real pump source with
small host-side replacements for machine, framebuf, utime, and ST7789. It never
connects to the Pico and cannot drive the motor.
"""

from __future__ import annotations

import argparse
import base64
import math
import os
import sys
import time
import types
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk


APP_DIR = Path(__file__).resolve().parent
DEFAULT_FIRMWARE = APP_DIR.parent / "firmware" / "pico_drv8833_correct_pins.py"
WIDTH = 240
HEIGHT = 240

SCREENS = (
    "Home (current mode)",
    "CGM home",
    "Buddy home",
    "Calm pause",
    "Glucose entry",
    "Carb entry",
    "Mood selection",
    "Meal portions",
    "Dose review",
    "Buddy review",
    "Delivering",
    "Dose complete",
    "CGM graph",
    "Settings menu",
    "Button guide",
    "Edit setting",
    "Rewind",
    "Locked",
    "Sleep",
    "Status",
    "Demo image",
)

DEFAULT_STATE = {
    "glucose": 120,
    "trend": 0,
    "age": 0,
    "carbs": 45,
    "dose": 5.1,
    "iob": 1.2,
    "cob": 18,
    "portion": 3,
    "emotion": "happy",
    "neuro": True,
    "hold": 65,
    "frame": 3,
    "setting": 0,
    "rewind_running": False,
}


FRAMEBUFFER_COLORS_SWAPPED = False


def raw_rgb565_to_rgb(value: int) -> tuple[int, int, int]:
    value = int(value) & 0xFFFF
    return (
        ((value >> 11) & 0x1F) * 255 // 31,
        ((value >> 5) & 0x3F) * 255 // 63,
        (value & 0x1F) * 255 // 31,
    )


def framebuffer_color_to_rgb(value: int) -> tuple[int, int, int]:
    value = int(value) & 0xFFFF
    if FRAMEBUFFER_COLORS_SWAPPED:
        value = ((value & 0xFF) << 8) | (value >> 8)
    return raw_rgb565_to_rgb(value)


def load_pixel_font() -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "DejaVuSansMono.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, 8)
        except OSError:
            continue
    return ImageFont.load_default()


PIXEL_FONT = load_pixel_font()

# Exact font bytes used by MicroPython's framebuf.text implementation.
# Source: extmod/font_petme128_8x8.h (MicroPython, MIT License).
MICROPYTHON_FONT_8X8 = base64.b64decode(
    "AAAAAAAAAAAAAABPTwAAAAAHBwAABwcAFH9/FBR/fxQAJC5razoSAABjMxgMZmMAADJ/TU13clAAAAAEBgMBAAAA"
    "HD5jQQAAAABBYz4cAAAIKj4cHD4qCAAICD4+CAgAAACA4GAAAAAACAgICAgIAAAAAGBgAAAAAEBgMBgMBgIAPn9J"
    "RX8+AABARH9/QEAAAGJzUUlPRgAAImNJSX82AAAYGBQWf38QACdnRUV9OQAAPn9JSXsyAAADA3l9BwMAADZ/SUl/"
    "NgAAJm9JSX8+AAAAACQkAAAAAACA5GQAAAAACBw2Y0FBAAAUFBQUFBQAAEFBYzYcCAAAAgNRWQ8GAAA+f0FNTy4A"
    "AHx+Cwt+fAAAf39JSX82AAA+f0FBYyIAAH9/QWM+HAAAf39JSUFBAAB/fwkJAQEAAD5/QUl7OgAAf38ICH9/AAAA"
    "QX9/QQAAACBgQX8/AQAAf38cNmNBAAB/f0BAQEAAAH9/BgwGf38Af38OHH9/AAA+f0FBfz4AAH9/CQkPBgAAHj8h"
    "YX9eAAB/fxk5b0YAACZvSUl7MgAAAQF/fwEBAAA/f0BAfz8AAB8/YGA/HwAAf38wGDB/fwBjdxwcd2MAAAcPeHgP"
    "BwAAYXFZTUdDAAAAf39BQQAAAAIGDBgwYEAAAEFBf38AAAAIDAYGDAgAwMDAwMDAwMAAAAEDBgQAAAAgdFRUfHgA"
    "AH9/RER8OAAAOHxERGwoAAA4fEREf38AADh8VFRcWAAACH5/CQMCAACYvKSk/HwAAH9/BAR8eAAAAAB9fQAAAABA"
    "wICA/X0AAH9/MDhsRAAAAEF/f0AAAAB8fBgwGHx8AHx8BAR8eAAAOHxERHw4AAD8/CQkPBgAABg8JCT8/AAAfHwE"
    "BAwIAABIXFRUdCAABAQ/f0RkIAAAPHxAQHw8AAAcPGBgPBwAABx8MBgwfBwARGw4OGxEAACcvKCg/HwAAERkdFxM"
    "RAAACAg+d0FBAAAAAP//AAAAAEFBdz4ICAAAAgMBAwIDAapVqlWqVapV"
)


class PillowFrameBuffer:
    """Subset of MicroPython framebuf backed by a Pillow RGB image."""

    def __init__(self, _buffer, width: int, height: int, _format):
        self.width = int(width)
        self.height = int(height)
        self.image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self._draw = ImageDraw.Draw(self.image)
        self._draw.fontmode = "1"

    def fill(self, color):
        self._draw.rectangle(
            (0, 0, self.width - 1, self.height - 1),
            fill=framebuffer_color_to_rgb(color),
        )

    def fill_rect(self, x, y, width, height, color):
        if width <= 0 or height <= 0:
            return
        self._draw.rectangle(
            (x, y, x + width - 1, y + height - 1),
            fill=framebuffer_color_to_rgb(color),
        )

    def hline(self, x, y, width, color):
        if width > 0:
            self._draw.line((x, y, x + width - 1, y), fill=framebuffer_color_to_rgb(color))

    def vline(self, x, y, height, color):
        if height > 0:
            self._draw.line((x, y, x, y + height - 1), fill=framebuffer_color_to_rgb(color))

    def line(self, x1, y1, x2, y2, color):
        self._draw.line((x1, y1, x2, y2), fill=framebuffer_color_to_rgb(color))

    def rect(self, x, y, width, height, color):
        if width <= 0 or height <= 0:
            return
        self._draw.rectangle(
            (x, y, x + width - 1, y + height - 1),
            outline=framebuffer_color_to_rgb(color),
        )

    def text(self, text, x, y, color):
        draw_color = framebuffer_color_to_rgb(color)
        cursor_x = int(x)
        y = int(y)
        for char in str(text):
            codepoint = ord(char)
            if codepoint < 32 or codepoint > 127:
                codepoint = 127
            offset = (codepoint - 32) * 8
            for column in range(8):
                pixel_x = cursor_x + column
                if pixel_x < 0 or pixel_x >= self.width:
                    continue
                column_bits = MICROPYTHON_FONT_8X8[offset + column]
                for row in range(8):
                    pixel_y = y + row
                    if column_bits & (1 << row) and 0 <= pixel_y < self.height:
                        self.image.putpixel((pixel_x, pixel_y), draw_color)
            cursor_x += 8

    def pixel(self, x, y, color=None):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return 0
        if color is None:
            red, green, blue = self.image.getpixel((x, y))
            return (red << 16) | (green << 8) | blue
        self.image.putpixel((x, y), framebuffer_color_to_rgb(color))
        return None


class FakePin:
    OUT = 1
    IN = 0
    PULL_UP = 2

    def __init__(self, _pin, mode=None, _pull=None):
        self._value = 1 if mode == self.IN else 0

    def value(self, new_value=None):
        if new_value is not None:
            self._value = int(new_value)
        return self._value


class FakeSPI:
    def __init__(self, *_args, **_kwargs):
        pass


class FakeDisplay:
    def __init__(self, *_args, **_kwargs):
        pass

    def init(self):
        pass

    def blit_buffer(self, *_args, **_kwargs):
        pass

    def _command(self, *_args, **_kwargs):
        pass


def install_fake_modules() -> None:
    machine = types.ModuleType("machine")
    machine.Pin = FakePin
    machine.SPI = FakeSPI
    machine.lightsleep = lambda *_args, **_kwargs: None
    sys.modules["machine"] = machine

    utime = types.ModuleType("utime")
    utime.ticks_ms = lambda: int(time.monotonic() * 1000)
    utime.ticks_diff = lambda current, previous: current - previous
    utime.sleep_ms = lambda _milliseconds: None
    utime.sleep = lambda _seconds: None
    utime.time = lambda: int(time.time())
    sys.modules["utime"] = utime

    framebuf = types.ModuleType("framebuf")
    framebuf.RGB565 = 1
    framebuf.FrameBuffer = PillowFrameBuffer
    sys.modules["framebuf"] = framebuf

    st7789 = types.ModuleType("st7789")
    st7789.ST7789 = FakeDisplay
    sys.modules["st7789"] = st7789


class FirmwareRuntime:
    def __init__(self, source_path: Path):
        self.source_path = Path(source_path).resolve()
        self.root = self.source_path.parent
        self.ns: dict[str, object] = {}
        self._image_cache: dict[tuple[Path, int, int, float], Image.Image] = {}
        self.load()

    @property
    def framebuffer(self) -> PillowFrameBuffer:
        return self.ns["fb"]  # type: ignore[return-value]

    def load(self) -> None:
        global FRAMEBUFFER_COLORS_SWAPPED
        install_fake_modules()
        source = self.source_path.read_text(encoding="utf-8")
        marker = "# --- Hoofdprogramma ---"
        if marker not in source:
            raise RuntimeError("The firmware main-loop marker was not found.")

        prefix = source.split(marker, 1)[0]
        namespace = {
            "__name__": "iints_ui_preview",
            "__file__": str(self.source_path),
        }
        old_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            exec(compile(prefix, str(self.source_path), "exec"), namespace)
        finally:
            os.chdir(old_cwd)

        self.ns = namespace
        FRAMEBUFFER_COLORS_SWAPPED = namespace["rgb565"](255, 0, 0) == 0x00F8
        self.ns["flush"] = lambda: None
        self.ns["draw_raw_image"] = self.draw_raw_image
        self._image_cache.clear()

    def resolve_asset(self, filename: str) -> Path | None:
        name = Path(filename).name
        candidates = (
            self.root / filename,
            self.root / name,
            self.root / "Bluey" / name,
            self.root / "deploy" / name,
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def load_raw_rgb565(self, path: Path, width: int, height: int) -> Image.Image:
        modified = path.stat().st_mtime
        key = (path, width, height, modified)
        cached = self._image_cache.get(key)
        if cached is not None:
            return cached.copy()

        data = path.read_bytes()
        expected = width * height * 2
        if len(data) < expected:
            raise ValueError(f"{path.name} is {len(data)} bytes; expected {expected}.")

        pixels = []
        for offset in range(0, expected, 2):
            value = (data[offset] << 8) | data[offset + 1]
            pixels.append(raw_rgb565_to_rgb(value))
        image = Image.new("RGB", (width, height))
        image.putdata(pixels)
        self._image_cache[key] = image
        return image.copy()

    @staticmethod
    def _paste_clipped(target: Image.Image, source: Image.Image, x: int, y: int) -> None:
        left = max(0, -x)
        top = max(0, -y)
        right = min(source.width, target.width - x)
        bottom = min(source.height, target.height - y)
        if right <= left or bottom <= top:
            return
        target.paste(source.crop((left, top, right, bottom)), (x + left, y + top))

    def draw_raw_image(
        self,
        filename,
        x,
        y,
        width,
        height,
        mask_radius=None,
        bg_color=None,
    ) -> bool:
        path = self.resolve_asset(str(filename))
        if path is None:
            return False
        try:
            image = self.load_raw_rgb565(path, int(width), int(height))
        except (OSError, ValueError):
            return False

        if bg_color is None:
            bg_color = self.ns.get("COLOR_BG", 0)
        if mask_radius is not None:
            composed = Image.new(
                "RGB",
                (int(width), int(height)),
                framebuffer_color_to_rgb(int(bg_color)),
            )
            mask = Image.new("L", (int(width), int(height)), 0)
            mask_draw = ImageDraw.Draw(mask)
            center_x = int(width) // 2
            center_y = int(height) // 2
            radius = int(mask_radius)
            mask_draw.ellipse(
                (
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                ),
                fill=255,
            )
            composed.paste(image, (0, 0), mask)
            image = composed

        self._paste_clipped(self.framebuffer.image, image, int(x), int(y))
        return True

    def draw_demo_image(self) -> None:
        path = self.resolve_asset("start.raw")
        if path is None:
            self.ns["draw_demo_fallback"]()
            return
        image = self.load_raw_rgb565(path, WIDTH, HEIGHT)
        self.framebuffer.image.paste(image, (0, 0))


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def apply_state(runtime: FirmwareRuntime, state: dict) -> None:
    ns = runtime.ns
    now_ticks = ns["utime"].ticks_ms()
    now_time = ns["utime"].time()
    glucose = int(state["glucose"])
    trend = int(state["trend"])

    ns["huidige_bg"] = glucose
    ns["gram_koolhydraten"] = int(state["carbs"])
    ns["cgm_trend"] = trend
    ns["cgm_last_update_ms"] = now_ticks - int(state["age"]) * 60000
    ns["TAMAGOTCHI_MODE"] = 1 if state["neuro"] else 0
    ns["tamagotchi_food_index"] = int(state["portion"])

    iob = max(0.0, float(state["iob"]))
    cob = max(0, int(state["cob"]))
    ns["injection_log"] = [(now_time, iob)] if iob else []
    ns["carb_log"] = [
        (now_time, cob, ns["STANDARD_CARB_ABSORPTION_SECONDS"])
    ] if cob else []

    direction = 1 if trend > 0 else -1 if trend < 0 else 0
    history = []
    for index in range(12):
        distance = 11 - index
        wobble = (index % 3) * 2 - 2
        history.append(clamp(glucose - direction * distance * 4 + wobble, 40, 400))
    history[-1] = glucose
    ns["cgm_history"] = history


def mood_for_glucose(runtime: FirmwareRuntime, glucose: int) -> str:
    if glucose < 70:
        return "sad"
    if glucose > 140:
        return "dizzy"
    return "happy"


def render_screen(
    runtime: FirmwareRuntime,
    screen: str,
    state: dict,
) -> tuple[Image.Image, tuple[str, str, str]]:
    apply_state(runtime, state)
    ns = runtime.ns
    glucose = int(state["glucose"])
    trend = int(state["trend"])
    carbs = int(state["carbs"])
    dose = float(state["dose"])
    portion = clamp(int(state["portion"]), 0, len(ns["PORTION_LABELS"]) - 1)
    frame = clamp(int(state["frame"]), 0, 3)
    emotion = str(state["emotion"])
    controls = ("", "", "")

    if screen == "Home (current mode)":
        if state["neuro"]:
            ns["draw_tamagotchi_home"](120, 110, mood_for_glucose(runtime, glucose))
            controls = ("HOLD SLEEP", "HOLD TREND", "BOLUS")
        else:
            ns["draw_cgm_home_screen"]()
            controls = ("HOLD SLEEP", "HOLD TREND", "BOLUS")
    elif screen == "CGM home":
        ns["draw_cgm_home_screen"]()
        controls = ("HOLD SLEEP", "HOLD TREND", "BOLUS")
    elif screen == "Buddy home":
        ns["draw_tamagotchi_home"](120, 110, mood_for_glucose(runtime, glucose))
        controls = ("HOLD SLEEP", "HOLD TREND", "BOLUS")
    elif screen == "Calm pause":
        ns["draw_calm_pause_screen"]()
        controls = ("", "BACK", "DONE")
    elif screen == "Glucose entry":
        ns["draw_value_screen"](
            "Glucose",
            1,
            glucose,
            "mg/dL",
            "Target: {}".format(ns["TARGET_BG"]),
            ns["COLOR_FOCUS"],
        )
        controls = ("+", "-", "OK")
    elif screen == "Carb entry":
        ns["draw_value_screen"](
            "Carbohydrate",
            2,
            carbs,
            "g",
            "CGM: {}".format(glucose),
            ns["COLOR_FOCUS"],
            trend,
        )
        controls = ("+", "-", "OK")
    elif screen == "Mood selection":
        ns["draw_face"](120, 110, emotion)
        controls = ("NEXT", "PREV", "SELECT")
    elif screen == "Meal portions":
        ns["draw_food"](120, 110, portion, glucose, trend)
        controls = ("NEXT", "PREV", "SELECT")
    elif screen == "Dose review":
        ns["draw_delivery_confirm_screen"](dose)
        controls = ("", "CANCEL", "CONFIRM")
    elif screen == "Buddy review":
        label = "{} / {} g".format(
            ns["PORTION_LABELS"][portion],
            ns["PORTION_CARBS"][portion],
        )
        if "bluey_safety_text" in ns:
            safety = ns["bluey_safety_text"](dose, portion)
        else:
            safety = "Adult check"
        ns["draw_bluey_parent_check_screen"](
            dose,
            label,
            safety,
            clamp(int(state["hold"]), 0, 100),
        )
        controls = ("", "CANCEL", "HOLD OK")
    elif screen == "Delivering":
        ns["draw_dosing_screen"](dose, frame)
        controls = ("", "STOP", "")
    elif screen == "Dose complete":
        ns["draw_done_screen"](dose, frame)
        controls = ("", "", "DONE")
    elif screen == "CGM graph":
        ns["draw_cgm_graph_screen"]()
        controls = ("", "BACK", "DONE")
    elif screen == "Settings menu":
        settings = ns["current_settings"]()
        selected = clamp(int(state["setting"]), 0, len(settings) - 1)
        ns["draw_settings_menu_screen"](selected, settings)
        controls = ("NEXT", "PREV", "OPEN")
    elif screen == "Button guide":
        ns["draw_controls_guide_screen"]()
        controls = ("", "BACK", "DONE")
    elif screen == "Edit setting":
        settings = ns["current_settings"]()
        selected = clamp(int(state["setting"]), 0, len(settings) - 1)
        item = settings[selected]
        ns["draw_settings_screen"](
            selected,
            len(settings),
            item[0],
            item[1],
            item[2],
            item[7],
        )
        controls = ("+", "-", "OK")
    elif screen == "Rewind":
        ns["draw_rewind_screen"](
            int(state["frame"]),
            bool(state["rewind_running"]),
        )
        controls = ("", "BACK", "HOLD OK")
    elif screen == "Locked":
        ns["draw_lock_screen"]()
        controls = ("", "", "UNLOCK")
    elif screen == "Sleep":
        ns["draw_sleep_screen"]()
        controls = ("WAKE", "WAKE", "WAKE")
    elif screen == "Status":
        ns["draw_status_screen"]("Event Log", "No events", ns["COLOR_FOCUS"])
        controls = ("", "BACK", "OK")
    elif screen == "Demo image":
        runtime.draw_demo_image()
        controls = ("", "", "EXIT")
    else:
        raise ValueError(f"Unknown screen: {screen}")

    return runtime.framebuffer.image.copy(), controls


def safe_filename(value: str) -> str:
    return "_".join(value.lower().replace("(", "").replace(")", "").split())


def export_contact_sheet(runtime: FirmwareRuntime, state: dict, output: Path) -> None:
    columns = 4
    tile_height = HEIGHT + 28
    rows = math.ceil(len(SCREENS) / columns)
    sheet = Image.new("RGB", (WIDTH * columns, tile_height * rows), (230, 233, 238))
    draw = ImageDraw.Draw(sheet)
    for index, screen in enumerate(SCREENS):
        image, _controls = render_screen(runtime, screen, state)
        x = (index % columns) * WIDTH
        y = (index // columns) * tile_height
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + HEIGHT + 8), screen, fill=(40, 44, 50), font=PIXEL_FONT)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


class SimulatorApp:
    def __init__(self, root: tk.Tk, firmware_path: Path):
        self.root = root
        self.firmware_path = firmware_path.resolve()
        self.runtime = FirmwareRuntime(self.firmware_path)
        self.last_source_mtime = self.firmware_path.stat().st_mtime
        self.photo = None
        self.render_job = None
        self.current_native_image = Image.new("RGB", (WIDTH, HEIGHT))

        self.screen_var = tk.StringVar(value=SCREENS[0])
        self.glucose_var = tk.IntVar(value=DEFAULT_STATE["glucose"])
        self.trend_var = tk.IntVar(value=DEFAULT_STATE["trend"])
        self.age_var = tk.IntVar(value=DEFAULT_STATE["age"])
        self.carbs_var = tk.IntVar(value=DEFAULT_STATE["carbs"])
        self.dose_var = tk.DoubleVar(value=DEFAULT_STATE["dose"])
        self.iob_var = tk.DoubleVar(value=DEFAULT_STATE["iob"])
        self.cob_var = tk.IntVar(value=DEFAULT_STATE["cob"])
        self.portion_var = tk.IntVar(value=DEFAULT_STATE["portion"])
        self.emotion_var = tk.StringVar(value=DEFAULT_STATE["emotion"])
        self.neuro_var = tk.BooleanVar(value=DEFAULT_STATE["neuro"])
        self.hold_var = tk.IntVar(value=DEFAULT_STATE["hold"])
        self.frame_var = tk.IntVar(value=DEFAULT_STATE["frame"])
        self.setting_var = tk.IntVar(value=DEFAULT_STATE["setting"])
        self.rewind_var = tk.BooleanVar(value=DEFAULT_STATE["rewind_running"])
        self.grid_var = tk.BooleanVar(value=False)
        self.auto_reload_var = tk.BooleanVar(value=True)
        self.zoom_var = tk.IntVar(value=3 if root.winfo_screenheight() >= 1000 else 2)
        self.status_var = tk.StringVar(value="Ready")
        self.pointer_var = tk.StringVar(value="x: --  y: --")

        self._configure_window()
        self._build_ui()
        self._bind_events()
        self._render_now()
        self.root.after(1000, self._poll_source)

    def _configure_window(self):
        self.root.title("IINTS UI Simulator")
        window_width = min(1360, self.root.winfo_screenwidth() - 40)
        window_height = min(900, self.root.winfo_screenheight() - 80)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(1080, 760)
        self.root.configure(background="#edf0f4")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#edf0f4")
        style.configure("Panel.TFrame", background="#f8f9fb")
        style.configure("TLabel", background="#edf0f4", foreground="#20242a")
        style.configure("Panel.TLabel", background="#f8f9fb", foreground="#20242a")
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Section.TLabel", font=("Helvetica", 11, "bold"))
        style.configure("TButton", padding=(10, 7))
        style.configure("Primary.TButton", foreground="#ffffff", background="#2f6f9f")
        style.map("Primary.TButton", background=[("active", "#285f88")])

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=(16, 12))
        top.grid(row=0, column=0, columnspan=3, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="IINTS UI Simulator", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.source_label = ttk.Label(top, text=str(self.firmware_path), foreground="#59636e")
        self.source_label.grid(row=0, column=1, padx=20, sticky="w")
        ttk.Checkbutton(top, text="Auto-reload", variable=self.auto_reload_var).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(top, text="Reload code", command=self.reload_firmware).grid(
            row=0, column=3, padx=4
        )
        ttk.Button(top, text="UI Builder", command=self.open_ui_builder).grid(
            row=0, column=4, padx=4
        )
        ttk.Button(top, text="Screenshot", command=self.export_current).grid(
            row=0, column=5, padx=4
        )
        ttk.Button(top, text="Export all", command=self.export_all).grid(
            row=0, column=6, padx=(4, 0)
        )

        self.root.columnconfigure(0, minsize=224)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, minsize=276)
        self.root.rowconfigure(1, weight=1)

        left = ttk.Frame(self.root, style="Panel.TFrame", padding=(14, 12))
        left.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(0, 10))
        left.rowconfigure(1, weight=1)
        ttk.Label(left, text="Screens", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.screen_list = tk.Listbox(
            left,
            listvariable=tk.StringVar(value=SCREENS),
            exportselection=False,
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
            background="#f8f9fb",
            foreground="#20242a",
            selectbackground="#dce9f2",
            selectforeground="#204f73",
            font=("Helvetica", 12),
            height=17,
        )
        self.screen_list.grid(row=1, column=0, sticky="nsew", pady=(10, 12))
        self.screen_list.selection_set(0)

        ttk.Separator(left).grid(row=2, column=0, sticky="ew", pady=8)
        ttk.Label(left, text="Quick access", style="Section.TLabel").grid(
            row=3, column=0, sticky="w", pady=(0, 6)
        )
        quick = ttk.Frame(left, style="Panel.TFrame")
        quick.grid(row=4, column=0, sticky="ew")
        quick.columnconfigure((0, 1), weight=1)
        ttk.Button(quick, text="Home", command=lambda: self.select_screen(SCREENS[0])).grid(
            row=0, column=0, sticky="ew", padx=(0, 3), pady=3
        )
        ttk.Button(quick, text="Trend", command=lambda: self.select_screen("CGM graph")).grid(
            row=0, column=1, sticky="ew", padx=(3, 0), pady=3
        )
        ttk.Button(
            quick,
            text="16+17 Settings",
            command=lambda: self.select_screen("Settings menu"),
        ).grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=3)
        ttk.Button(
            quick,
            text="16+18 Calm",
            command=lambda: self.select_screen("Calm pause"),
        ).grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=3)
        ttk.Button(
            quick,
            text="17+18 Demo",
            command=lambda: self.select_screen("Demo image"),
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=3)

        center = ttk.Frame(self.root, padding=(8, 0))
        center.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=1)

        screen_frame = tk.Frame(center, background="#111317", padx=12, pady=12)
        screen_frame.grid(row=0, column=0)
        self.screen_label = tk.Label(
            screen_frame,
            background="#000000",
            borderwidth=0,
            cursor="crosshair",
        )
        self.screen_label.pack()

        physical = ttk.Frame(center, padding=(0, 12, 0, 0))
        physical.grid(row=1, column=0, sticky="ew")
        physical.columnconfigure((0, 1, 2), weight=1, uniform="buttons")
        self.physical_buttons = []
        for index, pin in enumerate(("GP16", "GP17", "GP18")):
            style = "Primary.TButton" if index == 2 else "TButton"
            button = ttk.Button(
                physical,
                text=pin,
                style=style,
                command=lambda selected=index: self.press_physical(selected),
            )
            button.grid(row=0, column=index, sticky="ew", padx=5)
            self.physical_buttons.append(button)

        display_tools = ttk.Frame(center)
        display_tools.grid(row=2, column=0, pady=(2, 0))
        ttk.Label(display_tools, text="Zoom").grid(row=0, column=0, padx=(0, 6))
        ttk.Radiobutton(display_tools, text="2x", value=2, variable=self.zoom_var).grid(
            row=0, column=1
        )
        ttk.Radiobutton(display_tools, text="3x", value=3, variable=self.zoom_var).grid(
            row=0, column=2
        )
        ttk.Checkbutton(display_tools, text="10 px grid", variable=self.grid_var).grid(
            row=0, column=3, padx=(16, 0)
        )
        ttk.Label(display_tools, textvariable=self.pointer_var).grid(
            row=0, column=4, padx=(16, 0)
        )

        right = ttk.Frame(self.root, style="Panel.TFrame", padding=(14, 12))
        right.grid(row=1, column=2, sticky="nsew", padx=(8, 16), pady=(0, 10))
        right.columnconfigure(1, weight=1)
        ttk.Label(right, text="Preview data", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )

        row = 1
        row = self._add_spinbox(right, row, "Glucose", self.glucose_var, 40, 400, 5, "mg/dL")
        row = self._add_spinbox(right, row, "Sensor age", self.age_var, 0, 60, 1, "min")
        row = self._add_spinbox(right, row, "Carbs", self.carbs_var, 0, 250, 5, "g")
        row = self._add_spinbox(right, row, "Dose", self.dose_var, 0, 15, 0.1, "U")
        row = self._add_spinbox(right, row, "IOB", self.iob_var, 0, 15, 0.1, "U")
        row = self._add_spinbox(right, row, "COB", self.cob_var, 0, 250, 1, "g")

        ttk.Label(right, text="Trend", style="Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=6
        )
        trend_frame = ttk.Frame(right, style="Panel.TFrame")
        trend_frame.grid(row=row, column=1, sticky="ew")
        for column, (label, value) in enumerate((("Down", -1), ("Steady", 0), ("Up", 1))):
            ttk.Radiobutton(
                trend_frame,
                text=label,
                value=value,
                variable=self.trend_var,
            ).grid(row=0, column=column, sticky="w")
        row += 1

        ttk.Label(right, text="Portion", style="Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=6
        )
        labels = self.runtime.ns["PORTION_LABELS"]
        self.portion_combo = ttk.Combobox(
            right,
            state="readonly",
            values=[f"{index} - {label}" for index, label in enumerate(labels)],
        )
        self.portion_combo.current(int(self.portion_var.get()))
        self.portion_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        ttk.Label(right, text="Emotion", style="Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=6
        )
        emotion_combo = ttk.Combobox(
            right,
            state="readonly",
            values=("sad", "happy", "dizzy"),
            textvariable=self.emotion_var,
        )
        emotion_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        row = self._add_spinbox(right, row, "Animation", self.frame_var, 0, 3, 1, "frame")
        row = self._add_spinbox(right, row, "Setting", self.setting_var, 0, 6, 1, "index")

        ttk.Label(right, text="Hold progress", style="Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=6
        )
        ttk.Scale(right, from_=0, to=100, variable=self.hold_var).grid(
            row=row, column=1, sticky="ew", pady=6
        )
        row += 1

        ttk.Separator(right).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        ttk.Checkbutton(right, text="Neuro Mode", variable=self.neuro_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        row += 1
        ttk.Checkbutton(right, text="Rewind running", variable=self.rewind_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )

        status = ttk.Frame(self.root, padding=(16, 5))
        status.grid(row=2, column=0, columnspan=3, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.status_var, foreground="#59636e").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(status, text="Keys: 1 / 2 / 3", foreground="#59636e").grid(
            row=0, column=1, sticky="e"
        )

    def _add_spinbox(self, parent, row, label, variable, minimum, maximum, step, unit):
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=6
        )
        holder = ttk.Frame(parent, style="Panel.TFrame")
        holder.grid(row=row, column=1, sticky="ew", pady=3)
        holder.columnconfigure(0, weight=1)
        ttk.Spinbox(
            holder,
            from_=minimum,
            to=maximum,
            increment=step,
            textvariable=variable,
            width=8,
        ).grid(row=0, column=0, sticky="ew")
        ttk.Label(holder, text=unit, style="Panel.TLabel").grid(row=0, column=1, padx=(6, 0))
        return row + 1

    def _bind_events(self):
        self.screen_list.bind("<<ListboxSelect>>", self._on_screen_selected)
        self.portion_combo.bind("<<ComboboxSelected>>", self._on_portion_selected)
        self.screen_label.bind("<Motion>", self._on_pointer_motion)
        self.screen_label.bind("<Leave>", lambda _event: self.pointer_var.set("x: --  y: --"))
        self.root.bind("1", lambda _event: self.press_physical(0))
        self.root.bind("2", lambda _event: self.press_physical(1))
        self.root.bind("3", lambda _event: self.press_physical(2))
        self.root.bind("<Return>", lambda _event: self.press_physical(2))
        self.root.bind("<Escape>", lambda _event: self.select_screen(SCREENS[0]))

        variables = (
            self.glucose_var,
            self.trend_var,
            self.age_var,
            self.carbs_var,
            self.dose_var,
            self.iob_var,
            self.cob_var,
            self.emotion_var,
            self.neuro_var,
            self.hold_var,
            self.frame_var,
            self.setting_var,
            self.rewind_var,
            self.grid_var,
            self.zoom_var,
        )
        for variable in variables:
            variable.trace_add("write", self._schedule_render)

    def state(self) -> dict:
        def value(variable, default):
            try:
                return variable.get()
            except tk.TclError:
                return default

        return {
            "glucose": value(self.glucose_var, 120),
            "trend": value(self.trend_var, 0),
            "age": value(self.age_var, 0),
            "carbs": value(self.carbs_var, 0),
            "dose": value(self.dose_var, 0.0),
            "iob": value(self.iob_var, 0.0),
            "cob": value(self.cob_var, 0),
            "portion": value(self.portion_var, 0),
            "emotion": value(self.emotion_var, "happy"),
            "neuro": bool(value(self.neuro_var, True)),
            "hold": value(self.hold_var, 0),
            "frame": value(self.frame_var, 0),
            "setting": value(self.setting_var, 0),
            "rewind_running": bool(value(self.rewind_var, False)),
        }

    def _schedule_render(self, *_args):
        if self.render_job is not None:
            self.root.after_cancel(self.render_job)
        self.render_job = self.root.after(35, self._render_now)

    def _render_now(self):
        self.render_job = None
        screen = self.screen_var.get()
        try:
            image, controls = render_screen(self.runtime, screen, self.state())
        except Exception as exc:
            image = Image.new("RGB", (WIDTH, HEIGHT), (247, 248, 250))
            draw = ImageDraw.Draw(image)
            draw.text((12, 12), "RENDER ERROR", fill=(180, 60, 60), font=PIXEL_FONT)
            draw.text((12, 34), str(exc)[:34], fill=(32, 36, 42), font=PIXEL_FONT)
            controls = ("", "", "")
            self.status_var.set(f"Render error: {exc}")
        else:
            self.status_var.set(f"{screen} | {self.firmware_path.name}")

        self.current_native_image = image
        preview = image.resize(
            (WIDTH * int(self.zoom_var.get()), HEIGHT * int(self.zoom_var.get())),
            Image.Resampling.NEAREST,
        )
        if self.grid_var.get():
            preview = preview.copy()
            grid_draw = ImageDraw.Draw(preview)
            scale = int(self.zoom_var.get())
            for coordinate in range(0, WIDTH + 1, 10):
                position = coordinate * scale
                grid_draw.line((position, 0, position, HEIGHT * scale), fill=(180, 60, 60), width=1)
                grid_draw.line((0, position, WIDTH * scale, position), fill=(180, 60, 60), width=1)

        self.photo = ImageTk.PhotoImage(preview)
        self.screen_label.configure(image=self.photo)
        pins = ("GP16", "GP17", "GP18")
        for button, pin, label in zip(self.physical_buttons, pins, controls):
            button.configure(text=f"{pin}\n{label or '-'}")

    def _on_screen_selected(self, _event=None):
        selection = self.screen_list.curselection()
        if selection:
            self.screen_var.set(SCREENS[selection[0]])
            self._schedule_render()

    def _on_portion_selected(self, _event=None):
        self.portion_var.set(self.portion_combo.current())

    def _on_pointer_motion(self, event):
        scale = max(1, int(self.zoom_var.get()))
        x = clamp(event.x // scale, 0, WIDTH - 1)
        y = clamp(event.y // scale, 0, HEIGHT - 1)
        red, green, blue = self.current_native_image.getpixel((x, y))
        self.pointer_var.set(f"x: {x:03d}  y: {y:03d}  #{red:02X}{green:02X}{blue:02X}")

    def select_screen(self, screen: str):
        if screen not in SCREENS:
            return
        self.screen_var.set(screen)
        index = SCREENS.index(screen)
        self.screen_list.selection_clear(0, tk.END)
        self.screen_list.selection_set(index)
        self.screen_list.see(index)
        self._schedule_render()

    def press_physical(self, index: int):
        screen = self.screen_var.get()
        portion_count = len(self.runtime.ns["PORTION_LABELS"])

        if screen in ("Home (current mode)", "Buddy home") and self.neuro_var.get():
            if index == 0:
                self.select_screen("Sleep")
            elif index == 1:
                self.select_screen("CGM graph")
            else:
                self.select_screen("Meal portions")
            return
        if screen in ("Home (current mode)", "CGM home"):
            if index == 0:
                self.select_screen("Sleep")
            elif index == 1:
                self.select_screen("CGM graph")
            else:
                self.select_screen("Carb entry")
            return
        if screen == "Glucose entry":
            if index == 0:
                self.glucose_var.set(clamp(self.glucose_var.get() + 10, 40, 400))
            elif index == 1:
                self.glucose_var.set(clamp(self.glucose_var.get() - 10, 40, 400))
            else:
                self.select_screen("Carb entry")
            return
        if screen == "Carb entry":
            if index == 0:
                self.carbs_var.set(clamp(self.carbs_var.get() + 5, 0, 250))
            elif index == 1:
                self.carbs_var.set(clamp(self.carbs_var.get() - 5, 0, 250))
            else:
                self.select_screen("Dose review")
            return
        if screen == "Mood selection":
            emotions = ("sad", "happy", "dizzy")
            current = emotions.index(self.emotion_var.get())
            if index == 0:
                self.emotion_var.set(emotions[(current + 1) % len(emotions)])
            elif index == 1:
                self.emotion_var.set(emotions[(current - 1) % len(emotions)])
            else:
                self.select_screen("Meal portions")
            return
        if screen == "Meal portions":
            current = self.portion_var.get()
            if index == 0:
                self.portion_var.set((current + 1) % portion_count)
            elif index == 1:
                self.portion_var.set((current - 1) % portion_count)
            else:
                self.select_screen("Buddy review" if self.neuro_var.get() else "Dose review")
            self.portion_combo.current(self.portion_var.get())
            return
        if screen in ("Dose review", "Buddy review"):
            if index == 1:
                self.select_screen("Home (current mode)")
            elif screen == "Buddy review" and self.hold_var.get() < 100:
                self.hold_var.set(clamp(self.hold_var.get() + 25, 0, 100))
            else:
                self.select_screen("Delivering")
            return
        if screen == "Delivering":
            if index == 1:
                self.select_screen("Home (current mode)")
            return
        if screen == "Dose complete":
            if index == 2:
                self.select_screen("Home (current mode)")
            return
        if screen == "CGM graph":
            if index in (1, 2):
                self.select_screen("Home (current mode)")
            return
        if screen == "Settings menu":
            settings_count = len(self.runtime.ns["current_settings"]())
            if index == 0:
                self.setting_var.set((self.setting_var.get() + 1) % settings_count)
            elif index == 1:
                self.setting_var.set((self.setting_var.get() - 1) % settings_count)
            else:
                setting_id = self.runtime.ns["current_settings"]()[self.setting_var.get()][7]
                if setting_id == "rewind":
                    self.select_screen("Rewind")
                elif setting_id == "guide":
                    self.select_screen("Button guide")
                else:
                    self.select_screen("Edit setting")
            return
        if screen == "Edit setting":
            settings = self.runtime.ns["current_settings"]()
            selected = clamp(self.setting_var.get(), 0, len(settings) - 1)
            item = settings[selected]
            if index in (0, 1):
                direction = 1 if index == 0 else -1
                new_value = clamp(item[1] + direction * item[3], item[5], item[6])
                self.runtime.ns["apply_setting"](item[7], new_value)
                if item[7] == "tamagotchi":
                    self.neuro_var.set(bool(new_value))
                self._schedule_render()
            else:
                self.select_screen("Settings menu")
            return
        if screen == "Rewind":
            if index == 1:
                self.select_screen("Settings menu")
            elif index == 2:
                self.rewind_var.set(not self.rewind_var.get())
            return
        if screen in ("Locked", "Sleep"):
            self.select_screen("Home (current mode)")
            return
        if screen == "Calm pause" and index in (1, 2):
            self.select_screen("Home (current mode)")
            return
        if screen == "Button guide" and index in (1, 2):
            self.select_screen("Settings menu")
            return
        if screen in ("Status", "Demo image") and index in (1, 2):
            self.select_screen("Home (current mode)")

    def reload_firmware(self, silent=False):
        try:
            self.runtime = FirmwareRuntime(self.firmware_path)
            self.last_source_mtime = self.firmware_path.stat().st_mtime
            labels = self.runtime.ns["PORTION_LABELS"]
            self.portion_combo.configure(
                values=[f"{index} - {label}" for index, label in enumerate(labels)]
            )
            self._render_now()
            self.status_var.set(f"Reloaded {self.firmware_path.name}")
        except Exception as exc:
            self.status_var.set(f"Reload failed: {exc}")
            if not silent:
                messagebox.showerror("Reload failed", str(exc), parent=self.root)

    def _poll_source(self):
        try:
            modified = self.firmware_path.stat().st_mtime
        except OSError:
            modified = self.last_source_mtime
        if self.auto_reload_var.get() and modified != self.last_source_mtime:
            self.reload_firmware(silent=True)
        self.root.after(1000, self._poll_source)

    def export_current(self):
        output_dir = APP_DIR / "previews"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output = output_dir / f"{safe_filename(self.screen_var.get())}_{timestamp}.png"
        self.current_native_image.save(output)
        self.status_var.set(f"Saved {output.relative_to(APP_DIR)}")

    def open_ui_builder(self):
        if __package__:
            from .ui_builder import UIBuilderWindow
        else:
            from ui_builder import UIBuilderWindow

        UIBuilderWindow(self.root, self.status_var.set)

    def export_all(self):
        output_dir = APP_DIR / "previews"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output = output_dir / f"iints_ui_contact_sheet_{timestamp}.png"
        try:
            export_contact_sheet(self.runtime, self.state(), output)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc), parent=self.root)
            return
        self._render_now()
        self.status_var.set(f"Saved {output.relative_to(APP_DIR)}")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--firmware",
        type=Path,
        default=DEFAULT_FIRMWARE,
        help="MicroPython source file to preview.",
    )
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        help="Render every screen to one PNG without opening a window.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    runtime = FirmwareRuntime(args.firmware)
    if args.contact_sheet:
        export_contact_sheet(runtime, dict(DEFAULT_STATE), args.contact_sheet)
        print(args.contact_sheet.resolve())
        return

    root = tk.Tk()
    SimulatorApp(root, args.firmware)
    root.mainloop()


if __name__ == "__main__":
    main()
