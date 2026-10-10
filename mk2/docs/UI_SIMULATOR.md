# IINTS UI Simulator

The simulator previews the real drawing functions from
`../firmware/pico_drv8833_correct_pins.py` without connecting to the Pico.

## Requirements

- **Windows**: Python 3.10+ (Tkinter is included with standard Python installations) and Pillow (`pip install pillow`).
- **Linux / WSL (Ubuntu/Debian)**: Tkinter is packaged separately and must be installed via `apt`:
  ```bash
  sudo apt update
  sudo apt install -y python3-tk python3-pil python3-pil.imagetk
  ```
  *(Note: Running GUI applications inside WSL also requires WSLg or an active X11 server).*

## Start

Double-click `simulator/Open UI Simulator.command`, or run:

```bash
cd mk2/simulator
python3 ui_simulator.py
```

On Windows (Command Prompt / PowerShell):

```powershell
cd mk2\simulator
python ui_simulator.py
```

## Workflow

1. Select a screen in the left column.
2. Change glucose, trend, carbs, dose, portion, or mode on the right.
3. Use the GP16, GP17, and GP18 buttons below the display, or keys `1`, `2`, `3`.
4. Use Quick access for Settings, Calm Pause, Trend, and the demo image.
5. Keep Auto-reload enabled while editing the firmware source.
6. Use Screenshot for the current 240x240 screen or Export all for a contact sheet.
7. Open **UI Builder** to design a separate screen by adding and arranging text,
   rectangles, circles, and lines on a 240x240 canvas.

## UI Builder

The builder opens from the simulator and starts with an editable example screen.
Manage screens with Add, Copy, Delete, and the screen selector. Select an element
from the Layers list or click it on the canvas, then drag it or edit its position,
size, text, and color in Properties. Use the layer controls to change draw order.
Projects containing multiple screens are saved as `.iintsui` JSON files and can
be reopened later. Screen PNG exports the active screen; Contact sheet exports
all screens together.

Export firmware creates a standalone MicroPython module with a `draw_<screen>(fb)`
function for each screen, plus `draw_custom_ui(fb)` as an alias for the first
screen. Each function draws onto an existing 240x240
`framebuf.FrameBuffer`; call it from the firmware and then call the firmware's
`flush()` to show it. The generated module does not initialize the display or
alter pump behavior. Firmware text uses the built-in 8x8 framebuffer font, so
it must contain ASCII characters. Always review exported UI code and test it on
the simulator before deploying it to pump hardware.

The screen list includes all 21 standard, Calm Mode, confirmation, maintenance,
sleep, and help views. Auto-reload watches the firmware source; restart the
simulator after changing `ui_simulator.py` itself.

The simulator uses fake GPIO, SPI, motor, and display modules. It cannot deliver
a dose or move the physical motor.

## Command-line contact sheet

```bash
python3 ui_simulator.py --contact-sheet previews/all_screens.png
```
