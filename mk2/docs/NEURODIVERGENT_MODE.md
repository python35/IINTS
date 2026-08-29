# IINTS-AF Calm Mode

Calm Mode is the neurodivergent-friendly interface for the Pico pump prototype.
It keeps the medical calculation unchanged while reducing visual and cognitive
load during normal monitoring and the guided bolus flow.

## Prototype Features

- One decision per screen with a fixed header, content area, and three button zones.
- Soft cool-white, grey, and muted-blue surfaces with dark readable text.
- Status is always written in words; colour is never the only signal.
- A small buddy image supports the reading without replacing the glucose value.
- Meal size uses four visible portions plus the exact carbohydrate amount.
- Delivery requires a separate adult review and a deliberate hold on `OK`.
- Calm Pause stops motor output and presents three short, predictable steps.
- Animations can be disabled in Settings without changing the calculations.

## Complete Pico Control Guide

- `GP16`: increase a value or move to the next choice.
- `GP17`: decrease a value, move to the previous choice, cancel, or stop delivery.
- `GP18`: select, confirm, or continue.
- Hold `GP16` on Home for 2.5 seconds: enter deep sleep.
- Hold `GP17` on Home for 0.9 seconds: open glucose history.
- Hold `GP18` on Adult Check: confirm delivery.
- Hold `GP18` in Rewind: run the motor backwards while held.
- Hold `GP16 + GP17` for 0.7 seconds: open or close Settings.
- Hold `GP16 + GP18` for 0.7 seconds in Calm Mode: open Calm Pause.
- Hold `GP17 + GP18` for 0.7 seconds: open or close the project demo image.
- Press any button while sleeping: wake the display.

The same guide is available on the pump under `Settings > Button guide`.

## Safety Note

This is a research prototype, not a certified medical device. UI and motor tests
should be performed with insulin disconnected and under qualified supervision.
