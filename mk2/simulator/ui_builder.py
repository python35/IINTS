"""Visual editor for custom 240x240 IINTS pump screens."""

from __future__ import annotations

import json
import re
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk


WIDTH = 240
HEIGHT = 240
ZOOM = 2
PROJECT_VERSION = 1
ELEMENT_TYPES = ("Text", "Filled rectangle", "Rectangle", "Circle", "Filled circle", "Line")
DEFAULT_DESIGN = {
    "version": PROJECT_VERSION,
    "name": "My pump screen",
    "background": "#F4F7F9",
    "elements": [
        {"type": "Text", "x": 24, "y": 18, "w": 192, "h": 16, "text": "PUMP STATUS", "color": "#1C262E"},
        {"type": "Rectangle", "x": 20, "y": 48, "w": 200, "h": 96, "text": "", "color": "#C6D0D8"},
        {"type": "Text", "x": 36, "y": 66, "w": 168, "h": 16, "text": "GLUCOSE", "color": "#4B5B68"},
        {"type": "Text", "x": 36, "y": 92, "w": 168, "h": 24, "text": "120 mg/dL", "color": "#1C262E"},
        {"type": "Line", "x": 20, "y": 166, "w": 200, "h": 0, "text": "", "color": "#C6D0D8"},
        {"type": "Text", "x": 28, "y": 188, "w": 184, "h": 16, "text": "1  MENU       2  BACK       3  OK", "color": "#266086"},
    ],
}
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_design(data: object) -> dict:
    if not isinstance(data, dict) or data.get("version") != PROJECT_VERSION:
        raise ValueError("Unsupported or invalid UI Builder project version.")
    name = data.get("name")
    background = data.get("background")
    elements = data.get("elements")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("The project needs a name.")
    if not isinstance(background, str) or not COLOR_RE.fullmatch(background):
        raise ValueError("Background color must be in #RRGGBB format.")
    if not isinstance(elements, list) or len(elements) > 500:
        raise ValueError("Elements must be a list with no more than 500 items.")

    validated = []
    for index, item in enumerate(elements, start=1):
        if not isinstance(item, dict) or item.get("type") not in ELEMENT_TYPES:
            raise ValueError(f"Element {index} has an unsupported type.")
        color = item.get("color")
        if not isinstance(color, str) or not COLOR_RE.fullmatch(color):
            raise ValueError(f"Element {index} has an invalid color.")
        coordinates = {}
        for key, maximum in (("x", WIDTH - 1), ("y", HEIGHT - 1), ("w", WIDTH), ("h", HEIGHT)):
            value = item.get(key)
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"Element {index} has an invalid {key} coordinate.")
            coordinates[key] = max(0, min(maximum, value))
        text = item.get("text", "")
        if not isinstance(text, str):
            raise ValueError(f"Element {index} text must be a string.")
        if len(text) > 240:
            raise ValueError(f"Element {index} text is too long.")
        validated.append(
            {
                "type": item["type"],
                **coordinates,
                "text": text,
                "color": color.upper(),
            }
        )
    return {
        "version": PROJECT_VERSION,
        "name": name.strip()[:80],
        "background": background.upper(),
        "elements": validated,
    }


def validate_project(data: object) -> dict:
    if not isinstance(data, dict) or data.get("version") != PROJECT_VERSION:
        raise ValueError("Unsupported or invalid UI Builder project version.")
    name = data.get("name")
    screens = data.get("screens")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("The project needs a name.")
    if not isinstance(screens, list) or not 1 <= len(screens) <= 50:
        raise ValueError("A project must have between 1 and 50 screens.")

    validated_screens = [validate_design(screen) for screen in screens]
    names = [screen["name"].casefold() for screen in validated_screens]
    if len(names) != len(set(names)):
        raise ValueError("Each screen needs a unique name.")
    return {
        "version": PROJECT_VERSION,
        "name": name.strip()[:80],
        "screens": validated_screens,
    }


def _rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))


