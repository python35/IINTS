# IINTS UI Simulator

The simulator previews the real drawing functions from
`../firmware/pico_drv8833_correct_pins.py` without connecting to the Pico.

## Start

Double-click `simulator/Open UI Simulator.command`, or run:

```bash
cd mk2/simulator
python3 ui_simulator.py
```

## Workflow

1. Select a screen in the left column.
2. Change glucose, trend, carbs, dose, portion, or mode on the right.
3. Use the GP16, GP17, and GP18 buttons below the display, or keys `1`, `2`, `3`.
4. Use Quick access for Settings, Calm Pause, Trend, and the demo image.
5. Keep Auto-reload enabled while editing the firmware source.
6. Use Screenshot for the current 240x240 screen or Export all for a contact sheet.

The screen list includes all 21 standard, Calm Mode, confirmation, maintenance,
sleep, and help views. Auto-reload watches the firmware source; restart the
simulator after changing `ui_simulator.py` itself.

The simulator uses fake GPIO, SPI, motor, and display modules. It cannot deliver
a dose or move the physical motor.

## Command-line contact sheet

```bash
python3 ui_simulator.py --contact-sheet previews/all_screens.png
```
