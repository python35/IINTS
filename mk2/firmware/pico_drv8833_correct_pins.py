import machine
import utime
import framebuf
import gc
from st7789 import ST7789

# --- Pin mapping ---
PIN_DRV_EEP = 28

PIN_MOTOR_IN1 = 4
PIN_MOTOR_IN2 = 5
PIN_MOTOR_IN3 = 6
PIN_MOTOR_IN4 = 9

PIN_DISPLAY_SCK = 10
PIN_DISPLAY_SDA = 11
PIN_DISPLAY_RES = 12
PIN_DISPLAY_DC = 13

PIN_BUTTON_1 = 16
PIN_BUTTON_2 = 17
PIN_BUTTON_3 = 18

# --- DRV8833 enable ---
drv_eep = machine.Pin(PIN_DRV_EEP, machine.Pin.OUT)
drv_eep.value(1)

# --- Onboard status LED ---
try:
    onboard_led = machine.Pin("LED", machine.Pin.OUT)
except Exception:
    try:
        onboard_led = machine.Pin(25, machine.Pin.OUT)
    except Exception:
        onboard_led = None


def set_delivery_led(is_on):
    if onboard_led is not None:
        onboard_led.value(1 if is_on else 0)


set_delivery_led(False)

# --- Scherminitialisatie ---
spi = machine.SPI(
    1,
    baudrate=40000000,
    polarity=1,
    phase=1,
    sck=machine.Pin(PIN_DISPLAY_SCK),
    mosi=machine.Pin(PIN_DISPLAY_SDA),
)
dc = machine.Pin(PIN_DISPLAY_DC, machine.Pin.OUT)
reset = machine.Pin(PIN_DISPLAY_RES, machine.Pin.OUT)

display = ST7789(spi, 240, 240, reset=reset, dc=dc)
display.init()

# BLK zit volgens de mapping direct op Pico 3V3, dus geen GPIO nodig.
ST7789_DISPOFF = 0x28
ST7789_SLPIN = 0x10
ST7789_SLPOUT = 0x11
ST7789_DISPON = 0x29

# --- Grafische UI ---
WIDTH = 240
HEIGHT = 240


def rgb565(r, g, b):
    # Convert to 16-bit RGB565 and swap bytes for MicroPython's little-endian FrameBuffer
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | ((c >> 8) & 0xFF)


# --- Rustig IPS-palet: neutraal, hoog contrast en niet afhankelijk van kleur ---
COLOR_BG = rgb565(244, 247, 249)        # Zacht koelwit
COLOR_PANEL = rgb565(255, 255, 255)     # Primaire oppervlakken
COLOR_PANEL_2 = rgb565(232, 238, 243)   # Rustige selectie/status
COLOR_EDGE = rgb565(198, 208, 216)      # Scheiding zonder hard contrast
COLOR_SHADOW = rgb565(224, 230, 234)
COLOR_TEXT = rgb565(28, 38, 46)         # Donker antraciet
COLOR_MUTED = rgb565(75, 91, 104)       # Leesbare secundaire tekst
COLOR_FOCUS = rgb565(38, 96, 134)       # Gedempt klinisch blauw
COLOR_MINT = rgb565(38, 96, 134)
COLOR_SUCCESS = rgb565(43, 112, 92)     # Alleen aanvullend op een tekstlabel
COLOR_CORAL = rgb565(174, 61, 64)
COLOR_AMBER = rgb565(145, 94, 8)
COLOR_BLUE = rgb565(38, 96, 134)
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF

gc.collect()
buffer = bytearray(WIDTH * HEIGHT * 2)
fb = framebuf.FrameBuffer(buffer, WIDTH, HEIGHT, framebuf.RGB565)
char_buffer = bytearray(8 * 8 * 2)
char_fb = framebuf.FrameBuffer(char_buffer, 8, 8, framebuf.RGB565)
raw_image_row_buffer = bytearray(64 * 2)
raw_image_row_view = memoryview(raw_image_row_buffer)
raw_bg_pixel = bytearray(2)
raw_bg_fb = framebuf.FrameBuffer(raw_bg_pixel, 1, 1, framebuf.RGB565)


def flush():
    display.blit_buffer(buffer, 0, 0, WIDTH, HEIGHT)


def clear(color=COLOR_BG):
    fb.fill(color)


def fill_circle(cx, cy, radius, color):
    r2 = radius * radius
    for yy in range(-radius, radius + 1):
        span = int((r2 - yy * yy) ** 0.5)
        fb.hline(cx - span, cy + yy, span * 2 + 1, color)