def _safe_file_stem(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "pump_ui"


def render_design(data: dict) -> Image.Image:
    design = validate_design(data)
    image = Image.new("RGB", (WIDTH, HEIGHT), _rgb(design["background"]))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for element in design["elements"]:
        kind = element["type"]
        x, y, w, h = (element[key] for key in ("x", "y", "w", "h"))
        color = element["color"]
        if kind in ("Filled rectangle", "Rectangle", "Circle", "Filled circle") and (
            w == 0 or h == 0
        ):
            continue
        bounds = (
            x,
            y,
            min(WIDTH - 1, x + max(0, w - 1)),
            min(HEIGHT - 1, y + max(0, h - 1)),
        )
        if kind == "Text":
            draw.text((x, y), element["text"], fill=color, font=font)
        elif kind == "Filled rectangle":
            draw.rectangle(bounds, fill=color)
        elif kind == "Rectangle":
            draw.rectangle(bounds, outline=color)
        elif kind == "Circle":
            radius = min(w, h) // 2
            center_x, center_y = x + w // 2, y + h // 2
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                outline=color,
            )
        elif kind == "Filled circle":
            radius = min(w, h) // 2
            center_x, center_y = x + w // 2, y + h // 2
            draw.ellipse(
                (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                fill=color,
            )
        elif kind == "Line":
            draw.line((x, y, min(WIDTH - 1, x + w), min(HEIGHT - 1, y + h)), fill=color)
    return image


def _rgb565_literal(color: str) -> str:
    red, green, blue = _rgb(color)
    value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
    swapped = ((value & 0xFF) << 8) | (value >> 8)
    return f"0x{swapped:04X}"


def generate_firmware_module(data: dict) -> str:
    design = validate_design(data)
    lines = [
        '"""Generated by the IINTS UI Builder; draws one 240x240 screen."""',
        "",
        "def draw_custom_ui(fb):",
        '    """Draw this screen on a MicroPython framebuf.FrameBuffer."""',
        f"    fb.fill({_rgb565_literal(design['background'])})",
    ]
    for element in design["elements"]:
        kind = element["type"]
        x, y, w, h = (element[key] for key in ("x", "y", "w", "h"))
        color = _rgb565_literal(element["color"])
        if kind == "Text":
            text = element["text"]
            try:
                text.encode("ascii")
            except UnicodeEncodeError as exc:
                raise ValueError("Firmware text must use ASCII characters.") from exc
            lines.append(f"    fb.text({text!r}, {x}, {y}, {color})")
        elif kind == "Filled rectangle":
            lines.append(f"    fb.fill_rect({x}, {y}, {w}, {h}, {color})")
        elif kind == "Rectangle":
            lines.append(f"    fb.rect({x}, {y}, {w}, {h}, {color})")
        elif kind == "Line":
            lines.append(f"    fb.line({x}, {y}, {min(WIDTH - 1, x + w)}, {min(HEIGHT - 1, y + h)}, {color})")
        elif kind in ("Circle", "Filled circle"):
            radius = min(w, h) // 2
            if radius == 0:
                continue
            lines.append(
                f"    _draw_circle(fb, {x + w // 2}, {y + h // 2}, "
                f"{radius}, {color}, {kind == 'Filled circle'})"
            )

    if any(item["type"] in ("Circle", "Filled circle") for item in design["elements"]):
        lines.extend(
            [
                "",
                "",
                "def _draw_circle(fb, cx, cy, radius, color, filled=False):",
                "    x = radius",
                "    y = 0",
                "    error = 1 - radius",
                "    while x >= y:",
                "        if filled:",
                "            fb.hline(cx - x, cy + y, 2 * x + 1, color)",
                "            fb.hline(cx - x, cy - y, 2 * x + 1, color)",
                "            fb.hline(cx - y, cy + x, 2 * y + 1, color)",
                "            fb.hline(cx - y, cy - x, 2 * y + 1, color)",
                "        else:",
                "            fb.pixel(cx + x, cy + y, color)",
                "            fb.pixel(cx + y, cy + x, color)",
                "            fb.pixel(cx - y, cy + x, color)",
                "            fb.pixel(cx - x, cy + y, color)",
                "            fb.pixel(cx - x, cy - y, color)",
                "            fb.pixel(cx - y, cy - x, color)",
                "            fb.pixel(cx + y, cy - x, color)",
                "            fb.pixel(cx + x, cy - y, color)",
                "        y += 1",
                "        if error < 0:",
                "            error += 2 * y + 1",
                "        else:",
                "            x -= 1",
                "            error += 2 * (y - x) + 1",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def generate_firmware_project(data: dict) -> str:
    project = validate_project(data)
    function_names = []
    modules = []
    for index, screen in enumerate(project["screens"], start=1):
        base_name = re.sub(r"[^A-Za-z0-9]+", "_", screen["name"]).strip("_").lower()
        if not base_name:
            base_name = f"screen_{index}"
        function_name = "draw_" + base_name
        if function_name in function_names:
            function_name = f"{function_name}_{index}"
        function_names.append(function_name)
        module = generate_firmware_module(screen).replace(
            "def draw_custom_ui(fb):", f"def {function_name}(fb):", 1
        )
        modules.append(module)

    modules.append(
        "\n\ndef draw_custom_ui(fb):\n"
        '    """Draw the first screen in the project."""\n'
        f"    {function_names[0]}(fb)\n"
    )
    return "\n".join(modules)


def render_contact_sheet(screens: list[dict]) -> Image.Image:
    if not screens:
        raise ValueError("A contact sheet needs at least one screen.")
    validated = [validate_design(screen) for screen in screens]
    columns = min(3, len(validated))
    label_height = 24
    rows = (len(validated) + columns - 1) // columns
    image = Image.new(
        "RGB",
        (WIDTH * columns, (HEIGHT + label_height) * rows),
        (230, 233, 238),
    )
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for index, screen in enumerate(validated):
        x = (index % columns) * WIDTH
        y = (index // columns) * (HEIGHT + label_height)
        image.paste(render_design(screen), (x, y))
        draw.text((x + 8, y + HEIGHT + 6), screen["name"], fill=(40, 44, 50), font=font)
    return image


class UIBuilderWindow:
    def __init__(self, parent: tk.Misc, on_status=None):
        self.parent = parent
        self.on_status = on_status
        self.window = tk.Toplevel(parent)
        self.window.title("IINTS UI Builder — 240 x 240")
        self.window.geometry("1040x690")
        self.window.minsize(900, 610)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.screens = [deepcopy(DEFAULT_DESIGN)]
        self.selected_screen_index = 0
        self.project_path: Path | None = None
        self.selected_index: int | None = None
        self.dirty = False
        self.drag_origin: tuple[int, int, int, int] | None = None
        self.photo = None

        self.name_var = tk.StringVar(value=self.design["name"])
        self.project_name_var = tk.StringVar(value="Pump UI")
        self.position_vars = {key: tk.StringVar() for key in ("x", "y", "w", "h")}
        self.text_var = tk.StringVar()
        self.color_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Drag elements on the canvas to position them.")
        self._build()
        self._sync_screens()
        self._sync_layers()
        self._refresh()
        self.window.bind("<Delete>", lambda _event: self.delete_selected())

    @property
    def design(self) -> dict:
        return self.screens[self.selected_screen_index]

    @design.setter
    def design(self, value: dict):
        self.screens[self.selected_screen_index] = value

    def _build(self):
        toolbar = ttk.Frame(self.window, padding=8)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="New", command=self.new_project).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Open…", command=self.open_project).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_project).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Screen PNG…", command=self.export_png).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Contact sheet…", command=self.export_contact_sheet).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Export firmware…", command=self.export_firmware).pack(side="left", padx=2)
        ttk.Label(toolbar, text="Project").pack(side="left", padx=(10, 4))
        project_name = ttk.Entry(toolbar, textvariable=self.project_name_var, width=15)
        project_name.pack(side="left")
        project_name.bind("<KeyRelease>", self._mark_dirty)
        ttk.Label(toolbar, text="Screen name").pack(side="left", padx=(18, 5))
        name = ttk.Entry(toolbar, textvariable=self.name_var, width=24)
        name.pack(side="left")
        name.bind("<FocusOut>", self._name_changed)
        name.bind("<Return>", self._name_changed)
        name.bind("<KeyRelease>", self._mark_dirty)

        body = ttk.Frame(self.window, padding=(8, 0, 8, 8))
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, width=176)
        left.pack(side="left", fill="y", padx=(0, 8))
        ttk.Label(left, text="Screens", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.screen_selector = ttk.Combobox(left, state="readonly")
        self.screen_selector.pack(fill="x", pady=(4, 3))
        self.screen_selector.bind("<<ComboboxSelected>>", self._screen_selected)
        screen_buttons = ttk.Frame(left)
        screen_buttons.pack(fill="x")
        ttk.Button(screen_buttons, text="Add", command=self.add_screen).pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(screen_buttons, text="Copy", command=self.duplicate_screen).pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(left, text="Delete screen", command=self.delete_screen).pack(fill="x", pady=(3, 8))
        ttk.Separator(left).pack(fill="x", pady=(0, 8))
        ttk.Label(left, text="Add element", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        for element_type in ELEMENT_TYPES:
            ttk.Button(
                left,
                text="+ " + element_type,
                command=lambda kind=element_type: self.add_element(kind),
            ).pack(fill="x", pady=2)
        ttk.Separator(left).pack(fill="x", pady=8)
        ttk.Label(left, text="Layers", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.layers = tk.Listbox(left, exportselection=False, height=12, activestyle="none")
        self.layers.pack(fill="both", expand=True, pady=(4, 5))
        self.layers.bind("<<ListboxSelect>>", self._layer_selected)
        layer_buttons = ttk.Frame(left)
        layer_buttons.pack(fill="x")
        ttk.Button(layer_buttons, text="Up", command=lambda: self.move_layer(-1)).pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(layer_buttons, text="Down", command=lambda: self.move_layer(1)).pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(left, text="Delete selected", command=self.delete_selected).pack(
            fill="x", pady=(5, 0)
        )

        canvas_holder = ttk.Frame(body)
        canvas_holder.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(
            canvas_holder,
            width=WIDTH * ZOOM,
            height=HEIGHT * ZOOM,
            background="#252a30",
            highlightthickness=0,
        )
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self._canvas_press)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Motion>", self._canvas_motion)

        right = ttk.Frame(body, width=210)
        right.pack(side="right", fill="y", padx=(8, 0))
        ttk.Label(right, text="Properties", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.selected_label = ttk.Label(right, text="Nothing selected")
        self.selected_label.pack(anchor="w", pady=(3, 8))
        for key in ("x", "y", "w", "h"):
            row = ttk.Frame(right)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=key.upper(), width=5).pack(side="left")
            ttk.Entry(row, textvariable=self.position_vars[key], width=9).pack(side="left")
        ttk.Label(right, text="Text").pack(anchor="w", pady=(8, 2))
        self.text_entry = ttk.Entry(right, textvariable=self.text_var)
        self.text_entry.pack(fill="x")
        self.text_entry.bind("<Return>", lambda _event: self.apply_properties())
        ttk.Label(right, text="Element color").pack(anchor="w", pady=(8, 2))
        color_row = ttk.Frame(right)
        color_row.pack(fill="x")
        ttk.Entry(color_row, textvariable=self.color_var, width=10).pack(side="left")
        ttk.Button(color_row, text="Choose…", command=self.choose_color).pack(side="left", padx=4)
        ttk.Button(right, text="Apply properties", command=self.apply_properties).pack(
            fill="x", pady=(8, 4)
        )
        ttk.Button(right, text="Background color…", command=self.choose_background).pack(fill="x")
        ttk.Label(
            right,
            text="Canvas: 240 × 240 px\nDrag to move. Use the layer list to select objects.",
            justify="left",
        ).pack(anchor="w", pady=(14, 0))

        ttk.Label(self.window, textvariable=self.status_var, anchor="w", padding=(10, 5)).pack(fill="x")

    def _set_status(self, message: str):
        self.status_var.set(message)
        if self.on_status is not None:
            self.on_status(message)

    def _mark_dirty(self, _event=None):
        self.dirty = True
        project_name = self.project_path.name if self.project_path else self.project_name_var.get()
        marker = f" — {project_name}*"
        self.window.title(f"IINTS UI Builder{marker}")

    def _set_clean(self):
        self.dirty = False
        name = self.project_path.name if self.project_path else self.project_name_var.get()
        self.window.title(f"IINTS UI Builder — {name}")

    def _name_changed(self, _event=None):
        name = self.name_var.get().strip()
        if not name:
            self.name_var.set(self.design["name"])
            return
        if name != self.design["name"]:
            if any(
                index != self.selected_screen_index and screen["name"].casefold() == name.casefold()
                for index, screen in enumerate(self.screens)
            ):
                messagebox.showerror(
                    "Duplicate screen name",
                    "Each screen needs a unique name.",
                    parent=self.window,
                )
                self.name_var.set(self.design["name"])
                return
            self.design["name"] = name[:80]
            self.name_var.set(self.design["name"])
            self._mark_dirty()
            self._sync_screens()

    def _sync_screens(self):
        self.screen_selector.configure(values=[screen["name"] for screen in self.screens])
        self.screen_selector.current(self.selected_screen_index)

    def _screen_selected(self, _event=None):
        selected = self.screen_selector.current()
        self._name_changed()
        if selected < 0 or selected == self.selected_screen_index:
            return
        self.selected_screen_index = selected
        self.selected_index = None
        self.name_var.set(self.design["name"])
        self._sync_layers()
        self._select(None)
        self._set_status(f"Editing screen: {self.design['name']}.")

    def add_screen(self):
        if len(self.screens) >= 50:
            messagebox.showerror("Screen limit", "A project can contain at most 50 screens.", parent=self.window)
            return
        name = f"Screen {len(self.screens) + 1}"
        existing = {screen["name"].casefold() for screen in self.screens}
        suffix = 2
        base_name = name
        while name.casefold() in existing:
            name = f"{base_name} {suffix}"
            suffix += 1
        self.screens.append(
            {"name": name, "background": self.design["background"], "elements": []}
        )
        self.selected_screen_index = len(self.screens) - 1
        self.selected_index = None
        self.name_var.set(name)
        self._mark_dirty()
        self._sync_screens()
        self._select(None)
        self._set_status(f"Added screen: {name}.")

    def duplicate_screen(self):
        if len(self.screens) >= 50:
            messagebox.showerror("Screen limit", "A project can contain at most 50 screens.", parent=self.window)
            return
        duplicate = deepcopy(self.design)
        base_name = f"{duplicate['name']} copy"
        names = {screen["name"].casefold() for screen in self.screens}
        name = base_name
        suffix = 2
        while name.casefold() in names:
            name = f"{base_name} {suffix}"
            suffix += 1
        duplicate["name"] = name
        self.screens.append(duplicate)
        self.selected_screen_index = len(self.screens) - 1
        self.selected_index = None
        self.name_var.set(name)
        self._mark_dirty()
        self._sync_screens()
        self._select(None)
        self._set_status(f"Duplicated screen as {name}.")

    def delete_screen(self):
        if len(self.screens) == 1:
            messagebox.showinfo("Keep one screen", "A project must contain at least one screen.", parent=self.window)
            return
        if not messagebox.askyesno(
            "Delete screen?",
            f"Delete the screen “{self.design['name']}”?",
            parent=self.window,
        ):
            return
        deleted_name = self.design["name"]
        del self.screens[self.selected_screen_index]
        self.selected_screen_index = min(self.selected_screen_index, len(self.screens) - 1)
        self.selected_index = None
        self.name_var.set(self.design["name"])
        self._mark_dirty()
        self._sync_screens()
        self._select(None)
        self._set_status(f"Deleted screen: {deleted_name}.")

    def _sync_layers(self):
        self.layers.delete(0, tk.END)
        for index, item in enumerate(self.design["elements"], start=1):
            label = item["text"] if item["type"] == "Text" and item["text"] else item["type"]
            self.layers.insert(tk.END, f"{index:02d}  {label[:22]}")
        if self.selected_index is not None and self.selected_index < len(self.design["elements"]):
            self.layers.selection_set(self.selected_index)
            self.layers.see(self.selected_index)

    def _select(self, index: int | None):
        self.selected_index = index
        if index is None:
            self.selected_label.configure(text="Nothing selected")
            for variable in self.position_vars.values():
                variable.set("")
            self.text_var.set("")
            self.color_var.set("")
        else:
            item = self.design["elements"][index]
            self.selected_label.configure(text=item["type"])
            for key, variable in self.position_vars.items():
                variable.set(str(item[key]))
            self.text_var.set(item["text"])
            self.color_var.set(item["color"])
        self._sync_layers()
        self._refresh()

    def _layer_selected(self, _event=None):
        selection = self.layers.curselection()
        if selection:
            self._select(selection[0])

    def add_element(self, kind: str):
        item = {
            "type": kind,
            "x": 80,
            "y": 90,
            "w": 80 if kind in ("Circle", "Filled circle") else 100,
            "h": 50 if kind in ("Circle", "Filled circle") else 24,
            "text": "Text" if kind == "Text" else "",
            "color": "#266086",
        }
        self.design["elements"].append(item)
        self._mark_dirty()
        self._select(len(self.design["elements"]) - 1)
        self._set_status(f"Added {kind}.")

    def delete_selected(self):
        if self.selected_index is None:
            return
        del self.design["elements"][self.selected_index]
        self._mark_dirty()
        self._select(None)
        self._set_status("Element deleted.")

    def move_layer(self, direction: int):
        if self.selected_index is None:
            return
        target = self.selected_index + direction
        if target < 0 or target >= len(self.design["elements"]):
            return
        elements = self.design["elements"]
        elements[self.selected_index], elements[target] = elements[target], elements[self.selected_index]
        self._mark_dirty()
        self._select(target)

    def apply_properties(self):
        if self.selected_index is None:
            return
        try:
            item = self.design["elements"][self.selected_index]
            for key, variable in self.position_vars.items():
                value = int(variable.get())
                maximum = WIDTH if key in ("w", "h") else WIDTH - 1
                item[key] = max(0, min(maximum, value))
            item["text"] = self.text_var.get()
            color = self.color_var.get().strip()
            if not COLOR_RE.fullmatch(color):
                raise ValueError("Color must be in #RRGGBB format.")
            item["color"] = color.upper()
            self.design = validate_design(self.design)
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Invalid properties", str(exc), parent=self.window)
            return
        self._mark_dirty()
        self._sync_layers()
        self._refresh()

    def choose_color(self):
        initial = self.color_var.get() or "#266086"
        selected = colorchooser.askcolor(initialcolor=initial, parent=self.window)[1]
        if selected:
            self.color_var.set(selected.upper())

    def choose_background(self):
        selected = colorchooser.askcolor(
            initialcolor=self.design["background"], parent=self.window
        )[1]
        if selected:
            self.design["background"] = selected.upper()
            self._mark_dirty()
            self._refresh()

    def _refresh(self):
        image = render_design(self.design).resize(
            (WIDTH * ZOOM, HEIGHT * ZOOM), Image.Resampling.NEAREST
        )
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        if self.selected_index is not None and self.selected_index < len(self.design["elements"]):
            item = self.design["elements"][self.selected_index]
            x, y = item["x"] * ZOOM, item["y"] * ZOOM
            right = min(WIDTH, item["x"] + max(1, item["w"])) * ZOOM
            bottom = min(HEIGHT, item["y"] + max(1, item["h"])) * ZOOM
            self.canvas.create_rectangle(
                x, y, right, bottom, outline="#e34343", width=1, dash=(4, 2)
            )

    def _hit_test(self, x: int, y: int) -> int | None:
        for index in range(len(self.design["elements"]) - 1, -1, -1):
            item = self.design["elements"][index]
            left, top = item["x"], item["y"]
            right = left + max(8, item["w"])
            bottom = top + max(8, item["h"])
            if left <= x <= right and top <= y <= bottom:
                return index
        return None

    def _canvas_press(self, event):
        x, y = max(0, event.x // ZOOM), max(0, event.y // ZOOM)
        index = self._hit_test(x, y)
        self._select(index)
        if index is not None:
            item = self.design["elements"][index]
            self.drag_origin = (x, y, item["x"], item["y"])

    def _canvas_drag(self, event):
        if self.drag_origin is None or self.selected_index is None:
            return
        origin_x, origin_y, item_x, item_y = self.drag_origin
        item = self.design["elements"][self.selected_index]
        item["x"] = max(0, min(WIDTH - 1, item_x + event.x // ZOOM - origin_x))
        item["y"] = max(0, min(HEIGHT - 1, item_y + event.y // ZOOM - origin_y))
        for key in ("x", "y"):
            self.position_vars[key].set(str(item[key]))
        self._refresh()

    def _canvas_release(self, _event):
        if self.drag_origin is not None and self.selected_index is not None:
            self._mark_dirty()
        self.drag_origin = None

    def _canvas_motion(self, event):
        self.status_var.set(f"Canvas position: x={event.x // ZOOM}, y={event.y // ZOOM}")

    def new_project(self):
        if self.dirty and not messagebox.askyesno(
            "Discard changes?",
            "Start a new project and discard unsaved changes?",
            parent=self.window,
        ):
            return
        self.screens = [deepcopy(DEFAULT_DESIGN)]
        self.selected_screen_index = 0
        self.project_name_var.set("Pump UI")
        self.project_path = None
        self.name_var.set(self.design["name"])
        self._select(None)
        self.dirty = False
        self._sync_screens()
        self._set_clean()
        self._set_status("New screen ready.")

    def open_project(self):
        path = filedialog.askopenfilename(
            parent=self.window,
            title="Open UI Builder project",
            filetypes=(("IINTS UI project", "*.iintsui"), ("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        if self.dirty and not messagebox.askyesno(
            "Discard changes?",
            "Open another project and discard unsaved changes?",
            parent=self.window,
        ):
            return
        try:
            with Path(path).open("r", encoding="utf-8") as source:
                project = validate_project(json.load(source))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("Open failed", str(exc), parent=self.window)
            return
        self.screens = project["screens"]
        self.selected_screen_index = 0
        self.selected_index = None
        self.project_path = Path(path)
        self.project_name_var.set(project["name"])
        self.name_var.set(self.design["name"])
        self._sync_screens()
        self._select(None)
        self._set_clean()
        self._set_status(f"Opened {self.project_path.name}.")

    def save_project(self):
        self._name_changed()
        path = self.project_path
        if path is None:
            selected = filedialog.asksaveasfilename(
                parent=self.window,
                title="Save UI Builder project",
                defaultextension=".iintsui",
                initialfile=_safe_file_stem(self.project_name_var.get()) + ".iintsui",
                filetypes=(("IINTS UI project", "*.iintsui"), ("JSON files", "*.json")),
            )
            if not selected:
                return False
            path = Path(selected)
        try:
            project = validate_project(
                {
                    "version": PROJECT_VERSION,
                    "name": self.project_name_var.get(),
                    "screens": self.screens,
                }
            )
            path.write_text(json.dumps(project, indent=2), encoding="utf-8")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Save failed", str(exc), parent=self.window)
            return False
        self.project_path = path
        self.project_name_var.set(project["name"])
        self._set_clean()
        self._set_status(f"Saved project to {path}.")
        return True

    def export_png(self):
        path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export screen preview",
            defaultextension=".png",
            initialfile=_safe_file_stem(self.design["name"]) + ".png",
            filetypes=(("PNG image", "*.png"),),
        )
        if not path:
            return
        try:
            render_design(self.design).save(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("PNG export failed", str(exc), parent=self.window)
            return
        self._set_status(f"Exported PNG to {path}.")

    def export_contact_sheet(self):
        path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export all screen previews",
            defaultextension=".png",
            initialfile=_safe_file_stem(self.project_name_var.get()) + "_screens.png",
            filetypes=(("PNG image", "*.png"),),
        )
        if not path:
            return
        try:
            render_contact_sheet(self.screens).save(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Contact sheet export failed", str(exc), parent=self.window)
            return
        self._set_status(f"Exported contact sheet to {path}.")

    def export_firmware(self):
        path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export MicroPython drawing module",
            defaultextension=".py",
            initialfile=_safe_file_stem(self.project_name_var.get()) + "_ui.py",
            filetypes=(("Python module", "*.py"),),
        )
        if not path:
            return
        try:
            source = generate_firmware_project(
                {
                    "version": PROJECT_VERSION,
                    "name": self.project_name_var.get(),
                    "screens": self.screens,
                }
            )
            Path(path).write_text(source, encoding="utf-8")
            compile(source, path, "exec")
        except (OSError, ValueError, SyntaxError) as exc:
            messagebox.showerror("Firmware export failed", str(exc), parent=self.window)
            return
        self._set_status(f"Exported MicroPython module to {path}.")

    def close(self):
        if self.dirty and not messagebox.askyesno(
            "Discard changes?",
            "Close the UI Builder and discard unsaved changes?",
            parent=self.window,
        ):
            return
        self.window.destroy()
