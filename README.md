# IINTS MK2

**Second-generation neuro-inclusive insulin pump simulator, open hardware
study, and electromechanical research demonstrator**

> You are viewing the **`mk2` branch**. For the original first-generation
> project, open the [`mk1` branch](https://github.com/python35/IINTS/tree/mk1).

> [!CAUTION]
> **Research and education prototype only.** IINTS MK2 is not a certified
> medical device. It must not be used to make treatment decisions or deliver
> insulin to a person. Test it disconnected from a person and use water or
> another harmless test liquid.

<p align="center">
  <img src="mk2/assets/hardware/mk2-complete-prototype.png" width="650" alt="Complete IINTS MK2 prototype with controller, display, syringe, lead screw, and stepper motor">
</p>

<p align="center"><strong>Complete IINTS MK2 research prototype</strong></p>

## At A Glance

| | MK2 |
| --- | --- |
| Purpose | Open research demonstrator for pump mechanics, embedded UI, and neuro-inclusive interaction |
| Controller | Raspberry Pi Pico running MicroPython |
| Interface | 240 x 240 ST7789 IPS display and three physical buttons |
| Motor system | DRV8833 with a bipolar stepper, lead screw, and test syringe |
| Glucose input | Virtual CGM in `mg/dL`, updated every 60 seconds |
| UI modes | Standard Mode and low-sensory Calm Mode |
| Development tools | Desktop UI simulator, Thonny, `mpremote`, and `mpy-cross` |
| Open files | Firmware, Pico deploy package, KiCad V2 sources, assets, report, and guides |
| Current status | Working educational prototype; PCB V2 source remains a design draft |

## Quick Navigation

| I want to... | Open |
| --- | --- |
| Understand the complete MK2 | [Technical MK2 README](mk2/README.md) |
| Read the firmware | [MicroPython source](mk2/firmware/pico_drv8833_correct_pins.py) |
| Upload the app to a Pico | [Ready-to-upload deploy folder](mk2/firmware/deploy/) |
| Preview every screen safely | [Desktop UI simulator](mk2/simulator/) |
| Inspect the electronics design | [KiCad PCB V2 project](mk2/hardware/pcb-v2/) |
| Read the research report | [IINTS MK2 PDF](mk2/docs/IINTS-MK2.pdf) |

## Overview

IINTS MK2 is the second generation of the IINTS project. It combines a
Raspberry Pi Pico, a 240 x 240 ST7789 IPS display, three physical buttons, a
DRV8833 motor driver, a bipolar stepper motor, a virtual glucose sensor, and a
desktop UI simulator.

MK2 explores two questions together:

1. How can an embedded pump mechanism, user interface, and educational dosing
   model be built transparently from open source components?
2. How can the interaction be calmer and easier to follow for children and
   neurodivergent users without hiding clinically relevant information?

The current interface is in English and uses glucose values in `mg/dL`. The
complete source and documentation are kept under [`mk2/`](mk2/README.md).

## Main Features

- virtual CGM updates every minute with rising, steady, and falling trends;
- Standard Mode with glucose, IOB, COB, carbohydrate, and dose information;
- low-sensory **Calm Mode** with one decision per screen;
- guided meal-size and bolus flow;
- separate Adult Check with a deliberate hold before motor movement;
- glucose history, settings, button guide, manual rewind, and Calm Pause;
- automatic lock and power-saving sleep;
- delivery animation and flashing onboard LED while the motor runs;
- cancellable motor movement with completed-step tracking;
- desktop simulator that runs the real firmware drawing functions;
- published MicroPython source, deploy package, project report, UI assets,
  controller photograph, and editable KiCad V2 design files.

## Open Project Files

| Area | Files |
| --- | --- |
| Complete MK2 documentation | [`mk2/README.md`](mk2/README.md) |
| Canonical MicroPython firmware | [`mk2/firmware/pico_drv8833_correct_pins.py`](mk2/firmware/pico_drv8833_correct_pins.py) |
| Ready-to-upload Pico filesystem | [`mk2/firmware/deploy/`](mk2/firmware/deploy/) |
| Desktop UI simulator | [`mk2/simulator/`](mk2/simulator/) |
| Complete UI overview | [`mk2/simulator/previews/current-ui-overview.png`](mk2/simulator/previews/current-ui-overview.png) |
| PCB V2 KiCad source | [`mk2/hardware/pcb-v2/`](mk2/hardware/pcb-v2/) |
| MK2 controller photograph | [`mk2/assets/hardware/`](mk2/assets/hardware/) |
| Calm Mode documentation | [`mk2/docs/NEURODIVERGENT_MODE.md`](mk2/docs/NEURODIVERGENT_MODE.md) |
| UI simulator guide | [`mk2/docs/UI_SIMULATOR.md`](mk2/docs/UI_SIMULATOR.md) |
| Project report | [`mk2/docs/IINTS-MK2.pdf`](mk2/docs/IINTS-MK2.pdf) |

## Repository Structure

```text
mk2/
|-- README.md                         # Complete MK2 documentation
|-- assets/
|   |-- branding/                     # IINTS branding and startup preview
|   |-- bluey/                        # Calm Mode assets and rights notice
|   `-- hardware/                     # MK2 controller photograph
|-- docs/                             # Project report and focused guides
|-- firmware/
|   |-- pico_drv8833_correct_pins.py  # Readable source of truth
|   |-- st7789.py                     # Display driver
|   `-- deploy/                       # Ready-to-copy Pico files
|-- hardware/
|   `-- pcb-v2/                       # Editable KiCad 9 design source
|-- simulator/                        # Desktop UI simulator and previews
|-- tools/                            # Asset preparation and hardware tests
`-- requirements.txt                  # Desktop development dependencies
```

Some first-generation files remain in the repository history and root for
traceability. The maintained MK2 project lives under `mk2/`.

## Neuro-Inclusive Calm Mode

Calm Mode keeps the glucose value and trend visible while reducing the amount
of information presented at once. It uses:

- predictable screen structure;
- muted colours and dark readable text;
- written labels in addition to colour and arrows;
- a small buddy image that does not cover the glucose value;
- five consistent meal portions;
- an adult review before motor movement;
- a pause screen with three short, ordered steps;
- optional animations.

This is a research design direction, not a formally certified accessibility or
medical-usability claim.

<details>
<summary><strong>View all current MK2 screens</strong></summary>

![Complete IINTS MK2 UI overview](mk2/simulator/previews/current-ui-overview.png)

</details>

## Hardware And PCB V2

The photographed prototype uses a Raspberry Pi Pico, ST7789 display, three
buttons, and a DRV8833 motor-driver module. The firmware GPIO mapping is fully
documented in the [technical MK2 README](mk2/README.md#wiring).

The supplied KiCad project is published openly under
[`mk2/hardware/pcb-v2/`](mk2/hardware/pcb-v2/). It contains the project,
hierarchical schematics, and an early PCB placement file.

> [!WARNING]
> The KiCad PCB is an early design study. It still contains generic placeholder
> footprints, is not routed, and does not match the photographed Pico board
> one-to-one. It is not ready for fabrication. Read the
> [PCB status notes](mk2/hardware/pcb-v2/README.md) before reusing it.

Gerbers, drill files, BOM, and pick-and-place files are intentionally not
present because no reviewed manufacturing release exists yet.

## Run The UI Simulator

The simulator does not connect to the Pico and cannot move the motor:

```bash
git clone https://github.com/python35/IINTS.git
cd IINTS
git switch mk2
cd mk2

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python simulator/ui_simulator.py
```

On macOS, `mk2/simulator/Open UI Simulator.command` starts the same interface.

## Deploy To A Pico

The low-memory runtime files are already collected in
[`mk2/firmware/deploy/`](mk2/firmware/deploy/):

```text
main.py
pico_app.mpy
st7789.py
start.raw
happy_calm.raw
sad_calm.raw
angry_calm.raw
```

Back up the Pico first, then upload those seven runtime files to its filesystem
root with Thonny or `mpremote`. The compiled `.mpy` format must match the
MicroPython version installed on the Pico. Full build and upload commands are
in the [technical README](mk2/README.md#build-the-pico-application).

## Educational Model

The active demonstration path includes:

- `ICR = 500 / TDD`;
- `ISF = 1800 / TDD`;
- a simplified quadratic IOB decay model;
- linear COB decay over three or six hours;
- meal and correction components with IOB/COB compensation;
- a `70 mg/dL` low-glucose lockout;
- a `15.0 U` single-bolus software limit;
- a volatile 24-hour limit of `2 x TDD`;
- motor conversion based on assumed reservoir and lead-screw geometry.

Experimental PID, predictive-low-glucose, and sensor-noise helpers exist in the
source but are not connected to the active motor-delivery loop. MK2 must not be
presented as a validated closed-loop artificial pancreas.

## Current Limitations

- virtual CGM only;
- no validated basal or closed-loop controller;
- no persistent settings, dose log, or event log;
- no occlusion, reservoir, battery, current, or position sensing;
- no redundant processor or independent motor cutoff;
- unfinished PCB V2 layout and no manufacturing package;
- no formal medical-device, electrical-safety, usability, or clinical
  validation.

## License And Artwork

Original source code, KiCad files, and documentation are published under the
repository's [MIT License](LICENSE).

The optional Bluey buddy images are third-party artwork and are not covered by
the MIT License. IINTS is not affiliated with or endorsed by the relevant
rights holders. See the [asset notice](mk2/assets/bluey/README.md).

## Author

Developed by **Rune Bobbaers** as part of the **IINTS** research project.