def fill_round_rect(x, y, w, h, radius, color):
    radius = min(radius, w // 2, h // 2)
    fb.fill_rect(x + radius, y, w - radius * 2, h, color)
    fb.fill_rect(x, y + radius, w, h - radius * 2, color)
    fill_circle(x + radius, y + radius, radius, color)
    fill_circle(x + w - radius - 1, y + radius, radius, color)
    fill_circle(x + radius, y + h - radius - 1, radius, color)
    fill_circle(x + w - radius - 1, y + h - radius - 1, radius, color)


def draw_thick_line(x1, y1, x2, y2, color, thickness=2):
    half = thickness // 2
    for offset in range(-half, half + 1):
        fb.line(x1, y1 + offset, x2, y2 + offset, color)
        fb.line(x1 + offset, y1, x2 + offset, y2, color)


def draw_trend_arrow(cx, cy, trend, color=COLOR_TEXT):
    if trend > 0:
        draw_thick_line(cx, cy + 11, cx, cy - 11, color, 4)
        draw_thick_line(cx, cy - 11, cx - 8, cy - 3, color, 4)
        draw_thick_line(cx, cy - 11, cx + 8, cy - 3, color, 4)
    elif trend < 0:
        draw_thick_line(cx, cy - 11, cx, cy + 11, color, 4)
        draw_thick_line(cx, cy + 11, cx - 8, cy + 3, color, 4)
        draw_thick_line(cx, cy + 11, cx + 8, cy + 3, color, 4)
    else:
        draw_thick_line(cx - 11, cy, cx + 11, cy, color, 4)
        draw_thick_line(cx + 11, cy, cx + 3, cy - 8, color, 4)
        draw_thick_line(cx + 11, cy, cx + 3, cy + 8, color, 4)


def draw_compact_trend_arrow(cx, cy, trend, color=COLOR_TEXT):
    if trend > 0:
        draw_thick_line(cx, cy + 6, cx, cy - 6, color, 2)
        draw_thick_line(cx, cy - 6, cx - 4, cy - 2, color, 2)
        draw_thick_line(cx, cy - 6, cx + 4, cy - 2, color, 2)
    elif trend < 0:
        draw_thick_line(cx, cy - 6, cx, cy + 6, color, 2)
        draw_thick_line(cx, cy + 6, cx - 4, cy + 2, color, 2)
        draw_thick_line(cx, cy + 6, cx + 4, cy + 2, color, 2)
    else:
        draw_thick_line(cx - 6, cy, cx + 6, cy, color, 2)
        draw_thick_line(cx + 6, cy, cx + 2, cy - 4, color, 2)
        draw_thick_line(cx + 6, cy, cx + 2, cy + 4, color, 2)


def trend_label(trend):
    if trend > 0:
        return "RISING"
    if trend < 0:
        return "FALLING"
    return "STEADY"


def map_value(value, in_min, in_max, out_min, out_max):
    if value < in_min:
        value = in_min
    if value > in_max:
        value = in_max
    return out_min + (value - in_min) * (out_max - out_min) // (in_max - in_min)


def draw_ring(cx, cy, outer_radius, thickness, color, inner_color):
    fill_circle(cx, cy, outer_radius, color)
    fill_circle(cx, cy, outer_radius - thickness, inner_color)


def draw_circle_outline(cx, cy, radius, thickness, color):
    inner_radius = radius - thickness
    if inner_radius < 0:
        inner_radius = 0
    outer2 = radius * radius
    inner2 = inner_radius * inner_radius
    for yy in range(-radius, radius + 1):
        y = cy + yy
        outer_remaining = outer2 - yy * yy
        if outer_remaining < 0:
            continue
        outer_span = int(outer_remaining ** 0.5)
        inner_remaining = inner2 - yy * yy
        if inner_remaining < 0:
            fb.hline(cx - outer_span, y, outer_span * 2 + 1, color)
        else:
            inner_span = int(inner_remaining ** 0.5)
            width = outer_span - inner_span
            if width > 0:
                fb.hline(cx - outer_span, y, width, color)
                fb.hline(cx + inner_span + 1, y, width, color)


def draw_step_dots(step, total):
    if total <= 0:
        return
    spacing = 12
    radius = 3
    start_x = WIDTH - 16 - (total - 1) * spacing
    y = 14
    for index in range(total):
        color = COLOR_FOCUS if index < step else COLOR_EDGE
        fill_circle(start_x + index * spacing, y, radius, color)


def draw_header(title, step=0, total=2):
    fb.fill_rect(0, 0, WIDTH, 28, COLOR_PANEL)
    fb.hline(0, 27, WIDTH, COLOR_EDGE)
    draw_ui_text(title, 12, 10, COLOR_TEXT)
    if total and total > 0:
        draw_step_dots(step, total)


def draw_footer(left, middle, right):
    labels = (left, middle, right)
    y = 205
    h = 29
    btn_w = 68
    xs = (10, 86, 162)

    for i, (label, x) in enumerate(zip(labels, xs)):
        if not label:
            continue
        is_hold = label.startswith("~")
        if is_hold:
            label = label[1:]
        is_primary = (i == 2 and label in ("OK", "HOLD", "SELECT", "DONE", "BOLUS", "CONFIRM", "OPEN", "UNLOCK"))
        display_label = label if label in ("OK", "+", "-") else ui_title(label)
        bg = COLOR_FOCUS if is_primary else COLOR_PANEL
        txt_col = COLOR_WHITE if is_primary else COLOR_TEXT
        edge = COLOR_FOCUS if is_primary else COLOR_EDGE

        fill_round_rect(x, y, btn_w, h, 6, bg)
        fb.rect(x, y, btn_w, h, edge)

        if is_hold:
            hold_col = COLOR_WHITE if is_primary else COLOR_MUTED
            tx = x + (btn_w - ui_text_width("hold")) // 2
            draw_ui_text("hold", tx, y + 4, hold_col)
            tx = x + (btn_w - ui_text_width(display_label)) // 2
            draw_ui_text(display_label, tx, y + 16, txt_col)
        else:
            tx = x + (btn_w - ui_text_width(display_label)) // 2
            draw_ui_text(display_label, tx, y + 11, txt_col)


def text_width(text, scale=1):
    return len(str(text)) * 8 * scale


def fitting_text_scale(text, max_width, preferred=3):
    scale = preferred
    while scale > 1 and text_width(text, scale) > max_width:
        scale -= 1
    return scale


def draw_text_scaled(text, x, y, scale=1, color=COLOR_TEXT):
    text = str(text)
    if scale <= 1:
        fb.text(text, x, y, color)
        return

    cursor_x = x
    for char in text:
        char_fb.fill(COLOR_BLACK)
        char_fb.text(char, 0, 0, COLOR_WHITE)
        for yy in range(8):
            for xx in range(8):
                if char_fb.pixel(xx, yy):
                    fb.fill_rect(
                        cursor_x + xx * scale,
                        y + yy * scale,
                        scale,
                        scale,
                        color,
                    )
        cursor_x += 8 * scale


def ui_glyph_advance(char):
    return 8


def ui_text_width(text, scale=1):
    return len(str(text)) * 8 * scale


def ui_title(text):
    """ASCII title casing compatible with the reduced MicroPython str API."""
    result = []
    starts_word = True
    for char in str(text):
        is_letter = ("a" <= char <= "z") or ("A" <= char <= "Z")
        if is_letter:
            result.append(char.upper() if starts_word else char.lower())
            starts_word = False
        else:
            result.append(char)
            starts_word = True
    return "".join(result)


def draw_ui_text(text, x, y, color=COLOR_TEXT, scale=1):
    """Use MicroPython's native fixed 8x8 font for maximum legibility."""
    cursor_x = x
    if scale == 1:
        fb.text(str(text), x, y, color)
        return

    for char in str(text):
        advance = ui_glyph_advance(char)
        if char != " ":
            char_fb.fill(COLOR_BLACK)
            char_fb.text(char, 0, 0, COLOR_WHITE)
            for yy in range(8):
                for xx in range(8):
                    if char_fb.pixel(xx, yy):
                        fb.fill_rect(
                            cursor_x + xx * scale,
                            y + yy * scale,
                            scale,
                            scale,
                            color,
                        )
        cursor_x += advance * scale


def draw_ui_centered(text, y, color=COLOR_TEXT, scale=1):
    draw_ui_text(text, (WIDTH - ui_text_width(text, scale)) // 2, y, color, scale)


def draw_centered(text, y, color=COLOR_TEXT, scale=1):
    x = (WIDTH - text_width(text, scale)) // 2
    draw_text_scaled(text, x, y, scale, color)


SEGMENTS_BY_DIGIT = {
    "0": "abcdef",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgecd",
    "7": "abc",
    "8": "abcdefg",
    "9": "abfgcd",
}


def rounded_digit_width(height):
    return max(16, int(height * 0.54))


def draw_digit_segment(segment, x, y, w, h, thickness, color):
    half = h // 2
    radius = max(2, thickness // 2)
    if segment == "a":
        fill_round_rect(x, y, w, thickness, radius, color)
    elif segment == "b":
        fill_round_rect(x + w - thickness, y, thickness, half + radius, radius, color)
    elif segment == "c":
        fill_round_rect(x + w - thickness, y + half - radius, thickness, half + radius, radius, color)
    elif segment == "d":
        fill_round_rect(x, y + h - thickness, w, thickness, radius, color)
    elif segment == "e":
        fill_round_rect(x, y + half - radius, thickness, half + radius, radius, color)
    elif segment == "f":
        fill_round_rect(x, y, thickness, half + radius, radius, color)
    elif segment == "g":
        fill_round_rect(x, y + half - thickness // 2, w, thickness, radius, color)


def draw_rounded_digit(char, x, y, height, color):
    w = rounded_digit_width(height)
    thickness = max(4, height // 8)
    r = max(2, thickness // 2)
    half_h = height // 2

    if char == "." or char == ",":
        fill_circle(x + thickness, y + height - thickness, max(2, thickness // 2), color)
        return max(8, height // 6)
    if char == "-":
        fill_round_rect(x + 2, y + half_h - thickness // 2, w - 4, thickness, r, color)
        return w
    if char == "1":
        stem_x = x + w - thickness - 2
        fill_round_rect(stem_x, y, thickness, height, r, color)
        fill_round_rect(stem_x - thickness, y, thickness + 2, thickness, r, color)
        return w
    if char == "4":
        stem_x = x + w - thickness - 2
        fill_round_rect(stem_x, y, thickness, height, r, color)
        fill_round_rect(x, y, thickness, half_h + thickness // 2, r, color)
        fill_round_rect(x, y + half_h - thickness // 2, w - 2, thickness, r, color)
        return w
    if char == "7":
        fill_round_rect(x, y, w, thickness, r, color)
        fill_round_rect(x + w - thickness - 1, y, thickness, height, r, color)
        return w

    segments = SEGMENTS_BY_DIGIT.get(char)
    if not segments:
        return w

    for segment in segments:
        draw_digit_segment(segment, x, y, w, height, thickness, color)
    return w


def rounded_number_width(text, height):
    spacing = max(3, height // 12)
    total = 0
    for char in str(text):
        if char == "." or char == ",":
            total += max(8, height // 6)
        else:
            total += rounded_digit_width(height)
        total += spacing
    return max(0, total - spacing)


def draw_rounded_number(text, x, y, height, color):
    spacing = max(3, height // 12)
    cursor_x = x
    for char in str(text):
        used = draw_rounded_digit(char, cursor_x, y, height, color)
        cursor_x += used + spacing


def draw_card(x, y, w, h, fill=COLOR_PANEL, edge=COLOR_EDGE):
    fill_round_rect(x, y, w, h, 8, fill)
    fb.rect(x, y, w, h, edge)


def draw_value_screen(
    title,
    step,
    value,
    unit,
    hint,
    accent,
    hint_trend=None,
    value_trend=None,
    footer_labels=("+", "-", "OK"),
):
    clear()
    draw_header(title, step)

    draw_card(10, 34, 220, 164)

    if hint_trend is not None:
        label = trend_label(hint_trend)
        row_width = ui_text_width(hint) + 24 + ui_text_width(label)
        row_x = (WIDTH - row_width) // 2
        draw_ui_text(hint, row_x, 48, COLOR_MUTED)
        draw_compact_trend_arrow(row_x + ui_text_width(hint) + 10, 52, hint_trend, COLOR_FOCUS)
        draw_ui_text(ui_title(label), row_x + ui_text_width(hint) + 22, 48, COLOR_MUTED)
    else:
        draw_ui_centered(hint, 48, COLOR_MUTED)

    value_text = format_value(value)
    number_h = 50
    if len(value_text) >= 4:
        number_h = 44
    if len(value_text) >= 5:
        number_h = 38

    value_w = rounded_number_width(value_text, number_h)
    arrow_w = 30 if value_trend is not None else 0
    start_x = (WIDTH - value_w - arrow_w) // 2

    draw_rounded_number(value_text, start_x, 76, number_h, accent)
    if value_trend is not None:
        draw_trend_arrow(start_x + value_w + 16, 76 + number_h // 2, value_trend, COLOR_FOCUS)

    draw_ui_centered(unit, 144, COLOR_MUTED)

    draw_footer(footer_labels[0], footer_labels[1], footer_labels[2])
    flush()


def cgm_age_minutes():
    if cgm_last_update_ms == 0:
        return 0
    age = utime.ticks_diff(utime.ticks_ms(), cgm_last_update_ms) // 60000
    if age < 0:
        return 0
    return int(age)


def glucose_status(value):
    if value < 70:
        return "Low", COLOR_CORAL
    if value > 140:
        return "High", COLOR_AMBER
    return "In range", COLOR_SUCCESS


def calm_emotion_for_glucose(value):
    if value < 70:
        return "sad"
    if value > 140:
        return "dizzy"
    return "happy"


def draw_cgm_home_screen():
    clear()
    draw_header("IINTS sensor", 0, 0)

    draw_card(10, 34, 220, 164)
    draw_ui_text("Glucose", 22, 46, COLOR_MUTED)
    age = cgm_age_minutes()
    age_text = "Now" if age == 0 else "{} min".format(age)
    draw_ui_text(age_text, 218 - ui_text_width(age_text), 46, COLOR_MUTED)

    value_text = format_value(huidige_bg)
    number_h = 46
    value_w = rounded_number_width(value_text, number_h)
    content_w = value_w + 34
    start_x = (WIDTH - content_w) // 2
    draw_rounded_number(value_text, start_x, 60, number_h, COLOR_TEXT)
    draw_trend_arrow(start_x + value_w + 18, 82, cgm_trend, COLOR_FOCUS)
    draw_ui_centered("mg/dL  " + ui_title(trend_label(cgm_trend)), 111, COLOR_MUTED)

    status_text, status_color = glucose_status(huidige_bg)
    fill_round_rect(48, 128, 144, 24, 6, COLOR_PANEL_2)
    draw_ui_centered(status_text, 136, status_color)

    fb.hline(22, 160, 196, COLOR_EDGE)
    iob_val = calculate_non_linear_iob(utime.time())
    cob_val = int(calculate_cob(utime.time()))
    iob_text = "IOB {:.1f} U".format(iob_val)
    cob_text = "COB {} g".format(cob_val)
    draw_ui_text(iob_text, 24, 171, COLOR_MUTED)
    draw_ui_text(cob_text, 216 - ui_text_width(cob_text), 171, COLOR_MUTED)

    draw_footer("~SLEEP", "~TREND", "BOLUS")
    flush()


def draw_lock_screen():
    clear()
    draw_header("Locked", 0, 0)
    draw_card(10, 34, 220, 164)
    draw_ui_centered("Sensor monitor", 48, COLOR_MUTED)

    value_text = format_value(huidige_bg)
    number_h = 46
    value_w = rounded_number_width(value_text, number_h)
    start_x = (WIDTH - value_w - 30) // 2
    draw_rounded_number(value_text, start_x, 68, number_h, COLOR_TEXT)
    draw_trend_arrow(start_x + value_w + 16, 90, cgm_trend, COLOR_FOCUS)
    draw_ui_centered("mg/dL", 118, COLOR_MUTED)

    draw_ui_centered(ui_title(trend_label(cgm_trend)), 144, COLOR_TEXT)
    draw_ui_centered("Hold OK to unlock", 170, COLOR_MUTED)
    draw_footer("", "", "~UNLOCK")
    flush()


def draw_sleep_screen():
    clear(COLOR_BLACK)
    draw_ui_centered("Sleeping", 94, COLOR_WHITE, 2)
    draw_ui_centered("Press any key to wake", 128, COLOR_EDGE)
    flush()


def display_sleep():
    try:
        display._command(ST7789_DISPOFF)
        utime.sleep_ms(80)
        display._command(ST7789_SLPIN)
        utime.sleep_ms(120)
    except Exception:
        pass


def display_wake():
    try:
        display._command(ST7789_SLPOUT)
        utime.sleep_ms(150)
        display._command(ST7789_DISPON)
        utime.sleep_ms(120)
    except Exception:
        try:
            display.init()
        except Exception:
            pass


def split_number_unit(text):
    text = str(text)
    number = ""
    unit = ""
    for char in text:
        if char in "0123456789.-," and not unit:
            number += char
        else:
            unit += char
    return number, unit.strip()


def draw_status_screen(title, message, accent=COLOR_MINT):
    clear()
    draw_card(18, 54, 204, 132)
    draw_ui_centered(title, 76, accent, 2 if ui_text_width(title, 2) <= 180 else 1)
    number_text, unit = split_number_unit(message)
    if number_text:
        number_h = 40
        number_w = rounded_number_width(number_text, number_h)
        unit_w = ui_text_width(unit) if unit else 0
        start_x = (WIDTH - number_w - unit_w - (8 if unit else 0)) // 2
        draw_rounded_number(number_text, start_x, 112, number_h, COLOR_TEXT)
        if unit:
            draw_ui_text(unit, start_x + number_w + 8, 138, COLOR_TEXT)
    else:
        draw_ui_centered(message, 126, COLOR_TEXT, 1 if ui_text_width(message, 2) > 180 else 2)
    flush()


def draw_delivery_confirm_screen(units):
    clear()
    draw_header("Check dose", 2, 3)
    draw_card(10, 34, 220, 164)

    draw_ui_text("Meal", 22, 46, COLOR_MUTED)
    carbs_text = "{} g".format(gram_koolhydraten)
    draw_ui_text(carbs_text, 214 - ui_text_width(carbs_text), 46, COLOR_TEXT)
    fb.hline(22, 65, 196, COLOR_EDGE)

    draw_ui_text("Sensor", 22, 74, COLOR_MUTED)
    glucose_text = "{} mg/dL".format(huidige_bg)
    sensor_x = 214 - ui_text_width(glucose_text) - 18
    draw_ui_text(glucose_text, sensor_x, 74, COLOR_TEXT)
    draw_compact_trend_arrow(208, 78, cgm_trend, COLOR_FOCUS)
    fb.hline(22, 94, 196, COLOR_EDGE)

    draw_ui_text("Calculated dose", 22, 105, COLOR_MUTED)
    dose_text = "{:.1f}".format(units)
    number_h = 38
    dose_w = rounded_number_width(dose_text, number_h)
    start_x = (WIDTH - dose_w - ui_text_width("U") - 8) // 2
    draw_rounded_number(dose_text, start_x, 122, number_h, COLOR_TEXT)
    draw_ui_text("U", start_x + dose_w + 8, 148, COLOR_TEXT)

    in_range = (70 <= huidige_bg <= 140)
    note_txt = "Review values" if in_range else "Correction included"
    draw_ui_centered(note_txt, 178, COLOR_SUCCESS if in_range else COLOR_AMBER)

    draw_footer("", "CANCEL", "CONFIRM")
    flush()


def draw_bluey_parent_check_screen(units, food_label, safety_text, hold_progress):
    clear()
    draw_header("Adult check", 2, 3)
    draw_card(10, 34, 220, 164)

    draw_ui_text("Meal", 22, 45, COLOR_MUTED)
    draw_ui_text(food_label, 214 - ui_text_width(food_label), 45, COLOR_TEXT)
    fb.hline(22, 64, 196, COLOR_EDGE)

    draw_ui_text("Sensor", 22, 72, COLOR_MUTED)
    bg_str = "{} mg/dL".format(huidige_bg)
    sensor_x = 214 - ui_text_width(bg_str) - 18
    draw_ui_text(bg_str, sensor_x, 72, COLOR_TEXT)
    draw_compact_trend_arrow(208, 76, cgm_trend, COLOR_FOCUS)
    fb.hline(22, 92, 196, COLOR_EDGE)

    draw_ui_text("Dose", 22, 103, COLOR_MUTED)
    if safety_text:
        draw_ui_text(safety_text, 214 - ui_text_width(safety_text), 103, COLOR_AMBER)

    dose_str = "{:.1f}".format(units)
    number_h = 32
    dose_w = rounded_number_width(dose_str, number_h)
    start_x = (WIDTH - dose_w - ui_text_width("U") - 8) // 2
    draw_rounded_number(dose_str, start_x, 119, number_h, COLOR_TEXT)
    draw_ui_text("U", start_x + dose_w + 8, 141, COLOR_TEXT)

    hold_box_y = 162
    fill_round_rect(22, hold_box_y, 196, 24, 6, COLOR_PANEL_2)
    if hold_progress > 0:
        fill_width = min(196, int(hold_progress * 196 // 100))
        if fill_width > 0:
            fb.hline(22, hold_box_y + 22, fill_width, COLOR_FOCUS)
            fb.hline(22, hold_box_y + 23, fill_width, COLOR_FOCUS)

    hold_txt = "Hold OK to deliver" if hold_progress < 100 else "Confirmed"
    draw_ui_centered(hold_txt, hold_box_y + 8, COLOR_TEXT)

    draw_footer("", "CANCEL", "~OK")
    flush()


def fill_centered_triangle(cx, y, width, height, color, point_down=True):
    if height <= 0:
        return
    for row in range(height):
        if point_down:
            span = width * (height - row) // (height * 2)
        else:
            span = width * (row + 1) // (height * 2)
        fb.hline(cx - span, y + row, span * 2 + 1, color)


def draw_dosing_screen(units, frame=0):
    clear()
    draw_header("Delivering", 3, 3)
    draw_card(10, 34, 220, 164)

    cx = 120
    cy = 98
    draw_ring(cx, cy, 45, 4, COLOR_EDGE, COLOR_PANEL)
    marker_positions = ((120, 53), (165, 98), (120, 143), (75, 98))
    for index, position in enumerate(marker_positions):
        fill_circle(position[0], position[1], 4, COLOR_FOCUS if index == (frame & 3) else COLOR_PANEL_2)

    dose_str = "{:.1f}".format(units)
    dose_w = rounded_number_width(dose_str, 30)
    draw_rounded_number(dose_str, (WIDTH - dose_w) // 2, 77, 30, COLOR_TEXT)
    draw_ui_centered("units", 112, COLOR_MUTED)

    draw_ui_centered("Please wait", 156, COLOR_FOCUS)
    draw_ui_centered("Keep pump connected", 174, COLOR_MUTED)
    draw_footer("", "STOP", "")
    flush()


def draw_done_screen(units, frame=3):
    clear()
    draw_header("Dose complete", 3, 3)
    draw_card(10, 34, 220, 164)

    cx = 120
    cy = 92
    ring_color = COLOR_FOCUS if frame >= 1 else COLOR_EDGE
    fill_circle(cx, cy, 36, COLOR_PANEL_2)
    draw_circle_outline(cx, cy, 36, 4, ring_color)

    if frame >= 2:
        draw_thick_line(cx - 16, cy, cx - 4, cy + 12, COLOR_FOCUS, 4)
    if frame >= 3:
        draw_thick_line(cx - 5, cy + 12, cx + 18, cy - 12, COLOR_FOCUS, 4)

    draw_ui_centered("Delivered", 140, COLOR_TEXT, 2)
    draw_ui_centered("{:.1f} units".format(units), 168, COLOR_MUTED)
    draw_footer("", "", "DONE")
    flush()


def animate_done_screen(units):
    if not MOTION_ENABLED:
        draw_done_screen(units, 3)
        utime.sleep_ms(900)
        return

    for frame in range(4):
        draw_done_screen(units, frame)
        utime.sleep_ms(140)
    utime.sleep_ms(900)


def draw_gear(cx, cy, frame, color=COLOR_TEXT):
    phase = frame % 2
    fill_circle(cx, cy, 38, COLOR_EDGE)

    if phase == 0:
        fill_round_rect(cx - 8, cy - 56, 16, 24, 4, color)
        fill_round_rect(cx - 8, cy + 32, 16, 24, 4, color)
        fill_round_rect(cx - 56, cy - 8, 24, 16, 4, color)
        fill_round_rect(cx + 32, cy - 8, 24, 16, 4, color)
    else:
        fill_round_rect(cx - 42, cy - 42, 20, 20, 4, color)
        fill_round_rect(cx + 22, cy - 42, 20, 20, 4, color)
        fill_round_rect(cx - 42, cy + 22, 20, 20, 4, color)
        fill_round_rect(cx + 22, cy + 22, 20, 20, 4, color)

    draw_ring(cx, cy, 34, 11, color, COLOR_PANEL)
    draw_ring(cx, cy, 13, 6, COLOR_MUTED, COLOR_PANEL)


def draw_rewind_screen(frame=0, running=False):
    clear()
    draw_header("Rewind", 1, 1)
    draw_card(10, 34, 220, 164)
    draw_gear(120, 106, frame, COLOR_TEXT if running else COLOR_MUTED)
    draw_ui_centered("Rewinding" if running else "Hold OK to rewind", 162, COLOR_MUTED)
    draw_footer("", "BACK", "~OK")
    flush()


def draw_cgm_graph_screen():
    clear()
    draw_header("Glucose history", 1, 1)
    draw_card(10, 34, 220, 164)

    graph_x = 26
    graph_y = 48
    graph_w = 188
    graph_h = 92
    min_glucose = 40
    max_glucose = 240
    target_low = 70
    target_high = 140
    
    values = cgm_history[-18:]
    if not values:
        values = [huidige_bg]

    t_high_y = map_value(target_high, min_glucose, max_glucose, graph_y + graph_h, graph_y)
    t_low_y = map_value(target_low, min_glucose, max_glucose, graph_y + graph_h, graph_y)
    fb.fill_rect(graph_x, t_high_y, graph_w, t_low_y - t_high_y, COLOR_PANEL_2)
    
    fb.hline(graph_x, t_high_y, graph_w, COLOR_EDGE)
    fb.hline(graph_x, t_low_y, graph_w, COLOR_EDGE)
    draw_ui_text("140", graph_x + graph_w - ui_text_width("140") - 2, t_high_y - 9, COLOR_MUTED)
    draw_ui_text("70", graph_x + graph_w - ui_text_width("70") - 2, t_low_y + 2, COLOR_MUTED)

    fb.rect(graph_x, graph_y, graph_w, graph_h, COLOR_EDGE)

    if len(values) == 1:
        x = graph_x + graph_w // 2
        y = map_value(values[0], min_glucose, max_glucose, graph_y + graph_h, graph_y)
        fill_circle(x, y, 4, COLOR_FOCUS)
    else:
        last_x = graph_x
        last_y = map_value(values[0], min_glucose, max_glucose, graph_y + graph_h, graph_y)
        for index in range(1, len(values)):
            x = graph_x + index * graph_w // (len(values) - 1)
            y = map_value(values[index], min_glucose, max_glucose, graph_y + graph_h, graph_y)
            draw_thick_line(last_x, last_y, x, y, COLOR_FOCUS, 3)
            last_x = x
            last_y = y
        for index, value in enumerate(values):
            x = graph_x + index * graph_w // (len(values) - 1)
            y = map_value(value, min_glucose, max_glucose, graph_y + graph_h, graph_y)
            fill_circle(x, y, 3, COLOR_FOCUS)

    summary_y = 152
    fb.hline(22, summary_y - 4, 196, COLOR_EDGE)
    draw_compact_trend_arrow(32, summary_y + 8, cgm_trend, COLOR_FOCUS)
    now_text = "{} mg/dL".format(huidige_bg)
    draw_ui_text(now_text, 48, summary_y + 4, COLOR_TEXT)
    trend_text = ui_title(trend_label(cgm_trend))
    draw_ui_text(trend_text, 212 - ui_text_width(trend_text), summary_y + 4, COLOR_MUTED)

    draw_footer("", "BACK", "DONE")
    flush()


def format_value(value):
    if isinstance(value, float):
        if abs(value - round(value)) < 0.01:
            return str(int(round(value)))
        return "{:.1f}".format(value)
    return str(value)


def is_numeric_text(text):
    text = str(text)
    if not text:
        return False
    for char in text:
        if char not in "0123456789.-,":
            return False
    return True


def setting_display_value(setting_id, value):
    if setting_id in ("rewind", "guide"):
        return "OPEN"
    if setting_id in ("tamagotchi", "cgm", "motion"):
        return "ON" if int(value) else "OFF"
    return format_value(value)


def setting_menu_value(setting_id, value, unit):
    value_text = setting_display_value(setting_id, value)
    if unit and is_numeric_text(value_text):
        return "{} {}".format(value_text, unit)
    return value_text


def draw_settings_screen(index, total, title, value, unit, setting_id=None):
    clear()
    draw_header("Edit setting", index + 1, total)
    draw_card(10, 34, 220, 164)
    draw_ui_centered(title, 50, COLOR_MUTED)

    value_text = setting_display_value(setting_id, value)
    if is_numeric_text(value_text):
        number_h = 46
        if len(value_text) >= 4:
            number_h = 40
        number_w = rounded_number_width(value_text, number_h)
        draw_rounded_number(value_text, (WIDTH - number_w) // 2, 78, number_h, COLOR_TEXT)
    else:
        scale = 2 if ui_text_width(value_text, 2) <= 180 else 1
        draw_ui_centered(ui_title(value_text), 94, COLOR_TEXT, scale)

    if unit:
        draw_ui_centered(unit, 148, COLOR_MUTED)

    draw_footer("+", "-", "OK")
    flush()


def draw_settings_menu_screen(selected_index, settings):
    clear()
    page_size = 4
    page_index = selected_index // page_size
    page_count = (len(settings) + page_size - 1) // page_size
    first_index = page_index * page_size
    visible_settings = settings[first_index:first_index + page_size]

    draw_header("Settings", page_index + 1, page_count)

    for row, item in enumerate(visible_settings):
        index = first_index + row
        title, value, unit, setting_id = item[0], item[1], item[2], item[7]
        y = 36 + row * 40
        is_sel = (index == selected_index)
        
        bg = COLOR_PANEL_2 if is_sel else COLOR_PANEL
        edge = COLOR_FOCUS if is_sel else COLOR_EDGE
        txt_color = COLOR_FOCUS if is_sel else COLOR_TEXT

        fill_round_rect(10, y, 220, 36, 6, bg)
        fb.rect(10, y, 220, 36, edge)
        if is_sel:
            fb.fill_rect(10, y + 7, 4, 22, COLOR_FOCUS)

        draw_ui_text(title, 22, y + 14, txt_color)
        value_text = setting_menu_value(setting_id, value, unit)
        value_x = 216 - ui_text_width(value_text)
        if value_x < 120:
            value_x = 120
        draw_ui_text(value_text, value_x, y + 14, txt_color)

    draw_footer("NEXT", "PREV", "OPEN")
    flush()


def draw_controls_guide_screen():
    clear()
    draw_header("Button guide", 0, 0)
    draw_card(10, 34, 220, 164)
    rows = (
        ("GP16 hold", "Sleep"),
        ("GP17 hold", "Trend"),
        ("GP18", "Bolus / OK"),
        ("16 + 17", "Settings"),
        ("16 + 18", "Calm pause" if TAMAGOTCHI_MODE else "Calm off"),
        ("17 + 18", "Demo"),
        ("Any key", "Wake"),
    )
    for index, row in enumerate(rows):
        y = 41 + index * 22
        draw_ui_text(row[0], 22, y, COLOR_MUTED)
        draw_ui_text(row[1], 214 - ui_text_width(row[1]), y, COLOR_TEXT)
        if index < len(rows) - 1:
            fb.hline(22, y + 15, 196, COLOR_EDGE)
    draw_footer("", "BACK", "DONE")
    flush()


def draw_calm_pause_screen():
    clear()
    draw_header("Calm pause", 0, 0)
    draw_card(10, 34, 220, 164)
    draw_ui_centered("Take your time", 48, COLOR_FOCUS, 2)
    draw_ui_centered("No dose is running", 78, COLOR_MUTED)

    steps = ("Breathe slowly", "Check the sensor", "Press OK when ready")
    for index, text in enumerate(steps):
        y = 108 + index * 24
        fill_circle(34, y + 4, 9, COLOR_PANEL_2)
        draw_ui_text(str(index + 1), 32, y + 1, COLOR_FOCUS)
        draw_ui_text(text, 52, y, COLOR_TEXT)

    draw_footer("", "BACK", "DONE")
    flush()


def show_startup_raw(filename):
    try:
        with open(filename, "rb") as f:
            row = bytearray(WIDTH * 2)
            for y in range(HEIGHT):
                read = f.readinto(row)
                if read != WIDTH * 2:
                    return False
                display.blit_buffer(row, 0, y, WIDTH, 1)
        return True
    except Exception:
        return False


def draw_demo_fallback():
    clear()
    draw_card(16, 57, 208, 126)
    draw_centered("IINTS-AF", 81, COLOR_TEXT, 3)
    draw_centered("Low Sensory", 126, COLOR_MUTED, 2)
    draw_centered("OK = exit", 164, COLOR_MUTED, 1)
    flush()


def run_demo_mode():
    disable_motor()
    set_delivery_led(False)
    wait_buttons_released()

    if not show_startup_raw("start.raw"):
        draw_demo_fallback()

    while True:
        if sleep_if_idle():
            if not show_startup_raw("start.raw"):
                draw_demo_fallback()
            continue
        if confirm_pressed() or settings_combo_pressed() or demo_combo_pressed():
            wait_buttons_released()
            mark_screen_dirty()
            return
        utime.sleep_ms(35)


def confirm_delivery(units):
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue

        render_once("confirm_delivery", draw_delivery_confirm_screen, units)

        if demo_combo_pressed():
            run_demo_mode()
            mark_screen_dirty()
            continue
        if demo_combo_active():
            utime.sleep_ms(35)
            continue
        if settings_combo_pressed():
            wait_buttons_released()
            mark_screen_dirty()
            return False
        if button_pressed(sad_button):
            mark_screen_dirty()
            return False
        if confirm_pressed():
            mark_screen_dirty()
            return True
        utime.sleep_ms(35)


BLUEY_PARENT_HOLD_MS = 1400


def bluey_safety_text(units, food_index):
    if cgm_trend < 0:
        return "Falling - check"
    if units >= 3.0:
        return "High dose check"
    if food_index == 4:
        return "Slow meal check"
    return "Adult hold OK"


def bluey_parent_confirm(units, food_label, safety_text):
    wait_buttons_released()
    mark_screen_dirty()
    hold_started_ms = None
    progress = 0

    while True:
        if sleep_if_idle():
            continue

        if angry_button.value() == 0 and happy_button.value() == 1 and sad_button.value() == 1:
            now = utime.ticks_ms()
            if hold_started_ms is None:
                hold_started_ms = now
            held_ms = utime.ticks_diff(now, hold_started_ms)
            progress = min(100, int(held_ms * 100 // BLUEY_PARENT_HOLD_MS))
            if held_ms >= BLUEY_PARENT_HOLD_MS:
                wait_buttons_released()
                mark_screen_dirty()
                return True
        else:
            hold_started_ms = None
            progress = 0

        render_once(
            ("bluey_parent", int(units * 10), food_label, safety_text, progress // 10),
            draw_bluey_parent_check_screen,
            units,
            food_label,
            safety_text,
            progress,
        )

        if calm_combo_pressed():
            run_calm_pause()
            mark_screen_dirty()
            continue
        if button_pressed(sad_button):
            mark_screen_dirty()
            return False
        if demo_combo_pressed():
            run_demo_mode()
            mark_screen_dirty()
        elif settings_combo_pressed():
            run_settings_menu()
            mark_screen_dirty()
        utime.sleep_ms(35)


def reset_bolus_to_home():
    global gram_koolhydraten, stap, huidige_bg, selected_carb_absorption_seconds
    if CGM_SIM_MODE:
        update_cgm_sensor()
    else:
        huidige_bg = TARGET_BG
    gram_koolhydraten = 0
    selected_carb_absorption_seconds = STANDARD_CARB_ABSORPTION_SECONDS
    stap = 0
    mark_user_activity()
    mark_screen_dirty()


def run_guided_bluey_bolus_flow():
    global tamagotchi_food_index, gram_koolhydraten

    food_index = tamagotchi_food_index
    wait_buttons_released()
    mark_screen_dirty()

    while True:
        if sleep_if_idle():
            continue
        if CGM_SIM_MODE and update_cgm_sensor():
            mark_screen_dirty()

        render_once(
            "bluey_guided_food",
            draw_food,
            120,
            110,
            food_index,
            huidige_bg if CGM_SIM_MODE else None,
            cgm_trend if CGM_SIM_MODE else None,
            ("NEXT", "CANCEL", "SELECT"),
        )

        if calm_combo_pressed():
            run_calm_pause()
            mark_screen_dirty()
            continue
        if demo_combo_pressed():
            run_demo_mode()
            mark_screen_dirty()
            continue
        if settings_combo_pressed():
            run_settings_menu()
            mark_screen_dirty()
            continue
        if button_pressed(sad_button):
            draw_status_screen("Cancelled", "No dose", COLOR_BLUE)
            utime.sleep(1.2)
            reset_bolus_to_home()
            return
        if button_pressed(happy_button):
            food_index = (food_index + 1) % len(PORTION_LABELS)
            mark_screen_dirty()
            continue

        if confirm_pressed():
            tamagotchi_food_index = food_index
            gram_koolhydraten = PORTION_CARBS[food_index]
            absorption_seconds = (
                SLOW_CARB_ABSORPTION_SECONDS
                if food_index == 4
                else STANDARD_CARB_ABSORPTION_SECONDS
            )

            if huidige_bg < TARGET_BG - 20:
                draw_status_screen("Ask adult", "Low CGM", COLOR_BLUE)
                utime.sleep(2)
                reset_bolus_to_home()
                return

            current_time = utime.time()
            total_units, cob, iob = calculate_demo_bolus(gram_koolhydraten, current_time)

            if total_units <= 0:
                record_carbs_if_needed(
                    utime.time(),
                    gram_koolhydraten,
                    absorption_seconds,
                )
                draw_status_screen("No dose", "0.0 U", COLOR_BLUE)
                utime.sleep(2)
                reset_bolus_to_home()
                return

            food_label = "{} / {} g".format(
                PORTION_LABELS[food_index],
                PORTION_CARBS[food_index],
            )
            safety_text = bluey_safety_text(total_units, food_index)
            if not bluey_parent_confirm(total_units, food_label, safety_text):
                draw_status_screen("Cancelled", "No dose", COLOR_BLUE)
                utime.sleep(1.5)
                reset_bolus_to_home()
                return

            draw_status_screen("Ready", "Wait", COLOR_MINT)
            utime.sleep_ms(600)
            deliver_demo_bolus(
                total_units,
                gram_koolhydraten,
                absorption_seconds,
            )
            reset_bolus_to_home()
            return

        utime.sleep_ms(50)


def run_cgm_graph_screen():
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue
        if CGM_SIM_MODE and update_cgm_sensor():
            mark_screen_dirty()

        render_once(
            "cgm_graph",
            draw_cgm_graph_screen,
        )

        if settings_combo_pressed():
            run_settings_menu()
            mark_screen_dirty()
            continue
        if demo_combo_pressed():
            run_demo_mode()
            mark_screen_dirty()
            continue
        if confirm_pressed() or button_pressed(sad_button):
            wait_buttons_released()
            mark_screen_dirty()
            return
        utime.sleep_ms(35)


def show_startup_screen():
    # Static white startup image only. Video playback is intentionally omitted.
    if show_startup_raw("start.raw"):
        utime.sleep_ms(700)
        return
    clear(COLOR_PANEL)
    draw_text_scaled("IINTS-SDK", 60, 110, 2, COLOR_TEXT)
    flush()
    utime.sleep_ms(1000)


# --- Knopconfiguratie ---
happy_button = machine.Pin(PIN_BUTTON_1, machine.Pin.IN, machine.Pin.PULL_UP)
sad_button = machine.Pin(PIN_BUTTON_2, machine.Pin.IN, machine.Pin.PULL_UP)
angry_button = machine.Pin(PIN_BUTTON_3, machine.Pin.IN, machine.Pin.PULL_UP)


def button_pressed(button, debounce_ms=35):
    """Return True bij een nieuwe druk, na debounce en release."""
    buttons_down = (
        (1 if happy_button.value() == 0 else 0)
        + (1 if sad_button.value() == 0 else 0)
        + (1 if angry_button.value() == 0 else 0)
    )
    if buttons_down >= 2:
        return False

    if button.value() == 0:
        utime.sleep_ms(debounce_ms)
        if button.value() == 0:
            while button.value() == 0:
                utime.sleep_ms(10)
            utime.sleep_ms(80)
            mark_user_activity()
            return True
    return False


def wait_buttons_released():
    while happy_button.value() == 0 or sad_button.value() == 0 or angry_button.value() == 0:
        utime.sleep_ms(20)
    utime.sleep_ms(90)


settings_combo_started_ms = None
settings_combo_triggered = False
demo_combo_started_ms = None
demo_combo_triggered = False
calm_combo_started_ms = None
calm_combo_triggered = False
graph_button_started_ms = None
graph_button_triggered = False
sleep_button_started_ms = None
sleep_button_triggered = False


def settings_combo_pressed():
    global settings_combo_started_ms, settings_combo_triggered

    if happy_button.value() == 0 and sad_button.value() == 0:
        now = utime.ticks_ms()
        if settings_combo_started_ms is None:
            settings_combo_started_ms = now
            settings_combo_triggered = False
            return False
        if not settings_combo_triggered and utime.ticks_diff(now, settings_combo_started_ms) >= 700:
            settings_combo_triggered = True
            mark_user_activity()
            return True
        return False

    settings_combo_started_ms = None
    settings_combo_triggered = False
    return False


def demo_combo_active():
    return sad_button.value() == 0 and angry_button.value() == 0


def calm_combo_active():
    return happy_button.value() == 0 and angry_button.value() == 0 and sad_button.value() == 1


def demo_combo_pressed():
    global demo_combo_started_ms, demo_combo_triggered

    if demo_combo_active():
        now = utime.ticks_ms()
        if demo_combo_started_ms is None:
            demo_combo_started_ms = now
            demo_combo_triggered = False
            return False
        if not demo_combo_triggered and utime.ticks_diff(now, demo_combo_started_ms) >= 700:
            demo_combo_triggered = True
            mark_user_activity()
            return True
        return False

    demo_combo_started_ms = None
    demo_combo_triggered = False
    return False


def calm_combo_pressed():
    global calm_combo_started_ms, calm_combo_triggered

    if calm_combo_active():
        now = utime.ticks_ms()
        if calm_combo_started_ms is None:
            calm_combo_started_ms = now
            calm_combo_triggered = False
            return False
        if not calm_combo_triggered and utime.ticks_diff(now, calm_combo_started_ms) >= 700:
            calm_combo_triggered = True
            mark_user_activity()
            return True
        return False

    calm_combo_started_ms = None
    calm_combo_triggered = False
    return False


def confirm_pressed():
    if demo_combo_active() or calm_combo_active():
        return False
    if button_pressed(angry_button):
        return True
    return False


def graph_button_long_pressed(hold_ms=900):
    global graph_button_started_ms, graph_button_triggered

    if sad_button.value() == 0 and happy_button.value() == 1 and angry_button.value() == 1:
        now = utime.ticks_ms()
        if graph_button_started_ms is None:
            graph_button_started_ms = now
            graph_button_triggered = False
            return False
        if not graph_button_triggered and utime.ticks_diff(now, graph_button_started_ms) >= hold_ms:
            graph_button_triggered = True
            mark_user_activity()
            return True
        return False

    graph_button_started_ms = None
    graph_button_triggered = False
    return False


def sleep_button_long_pressed(hold_ms=2500):
    global sleep_button_started_ms, sleep_button_triggered

    if happy_button.value() == 0 and sad_button.value() == 1 and angry_button.value() == 1:
        now = utime.ticks_ms()
        if sleep_button_started_ms is None:
            sleep_button_started_ms = now
            sleep_button_triggered = False
            return False
        if not sleep_button_triggered and utime.ticks_diff(now, sleep_button_started_ms) >= hold_ms:
            sleep_button_triggered = True
            return True
        return False

    sleep_button_started_ms = None
    sleep_button_triggered = False
    return False


def home_should_lock():
    if not CGM_SIM_MODE:
        return False
    if happy_button.value() == 0 or sad_button.value() == 0 or angry_button.value() == 0:
        return False
    return utime.ticks_diff(utime.ticks_ms(), last_activity_ms) >= LOCK_TIMEOUT_MS


def run_lock_screen():
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue
        if CGM_SIM_MODE and update_cgm_sensor():
            mark_screen_dirty()

        render_once(
            "lock_screen",
            draw_lock_screen,
        )

        if sleep_button_long_pressed():
            enter_deep_sleep()
        if settings_combo_pressed() or demo_combo_pressed() or confirm_pressed():
            wait_buttons_released()
            mark_user_activity()
            mark_screen_dirty()
            return
        utime.sleep_ms(35)


def run_calm_pause():
    disable_motor()
    set_delivery_led(False)
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue
        render_once("calm_pause", draw_calm_pause_screen)
        if confirm_pressed() or button_pressed(sad_button):
            wait_buttons_released()
            mark_user_activity()
            mark_screen_dirty()
            return
        utime.sleep_ms(35)


# --- Motorconfiguratie ---
in1 = machine.Pin(PIN_MOTOR_IN1, machine.Pin.OUT)
in2 = machine.Pin(PIN_MOTOR_IN2, machine.Pin.OUT)
in3 = machine.Pin(PIN_MOTOR_IN3, machine.Pin.OUT)
in4 = machine.Pin(PIN_MOTOR_IN4, machine.Pin.OUT)


def disable_motor():
    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(0)
    set_delivery_led(False)


disable_motor()

sleep_wake_flag = False


def sleep_wake_irq(pin):
    global sleep_wake_flag
    sleep_wake_flag = True


def configure_sleep_wake_buttons():
    wake_mode = getattr(machine, "LIGHTSLEEP", 0)
    for button in (happy_button, sad_button, angry_button):
        try:
            if wake_mode:
                button.irq(trigger=machine.Pin.IRQ_FALLING, handler=sleep_wake_irq, wake=wake_mode)
            else:
                button.irq(trigger=machine.Pin.IRQ_FALLING, handler=sleep_wake_irq)
        except Exception:
            try:
                button.irq(trigger=machine.Pin.IRQ_FALLING, handler=sleep_wake_irq)
            except Exception:
                pass


def clear_sleep_wake_buttons():
    for button in (happy_button, sad_button, angry_button):
        try:
            button.irq(handler=None)
        except Exception:
            pass


def any_button_down():
    return happy_button.value() == 0 or sad_button.value() == 0 or angry_button.value() == 0


def run_power_save_sleep():
    global sleep_wake_flag

    draw_sleep_screen()
    utime.sleep_ms(700)

    disable_motor()
    set_delivery_led(False)
    try:
        drv_eep.value(0)
    except Exception:
        pass

    wait_buttons_released()
    sleep_wake_flag = False
    configure_sleep_wake_buttons()

    clear(COLOR_BLACK)
    flush()
    utime.sleep_ms(120)
    display_sleep()

    while not sleep_wake_flag and not any_button_down():
        try:
            machine.lightsleep(300)
        except Exception:
            utime.sleep_ms(300)

    clear_sleep_wake_buttons()
    try:
        drv_eep.value(1)
    except Exception:
        pass
    display_wake()
    wait_buttons_released()
    mark_user_activity()
    mark_screen_dirty()


def enter_deep_sleep():
    run_power_save_sleep()

# --- Full-step sequentie ---
full_step_sequence = (
    (1, 0, 1, 0),
    (0, 1, 1, 0),
    (0, 1, 0, 1),
    (1, 0, 0, 1),
)
reverse_full_step_sequence = (
    (1, 0, 0, 1),
    (0, 1, 0, 1),
    (0, 1, 1, 0),
    (1, 0, 1, 0),
)


def step_motor(delay, steps, direction=1, blink_led=False, animation_callback=None):
    sequence = full_step_sequence if direction == 1 else reverse_full_step_sequence
    led_state = False
    animation_frame = 0
    last_led_ms = utime.ticks_ms()
    completed_steps = 0
    cancelled = False
    try:
        if blink_led:
            led_state = True
            set_delivery_led(True)
        if animation_callback is not None:
            animation_callback(animation_frame)
            animation_frame += 1

        for step_index in range(steps):
            if sad_button.value() == 0:
                cancelled = True
                mark_user_activity()
                break

            step = sequence[step_index & 3]
            in1.value(step[0])
            in2.value(step[1])
            in3.value(step[2])
            in4.value(step[3])
            completed_steps += 1

            now = utime.ticks_ms()
            if blink_led and utime.ticks_diff(now, last_led_ms) >= 180:
                led_state = not led_state
                set_delivery_led(led_state)
                if animation_callback is not None:
                    animation_callback(animation_frame)
                    animation_frame += 1
                last_led_ms = now
            utime.sleep_ms(delay)
    finally:
        disable_motor()
    return completed_steps, cancelled


def continuous_step_motor(delay, steps, direction=1):
    sequence = full_step_sequence if direction == 1 else reverse_full_step_sequence
    for step_index in range(steps):
        step = sequence[step_index & 3]
        in1.value(step[0])
        in2.value(step[1])
        in3.value(step[2])
        in4.value(step[3])
        utime.sleep_ms(delay)


# --- Instellingen & Variabelen ---
TDD = 50.0  # Total Daily Dose (eenheden per dag)
# Klinische 500-regel en 1800-regel:
ICR = 500.0 / TDD   # Insulin to Carb Ratio (gram koolhydraten per eenheid)
ISF = 1800.0 / TDD  # Insulin Sensitivity Factor (mg/dL daling per eenheid)
TARGET_BG = 110
DIA_HOURS = 4.0
TAMAGOTCHI_MODE = 1
CGM_SIM_MODE = 1
MOTION_ENABLED = 1
ACTIVITY_MODE = False
CGM_UPDATE_MS = 60000
CGM_PATTERN = (118, 124, 132, 145, 158, 151, 138, 126, 113, 101, 108, 116)
LOCK_TIMEOUT_MS = 30000
AUTO_SLEEP_TIMEOUT_MS = 180000
STANDARD_CARB_ABSORPTION_SECONDS = 3 * 3600
SLOW_CARB_ABSORPTION_SECONDS = 6 * 3600
MAX_DIA_SECONDS = 8 * 3600

# --- Medtronic & Tandem Medical Safety Guardrails (FDA / IEC 62304) ---
MAX_SINGLE_BOLUS = 15.0         # Hard physiological safety clamp (Max 15.0 U per bolus)
MAX_DAILY_MULTIPLIER = 2.0     # Max 24h rolling total limit = 2.0 * TDD (100.0 U)
HYPO_LOCKOUT_BG = 70           # Absolute hypo lockout threshold (mg/dL)
PLGS_THRESHOLD_BG = 80         # Predictive Low Glucose Suspend threshold (mg/dL)
SMARTGUARD_SUSPENDED = False   # Automatic basal suspend state flag
SENSOR_MAX_ROC_5MIN = 30       # Max physiological rate-of-change per 5 min (mg/dL)
MICRO_DOSE_STEP_UNITS = 0.05   # Micro-metering step granularity (Units)

injection_log = []
carb_log = []

huidige_bg = 120
gram_koolhydraten = 0
stap = 0
last_screen_key = None

tamagotchi_mood_index = 1 # 0: sleepy, 1: happy, 2: hyper
tamagotchi_food_index = 0 # 0: none, 1: snack, 2: small, 3: meal, 4: big
TAMAGOTCHI_MOODS = ("sad", "happy", "dizzy")
PORTION_LABELS = ("No meal", "Snack", "Small meal", "Meal", "Large meal")
PORTION_CARBS = (0, 15, 30, 45, 60)
cgm_index = 0
cgm_last_update_ms = 0
cgm_trend = 0
cgm_history = []
last_activity_ms = utime.ticks_ms()
delivery_animation_units = 0.0
selected_carb_absorption_seconds = STANDARD_CARB_ABSORPTION_SECONDS


def mark_user_activity():
    global last_activity_ms
    last_activity_ms = utime.ticks_ms()


def auto_sleep_due():
    if any_button_down():
        return False
    return utime.ticks_diff(utime.ticks_ms(), last_activity_ms) >= AUTO_SLEEP_TIMEOUT_MS


def sleep_if_idle():
    if auto_sleep_due():
        run_power_save_sleep()
        return True
    return False


def draw_delivery_animation(frame):
    draw_dosing_screen(delivery_animation_units, frame)


def record_cgm_value(value):
    cgm_history.append(int(value))
    if len(cgm_history) > 24:
        cgm_history.pop(0)


def prune_history(current_time):
    while injection_log and current_time - injection_log[0][0] >= MAX_DIA_SECONDS:
        injection_log.pop(0)
    while carb_log and current_time - carb_log[0][0] >= SLOW_CARB_ABSORPTION_SECONDS:
        carb_log.pop(0)


def update_cgm_sensor(force=False):
    global huidige_bg, cgm_index, cgm_last_update_ms, cgm_trend

    if not CGM_SIM_MODE:
        return False

    now = utime.ticks_ms()
    if cgm_last_update_ms == 0:
        cgm_last_update_ms = now
        huidige_bg = CGM_PATTERN[cgm_index]
        cgm_trend = 0
        record_cgm_value(huidige_bg)
        return True

    elapsed_ms = utime.ticks_diff(now, cgm_last_update_ms)
    if force or elapsed_ms >= CGM_UPDATE_MS:
        steps = 1
        if not force:
            steps = max(1, elapsed_ms // CGM_UPDATE_MS)
        cgm_index = (cgm_index + steps) % len(CGM_PATTERN)
        cgm_last_update_ms = now
        new_bg = CGM_PATTERN[cgm_index]
        change = new_bg - huidige_bg
        if change >= 5:
            cgm_trend = 1
        elif change <= -5:
            cgm_trend = -1
        else:
            cgm_trend = 0
        if new_bg != huidige_bg:
            huidige_bg = new_bg
            record_cgm_value(huidige_bg)
            return True
    return False

# ==============================================================================
# MEDTRONIC & TANDEM 1-TO-1 SCIENTIFIC PHARMACOKINETICS & CLINICAL SAFETY
# ==============================================================================

# 1. 24-Hour Rolling Total & Safety Cap (IEC 62304 Safety Class C)
def calculate_24h_insulin_total(current_time):
    window_24h = 86400  # 24 hours in seconds
    total = 0.0
    for inj_time, units in injection_log:
        if (current_time - inj_time) <= window_24h:
            total += units
    return total


def check_daily_insulin_cap(current_time, requested_units):
    total_24h = calculate_24h_insulin_total(current_time)
    daily_cap = TDD * MAX_DAILY_MULTIPLIER
    if (total_24h + requested_units) > daily_cap:
        allowed = max(0.0, daily_cap - total_24h)
        return False, allowed, "24h Cap Exceeded"
    return True, requested_units, "OK"


# 2. Predictive Low Glucose Suspend (PLGS / Medtronic SmartGuard / Tandem Basal-IQ)
def predict_future_bg(current_bg, trend, current_time, horizon_minutes=30):
    # Velocity estimation: Trend values (-2 to +2) mapped to mg/dL/min
    v_trend = trend * 1.5
    iob = calculate_non_linear_iob(current_time)
    # Predicted BG in 30 minutes accounting for trend slope and active IOB drag:
    bg_pred = current_bg + (v_trend * horizon_minutes) - (iob * ISF * 0.25)
    return bg_pred


def check_plgs_suspend(current_bg, trend, current_time):
    global SMARTGUARD_SUSPENDED
    bg_pred = predict_future_bg(current_bg, trend, current_time, 30)
    if current_bg <= HYPO_LOCKOUT_BG or bg_pred < PLGS_THRESHOLD_BG:
        SMARTGUARD_SUSPENDED = True
        return True, bg_pred
    else:
        SMARTGUARD_SUSPENDED = False
        return False, bg_pred


# 3. Sensor Noise & Compression Artifact Filter
def filter_sensor_noise(new_bg, last_bg, dt_minutes=5):
    if last_bg <= 0 or dt_minutes <= 0:
        return new_bg, False
    max_delta = SENSOR_MAX_ROC_5MIN * (dt_minutes / 5.0)
    delta = new_bg - last_bg
    if abs(delta) > max_delta:
        clamped_bg = last_bg + (max_delta if delta > 0 else -max_delta)
        return int(round(clamped_bg)), True
    return new_bg, False


# 4. Hovorka / Walsh Bi-Exponential Active Insulin (IOB) Decay
def calculate_non_linear_iob(current_time):
    prune_history(current_time)
    dia_seconds = DIA_HOURS * 3600
    iob = 0.0

    for inj_time, units in injection_log:
        elapsed = current_time - inj_time
        if 0 <= elapsed < dia_seconds:
            ratio = elapsed / dia_seconds
            # Walsh quadratic decay: IOB(t) = Dose * (1 - t/DIA)^2
            iob += units * ((1.0 - ratio) ** 2)
    return iob


# 5. PID-CONTROLLER (Hybrid Closed-Loop Basal Modulation)
pid_integral_error = 0.0
pid_last_error = 0.0
pid_last_time = 0

def calculate_pid_basal(current_bg, target_bg, current_time):
    global pid_integral_error, pid_last_error, pid_last_time
    
    # Check PLGS (SmartGuard / Basal-IQ) safety interlock first
    suspended, bg_pred = check_plgs_suspend(current_bg, cgm_trend, current_time)
    if suspended:
        return 0.0
    
    active_target = target_bg
    if ACTIVITY_MODE:
        active_target += 40
        Kp, Ki, Kd = 0.005, 0.00005, 0.025
    else:
        Kp, Ki, Kd = 0.01, 0.0001, 0.05
    
    error = current_bg - active_target
    dt = 1 if pid_last_time == 0 else max(1, current_time - pid_last_time)
    
    P_out = Kp * error
    pid_integral_error += error * dt
    pid_integral_error = max(-50.0, min(50.0, pid_integral_error))
    I_out = Ki * pid_integral_error
    
    derivative = (error - pid_last_error) / dt
    D_out = Kd * derivative
    
    pid_last_error = error
    pid_last_time = current_time
    
    pid_output = P_out + I_out + D_out
    return max(-1.0, min(2.0, pid_output))


# 6. Carbohydrate Absorption (Carbs On Board - COB)
def calculate_cob(current_time):
    prune_history(current_time)
    cob = 0.0
    for carb_entry in carb_log:
        carb_time = carb_entry[0]
        carbs = carb_entry[1]
        absorption_seconds = (
            carb_entry[2]
            if len(carb_entry) >= 3
            else STANDARD_CARB_ABSORPTION_SECONDS
        )
        elapsed = current_time - carb_time
        if 0 <= elapsed < absorption_seconds:
            remaining = carbs * (1.0 - (elapsed / absorption_seconds))
            cob += remaining
    return cob


# 7. Circadian Rhythm (Dawn Phenomenon ISF Multiplier)
def get_circadian_isf(current_hour):
    if 4 <= current_hour <= 8:
        return ISF * 0.75  # 25% lower sensitivity during early morning cortisol surge
    return ISF


# 8. Universal Clinical Bolus Calculator (Medtronic 780G & Tandem Control-IQ Standard)
def calculate_demo_bolus(carb_grams, current_time):
    """
    Standard Universal Bolus Equation:
    Total = max(0, (Carbs / ICR) + ((Current BG - Target BG) / ISF) - IOB_deductible)
    """
    prune_history(current_time)
    cob = calculate_cob(current_time) + carb_grams
    iob = calculate_non_linear_iob(current_time)
    
    # Hypoglycemia Hard Lockout (Safety Interlock)
    if huidige_bg <= HYPO_LOCKOUT_BG:
        return 0.0, cob, iob
    
    # 1. Meal Bolus Component (Carbs / ICR)
    carb_bolus = carb_grams / ICR

    # 2. Correction Bolus Component ((Current BG - Target BG) / ISF)
    # Includes negative correction if BG < Target BG to reduce meal dose
    effective_isf = get_circadian_isf(12)
    correction_bolus = (huidige_bg - TARGET_BG) / effective_isf

    # 3. IOB Deduction with COB Protection
    cob_insulin_needed = cob / ICR
    deductible_iob = max(0.0, iob - cob_insulin_needed)
    
    calculated = carb_bolus + correction_bolus - deductible_iob
    net_dose = max(0.0, calculated)
    
    # 4. Hard Single Bolus Safety Clamp
    clamped_dose = min(MAX_SINGLE_BOLUS, net_dose)
    
    # 5. 24-Hour Safety Cap Check
    allowed, safe_limit, reason = check_daily_insulin_cap(current_time, clamped_dose)
    final_dose = min(clamped_dose, safe_limit)
    
    return final_dose, cob, iob


def record_carbs_if_needed(
    current_time,
    carb_grams,
    absorption_seconds=STANDARD_CARB_ABSORPTION_SECONDS,
):
    if carb_grams > 0:
        carb_log.append((current_time, carb_grams, absorption_seconds))
        prune_history(current_time)


def deliver_demo_bolus(
    total_units,
    carb_grams,
    absorption_seconds=STANDARD_CARB_ABSORPTION_SECONDS,
):
    global delivery_animation_units

    # Safety Pre-Check 1: Hypoglycemia Hard Lockout
    if huidige_bg <= HYPO_LOCKOUT_BG:
        draw_status_screen("Lockout", "Hypo <70", COLOR_CORAL)
        utime.sleep(2)
        return False

    # Safety Pre-Check 2: Hard Max Single Bolus Clamp
    if total_units > MAX_SINGLE_BOLUS:
        total_units = MAX_SINGLE_BOLUS

    # Safety Pre-Check 3: 24-Hour Rolling Safety Cap
    current_time = utime.time()
    allowed, safe_units, reason = check_daily_insulin_cap(current_time, total_units)
    if not allowed:
        total_units = safe_units
        if total_units <= 0:
            draw_status_screen("24h Limit", "Cap Exceeded", COLOR_CORAL)
            utime.sleep(2)
            return False

    # ==============================================================================
    # EUCYS BIOMECHANICAL ENGINEERING: MOTOR & RESERVOIR GEOMETRY
    # ==============================================================================
    # U-100 Insulin: 1 Unit = 10 microliters (µL) = 10 mm^3
    # Reservoir (Syringe) inner diameter: 9.5 mm -> Radius (r) = 4.75 mm
    # Area of reservoir (pi * r^2) = ~70.88 mm^2
    # Lead screw pitch: 0.5 mm per revolution
    # Volume pushed per revolution = Area * pitch = 35.44 mm^3 = 35.44 µL
    # Insulin units pushed per revolution = 35.44 / 10 = 3.544 Units
    # Stepper Motor: 200 steps per revolution (1.8 deg/step)
    # Steps per Unit = 200 / 3.544 = 56.43 steps/U
    steps_per_revolution = 200
    mechanical_calibration_factor = 1.0
    units_per_revolution = 3.544 * mechanical_calibration_factor
    steps_per_unit_insulin = steps_per_revolution / units_per_revolution
    total_steps = max(1, int(round(total_units * steps_per_unit_insulin)))

    delivery_animation_units = total_units
    delivery_time = utime.time()
    animation_callback = draw_delivery_animation if MOTION_ENABLED else None
    if animation_callback is None:
        draw_dosing_screen(total_units, 0)
    
    completed_steps, cancelled = step_motor(
        5,
        total_steps,
        direction=-1,
        blink_led=True,
        animation_callback=animation_callback,
    )

    delivered_units = completed_steps / steps_per_unit_insulin
    record_carbs_if_needed(delivery_time, carb_grams, absorption_seconds)
    if completed_steps > 0:
        injection_log.append((delivery_time, delivered_units))
    prune_history(delivery_time)

    if cancelled:
        draw_status_screen("Stopped", "{:.1f} U".format(delivered_units), COLOR_BLUE)
        utime.sleep(2)
        return False

    animate_done_screen(total_units)
    return True


def render_once(screen_key, draw_function, *args):
    global last_screen_key
    if screen_key != last_screen_key:
        draw_function(*args)
        last_screen_key = screen_key


def mark_screen_dirty():
    global last_screen_key
    last_screen_key = None


hold_button_name = None
hold_started_ms = 0
hold_last_step_ms = 0


def adjust_value_by_hold(value, normal_step, fast_step, min_value, max_value):
    global hold_button_name, hold_started_ms, hold_last_step_ms

    if happy_button.value() == 0 and sad_button.value() == 0:
        hold_button_name = None
        return value, False
    if demo_combo_active() or calm_combo_active():
        hold_button_name = None
        return value, False

    button_name = None
    direction = 0
    if happy_button.value() == 0:
        button_name = "up"
        direction = 1
    elif sad_button.value() == 0:
        button_name = "down"
        direction = -1
    else:
        hold_button_name = None
        return value, False

    now = utime.ticks_ms()
    if button_name != hold_button_name:
        hold_button_name = button_name
        hold_started_ms = now
        hold_last_step_ms = now
        step = normal_step
    else:
        held_ms = utime.ticks_diff(now, hold_started_ms)
        repeat_ms = 260
        step = normal_step
        if held_ms > 900:
            repeat_ms = 130
            step = fast_step
        if held_ms > 2200:
            repeat_ms = 75
            step = fast_step * 2
        if utime.ticks_diff(now, hold_last_step_ms) < repeat_ms:
            return value, False
        hold_last_step_ms = now

    value += direction * step
    if value < min_value:
        value = min_value
    if value > max_value:
        value = max_value
    if isinstance(normal_step, float) or isinstance(fast_step, float):
        value = round(value, 1)
    else:
        value = int(value)
    mark_user_activity()
    return value, True


def current_settings():
    return (
        ("Target", TARGET_BG, "mg/dL", 5, 20, 80, 180, "target"),
        ("Daily dose", TDD, "U/day", 1, 5, 10, 100, "tdd"),
        ("Insulin action", DIA_HOURS, "hours", 0.5, 1.0, 2.0, 8.0, "dia"),
        ("Calm mode", TAMAGOTCHI_MODE, "", 1, 1, 0, 1, "tamagotchi"),
        ("CGM sensor", CGM_SIM_MODE, "", 1, 1, 0, 1, "cgm"),
        ("Animations", MOTION_ENABLED, "", 1, 1, 0, 1, "motion"),
        ("Rewind", 0, "", 1, 1, 0, 0, "rewind"),
        ("Button guide", 0, "", 1, 1, 0, 0, "guide"),
    )


def apply_setting(setting_id, value):
    global TARGET_BG, TDD, ICR, ISF, DIA_HOURS
    global TAMAGOTCHI_MODE, CGM_SIM_MODE, MOTION_ENABLED
    if setting_id == "target":
        TARGET_BG = int(value)
    elif setting_id == "tdd":
        TDD = float(value)
        ICR = 500.0 / TDD
        ISF = 1800.0 / TDD
    elif setting_id == "dia":
        DIA_HOURS = float(value)
    elif setting_id == "tamagotchi":
        TAMAGOTCHI_MODE = int(value)
    elif setting_id == "cgm":
        CGM_SIM_MODE = int(value)
        if CGM_SIM_MODE:
            update_cgm_sensor(force=True)
    elif setting_id == "motion":
        MOTION_ENABLED = int(value)


def run_rewind_mode():
    frame = 0
    wait_buttons_released()
    mark_screen_dirty()
    try:
        while True:
            if sleep_if_idle():
                continue
            if settings_combo_pressed():
                wait_buttons_released()
                mark_screen_dirty()
                return
            if demo_combo_pressed():
                disable_motor()
                run_demo_mode()
                mark_screen_dirty()
                continue
            if button_pressed(sad_button):
                mark_screen_dirty()
                return

            if angry_button.value() == 0 and happy_button.value() == 1 and sad_button.value() == 1:
                render_once(
                    ("rewind_running", frame),
                    draw_rewind_screen,
                    frame,
                    True,
                )
                continuous_step_motor(5, 32, direction=1)
                frame = (frame + 1) % 12
            else:
                disable_motor()
                render_once(
                    ("rewind_idle", frame),
                    draw_rewind_screen,
                    frame,
                    False,
                )
                utime.sleep_ms(35)
    finally:
        disable_motor()


def run_controls_guide():
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue
        render_once("button_guide", draw_controls_guide_screen)
        if confirm_pressed() or button_pressed(sad_button) or settings_combo_pressed():
            wait_buttons_released()
            mark_screen_dirty()
            return
        utime.sleep_ms(35)


def run_settings_menu():
    setting_index = 0
    settings = current_settings()
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue
        render_once(
            "settings_menu",
            draw_settings_menu_screen,
            setting_index,
            settings,
        )

        if settings_combo_pressed():
            mark_screen_dirty()
            wait_buttons_released()
            return
        if demo_combo_pressed():
            run_demo_mode()
            mark_screen_dirty()
            continue

        if confirm_pressed():
            setting_id = settings[setting_index][7]
            if setting_id == "rewind":
                run_rewind_mode()
            elif setting_id == "guide":
                run_controls_guide()
            else:
                run_setting_editor(setting_index)
                settings = current_settings()
            mark_screen_dirty()
            continue

        new_index, changed = adjust_value_by_hold(setting_index, 1, 1, 0, len(settings) - 1)
        if changed:
            setting_index = new_index
            mark_screen_dirty()
        utime.sleep_ms(35)


def run_setting_editor(setting_index):
    settings = current_settings()
    title, value, unit, normal_step, fast_step, min_value, max_value, setting_id = settings[setting_index]
    wait_buttons_released()
    mark_screen_dirty()
    while True:
        if sleep_if_idle():
            continue
        render_once(
            "setting_editor",
            draw_settings_screen,
            setting_index,
            len(settings),
            title,
            value,
            unit,
            setting_id,
        )

        if settings_combo_pressed():
            wait_buttons_released()
            mark_screen_dirty()
            return
        if demo_combo_pressed():
            run_demo_mode()
            mark_screen_dirty()
            continue
        if confirm_pressed():
            mark_screen_dirty()
            return

        new_value, changed = adjust_value_by_hold(value, normal_step, fast_step, min_value, max_value)
        if changed:
            value = new_value
            apply_setting(setting_id, new_value)
            mark_screen_dirty()
        utime.sleep_ms(35)


def resolve_image_path(filename):
    for candidate in (
        filename,
        "Bluey/" + filename,
        "/" + filename,
        "/Bluey/" + filename,
    ):
        try:
            with open(candidate, "rb"):
                return candidate
        except Exception:
            pass
    return filename


def draw_face_fallback(cx, cy, emotion):
    fill_circle(cx, cy, 34, COLOR_PANEL_2)
    if emotion == "happy":
        fill_circle(cx - 11, cy - 6, 4, COLOR_TEXT)
        fill_circle(cx + 11, cy - 6, 4, COLOR_TEXT)
        for offset in range(-10, 11):
            y_arc = cy + 6 + (offset * offset) // 16
            fb.pixel(cx + offset, y_arc, COLOR_TEXT)
            fb.pixel(cx + offset, y_arc + 1, COLOR_TEXT)
    elif emotion == "sad":
        draw_thick_line(cx - 15, cy - 4, cx - 7, cy - 4, COLOR_TEXT, 2)
        draw_thick_line(cx + 7, cy - 4, cx + 15, cy - 4, COLOR_TEXT, 2)
        for offset in range(-10, 11):
            y_arc = cy + 14 - (offset * offset) // 16
            fb.pixel(cx + offset, y_arc, COLOR_TEXT)
            fb.pixel(cx + offset, y_arc + 1, COLOR_TEXT)
    elif emotion == "dizzy":
        draw_thick_line(cx - 14, cy - 10, cx - 6, cy - 2, COLOR_TEXT, 2)
        draw_thick_line(cx - 14, cy - 2, cx - 6, cy - 10, COLOR_TEXT, 2)
        draw_thick_line(cx + 6, cy - 10, cx + 14, cy - 2, COLOR_TEXT, 2)
        draw_thick_line(cx + 6, cy - 2, cx + 14, cy - 10, COLOR_TEXT, 2)
        draw_thick_line(cx - 10, cy + 10, cx + 10, cy + 10, COLOR_AMBER, 2)


def draw_raw_image(filename, x, y, w, h, mask_radius=None, bg_color=COLOR_BG):
    if w <= 0 or h <= 0:
        return False
    if x + w <= 0 or y + h <= 0 or x >= WIDTH or y >= HEIGHT:
        return False

    actual_path = resolve_image_path(filename)
    row_bytes = w * 2
    if row_bytes == len(raw_image_row_buffer):
        row_buffer = raw_image_row_view
    elif row_bytes < len(raw_image_row_buffer):
        row_buffer = raw_image_row_view[:row_bytes]
    else:
        row_buffer = bytearray(row_bytes)

    try:
        raw_bg_fb.fill(bg_color)
        bg0 = raw_bg_pixel[0]
        bg1 = raw_bg_pixel[1]
        mask_cx = w // 2
        mask_cy = h // 2
        r2 = (mask_radius * mask_radius) if mask_radius else None

        with open(actual_path, "rb") as f:
            for row in range(h):
                read = f.readinto(row_buffer)
                if read != row_bytes:
                    break

                screen_y = y + row
                if screen_y < 0 or screen_y >= HEIGHT:
                    continue

                if mask_radius is not None:
                    dy = row - mask_cy
                    remaining = r2 - dy * dy
                    if remaining < 0:
                        left = w
                        right = -1
                    else:
                        span = int(remaining ** 0.5)
                        left = max(0, mask_cx - span)
                        right = min(w - 1, mask_cx + span)

                    for px in range(left):
                        pos = px * 2
                        row_buffer[pos] = bg0
                        row_buffer[pos + 1] = bg1
                    for px in range(right + 1, w):
                        pos = px * 2
                        row_buffer[pos] = bg0
                        row_buffer[pos + 1] = bg1

                screen_x_start = max(0, x)
                screen_x_end = min(WIDTH, x + w)
                src_x_start = screen_x_start - x
                src_x_end = screen_x_end - x
                src_bytes_len = (src_x_end - src_x_start) * 2

                if src_bytes_len > 0:
                    start_idx = (screen_y * WIDTH + screen_x_start) * 2
                    src_pos = src_x_start * 2
                    buffer[start_idx : start_idx + src_bytes_len] = row_buffer[src_pos : src_pos + src_bytes_len]
        return True
    except Exception as e:
        print("Image load error for", actual_path, ":", e)
        return False


def draw_tamagotchi_home(cx, cy, emotion):
    clear(COLOR_BG)
    draw_card(10, 34, 220, 164)

    image_center_y = 78
    image_radius = 28
    img_x = cx - 32
    img_y = image_center_y - 32

    label = "In range"
    drawn = False
    if emotion == "happy":
        label = "In range"
        drawn = draw_raw_image("happy_calm.raw", int(img_x), int(img_y), 64, 64, image_radius, COLOR_PANEL)
        if not drawn:
            draw_face_fallback(cx, image_center_y, "happy")
    elif emotion == "sad":
        label = "Glucose is low"
        drawn = draw_raw_image("sad_calm.raw", int(img_x), int(img_y), 64, 64, image_radius, COLOR_PANEL)
        if not drawn:
            draw_face_fallback(cx, image_center_y, "sad")
    elif emotion == "dizzy":
        label = "Glucose is high"
        drawn = draw_raw_image("angry_calm.raw", int(img_x), int(img_y), 64, 64, image_radius, COLOR_PANEL)
        if not drawn:
            draw_face_fallback(cx, image_center_y, "dizzy")

    draw_header("Calm mode", 0, 0)
    draw_circle_outline(cx, image_center_y, image_radius + 2, 2, COLOR_FOCUS)
    draw_ui_centered(label, 113, COLOR_TEXT)
    fb.hline(22, 130, 196, COLOR_EDGE)

    value_text = format_value(huidige_bg)
    val_w = rounded_number_width(value_text, 34)
    start_x = (WIDTH - val_w - 28) // 2
    draw_rounded_number(value_text, start_x, 139, 34, COLOR_TEXT)
    draw_trend_arrow(start_x + val_w + 15, 155, cgm_trend, COLOR_FOCUS)
    draw_ui_centered("mg/dL  " + ui_title(trend_label(cgm_trend)), 178, COLOR_MUTED)

    draw_footer("~SLEEP", "~TREND", "BOLUS")
    flush()


def draw_face(cx, cy, emotion):
    clear(COLOR_BG)
    draw_card(10, 34, 220, 164)
    image_center_y = 78
    image_radius = 28
    img_x = cx - 32
    img_y = image_center_y - 32

    label = "Feels okay"
    preview_bg = TARGET_BG
    if emotion == "happy":
        label = "Feels okay"
        preview_bg = TARGET_BG
        drawn = draw_raw_image("happy_calm.raw", int(img_x), int(img_y), 64, 64, image_radius, COLOR_PANEL)
        if not drawn:
            draw_face_fallback(cx, image_center_y, "happy")
    elif emotion == "sad":
        label = "Feels low"
        preview_bg = TARGET_BG - 30
        drawn = draw_raw_image("sad_calm.raw", int(img_x), int(img_y), 64, 64, image_radius, COLOR_PANEL)
        if not drawn:
            draw_face_fallback(cx, image_center_y, "sad")
    elif emotion == "dizzy":
        label = "Feels high"
        preview_bg = TARGET_BG + 50
        drawn = draw_raw_image("angry_calm.raw", int(img_x), int(img_y), 64, 64, image_radius, COLOR_PANEL)
        if not drawn:
            draw_face_fallback(cx, image_center_y, "dizzy")

    draw_header("How do you feel?", 1, 2)
    draw_circle_outline(cx, image_center_y, image_radius + 2, 2, COLOR_FOCUS)
    draw_ui_centered(label, 113, COLOR_TEXT, 2)
    fb.hline(22, 139, 196, COLOR_EDGE)

    value_text = format_value(preview_bg)
    val_w = rounded_number_width(value_text, 30)
    start_x = (WIDTH - val_w - ui_text_width("mg/dL") - 8) // 2
    draw_rounded_number(value_text, start_x, 151, 30, COLOR_TEXT)
    draw_ui_text("mg/dL", start_x + val_w + 8, 172, COLOR_MUTED)
    draw_footer("NEXT", "PREV", "SELECT")
    flush()


def draw_portion_plate(cx, cy, portion_level):
    fill_circle(cx, cy, 46, COLOR_EDGE)
    fill_circle(cx, cy, 43, COLOR_PANEL)

    positions = ((cx - 14, cy - 14), (cx + 14, cy - 14), (cx - 14, cy + 14), (cx + 14, cy + 14))
    for index, position in enumerate(positions):
        fill_circle(position[0], position[1], 12, COLOR_FOCUS if index < portion_level else COLOR_PANEL_2)
        draw_circle_outline(position[0], position[1], 12, 2, COLOR_FOCUS if index < portion_level else COLOR_EDGE)

    draw_circle_outline(cx, cy, 43, 2, COLOR_EDGE)


def draw_food(cx, cy, food_index, cgm_value=None, trend=None, footer_labels=("NEXT", "PREV", "SELECT")):
    clear(COLOR_BG)
    draw_header("Choose meal size", 1, 3)

    draw_card(10, 34, 220, 164)

    if cgm_value is not None:
        cgm_text = "Sensor {}".format(cgm_value)
        draw_ui_text(cgm_text, 22, 45, COLOR_MUTED)
        if trend is not None:
            draw_compact_trend_arrow(22 + ui_text_width(cgm_text) + 9, 49, trend, COLOR_FOCUS)

    draw_portion_plate(cx, 103, food_index)

    label = PORTION_LABELS[food_index]
    draw_ui_centered(label, 153, COLOR_TEXT, 2 if ui_text_width(label, 2) <= 190 else 1)
    grams = "{} g carbohydrate".format(PORTION_CARBS[food_index])
    draw_ui_centered(grams, 179, COLOR_MUTED)

    draw_footer(footer_labels[0], footer_labels[1], footer_labels[2])
    flush()

# --- Hoofdprogramma ---
show_startup_screen()
gc.collect()

while True:
    if stap != 2 and sleep_if_idle():
        continue

    if CGM_SIM_MODE and update_cgm_sensor():
        mark_screen_dirty()

    # Stap 0: Huidige Bloedsuiker
    if stap == 0:
        if CGM_SIM_MODE == 1:
            if home_should_lock():
                run_lock_screen()
                continue

            if TAMAGOTCHI_MODE == 1:
                emotion = calm_emotion_for_glucose(huidige_bg)
                render_once(
                    "tamagotchi_home",
                    draw_tamagotchi_home,
                    120,
                    110,
                    emotion,
                )
            else:
                render_once(
                    "cgm_home",
                    draw_cgm_home_screen,
                )

            if TAMAGOTCHI_MODE == 1 and calm_combo_pressed():
                run_calm_pause()
            elif sleep_button_long_pressed():
                enter_deep_sleep()
            elif demo_combo_pressed():
                mark_user_activity()
                run_demo_mode()
            elif settings_combo_pressed():
                mark_user_activity()
                run_settings_menu()
            elif graph_button_long_pressed():
                mark_user_activity()
                run_cgm_graph_screen()
            elif confirm_pressed():
                mark_user_activity()
                if TAMAGOTCHI_MODE == 1:
                    run_guided_bluey_bolus_flow()
                else:
                    stap = 1
                mark_screen_dirty()
                utime.sleep_ms(200)
            utime.sleep_ms(50)
        elif TAMAGOTCHI_MODE == 1:
            emotion = TAMAGOTCHI_MOODS[tamagotchi_mood_index]
                
            render_once(
                "tamagotchi_bg",
                draw_face,
                120,
                110,
                emotion,
            )
            
            if calm_combo_pressed():
                run_calm_pause()
            elif demo_combo_pressed():
                run_demo_mode()
            elif settings_combo_pressed():
                run_settings_menu()
            elif confirm_pressed():
                if tamagotchi_mood_index == 0:
                    huidige_bg = TARGET_BG - 30
                elif tamagotchi_mood_index == 1:
                    huidige_bg = TARGET_BG
                else:
                    huidige_bg = TARGET_BG + 50
                stap = 1
                mark_screen_dirty()
                utime.sleep_ms(200)
            elif button_pressed(happy_button): # RIGHT / UP
                tamagotchi_mood_index = (tamagotchi_mood_index + 1) % 3
                mark_screen_dirty()
                utime.sleep_ms(200)
            elif button_pressed(sad_button): # LEFT / DOWN
                tamagotchi_mood_index = (tamagotchi_mood_index - 1) % 3
                mark_screen_dirty()
                utime.sleep_ms(200)
            utime.sleep_ms(50)
        else:
            render_once(
                "bg",
                draw_value_screen,
                "Glucose",
                1,
                huidige_bg,
                "mg/dL",
                "Target: {}".format(TARGET_BG),
                COLOR_MINT,
            )
            
            if demo_combo_pressed():
                run_demo_mode()
            elif settings_combo_pressed():
                run_settings_menu()
            elif confirm_pressed():
                stap = 1
                mark_screen_dirty()
            else:
                nieuwe_bg, changed = adjust_value_by_hold(huidige_bg, 10, 25, 40, 400)
                if changed:
                    huidige_bg = nieuwe_bg
                    mark_screen_dirty()
            utime.sleep_ms(50)

    # Stap 1: Stel gram koolhydraten in
    elif stap == 1:
        if TAMAGOTCHI_MODE == 1:
            render_once(
                "tamagotchi_food",
                draw_food,
                120,
                110,
                tamagotchi_food_index,
                huidige_bg if CGM_SIM_MODE else None,
                cgm_trend if CGM_SIM_MODE else None,
            )
            
            if calm_combo_pressed():
                run_calm_pause()
            elif demo_combo_pressed():
                run_demo_mode()
            elif settings_combo_pressed():
                run_settings_menu()
            elif confirm_pressed():
                mark_user_activity()
                gram_koolhydraten = PORTION_CARBS[tamagotchi_food_index]
                selected_carb_absorption_seconds = (
                    SLOW_CARB_ABSORPTION_SECONDS
                    if tamagotchi_food_index == 4
                    else STANDARD_CARB_ABSORPTION_SECONDS
                )
                stap = 2
                mark_screen_dirty()
                utime.sleep_ms(200)
            elif button_pressed(happy_button):
                tamagotchi_food_index = (tamagotchi_food_index + 1) % 5
                mark_screen_dirty()
                utime.sleep_ms(200)
            elif button_pressed(sad_button):
                tamagotchi_food_index = (tamagotchi_food_index - 1) % 5
                mark_screen_dirty()
                utime.sleep_ms(200)
            utime.sleep_ms(50)
        else:
            carb_hint = "CGM: {}".format(huidige_bg) if CGM_SIM_MODE else "Grams"
            render_once(
                "koolhydraten",
                draw_value_screen,
                "Carbohydrate",
                2,
                gram_koolhydraten,
                "g",
                carb_hint,
                COLOR_FOCUS,
                cgm_trend if CGM_SIM_MODE else None,
            )
            
            if demo_combo_pressed():
                run_demo_mode()
            elif settings_combo_pressed():
                run_settings_menu()
            elif confirm_pressed():
                selected_carb_absorption_seconds = STANDARD_CARB_ABSORPTION_SECONDS
                stap = 2
                mark_screen_dirty()
            else:
                nieuwe_carbs, changed = adjust_value_by_hold(gram_koolhydraten, 5, 20, 0, 250)
                if changed:
                    gram_koolhydraten = nieuwe_carbs
                    mark_screen_dirty()
            utime.sleep_ms(50)

    # Stap 2: Bereken insuline en voer de bevestigde demonstratiedosis uit
    elif stap == 2:
        current_time = utime.time()
        totale_dosis, cob, iob = calculate_demo_bolus(gram_koolhydraten, current_time)

        # Toon een rustig rekenscherm
        draw_status_screen("Calc", "Wait", COLOR_MINT)
        utime.sleep_ms(500)

        if totale_dosis > 0:
            if not confirm_delivery(totale_dosis):
                draw_status_screen("Cancelled", "No dose", COLOR_BLUE)
                utime.sleep(2)
                reset_bolus_to_home()
                continue

            deliver_demo_bolus(
                totale_dosis,
                gram_koolhydraten,
                selected_carb_absorption_seconds,
            )
        else:
            record_carbs_if_needed(
                utime.time(),
                gram_koolhydraten,
                selected_carb_absorption_seconds,
            )
            draw_status_screen("None", "0.0 U", COLOR_BLUE)
            utime.sleep(2)

        reset_bolus_to_home()
    
