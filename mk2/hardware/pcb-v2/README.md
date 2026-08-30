# IINTS MK2 PCB V2

This directory contains the editable KiCad source files supplied for the IINTS
V2 electronics concept. Open `ai_pomp.kicad_pro` with **KiCad 9** to inspect or
continue the design.

> [!WARNING]
> **Design source, not a production release.** The current board file is an
> early placement placeholder. It has no finished board outline, routing,
> copper pours, verified netlist, fabrication outputs, or manufacturing
> validation. Do not order this board or connect it to a person on the basis of
> these files.

## Project Files

| File | Purpose |
| --- | --- |
| `ai_pomp.kicad_pro` | Main KiCad project settings |
| `ai_pomp.kicad_sch` | Root hierarchical schematic |
| `ai_pomp.kicad_pcb` | Early PCB placement concept |
| `USB-C.kicad_sch` | USB-C power-input draft |
| `untitled.kicad_sch` | Seven-pin display connector sheet |
| `Motor_Driver.kicad_sch` | Motor-driver draft sheet |
| `Pinnen.kicad_sch` | Controller-pin/header draft sheet |
| `Schermpje.kicad_sch` | Additional interface draft sheet |
| `1e-knopje.kicad_sch` | Button 1 draft |
| `2e-knopje.kicad_sch` | Button 2 draft |
| `3e-knopje.kicad_sch` | Button 3 draft |

KiCad lock files, personal preferences, autosaves, and backup archives are
deliberately excluded. Git already provides version history for the published
source files.

## Known Differences From The Current MK2 Prototype

The active MK2 firmware and photographed controller use a Raspberry Pi Pico,
three buttons, a DRV8833 module, and a 240 x 240 ST7789 display. The supplied
KiCad draft predates that final wiring choice:

- `Pinnen.kicad_sch` describes a generic 2 x 20 controller header rather than
  the Pico's 40 castellated pins;
- `ai_pomp.kicad_pcb` contains placeholder footprints, including a compute
  module and a generic SPI display;
- the PCB file does not yet contain a complete schematic-derived netlist,
  tracks, vias, mounting holes, or a closed `Edge.Cuts` outline;
- the three separate button sheets are retained as source material but are not
  all linked into the current root hierarchy.

The files are published so the design history is open and can be improved, not
to suggest that this revision is fabrication-ready.

## Firmware GPIO Target

A future PCB revision should be checked against the canonical firmware mapping:

| Function | Pico GPIO |
| --- | --- |
| DRV8833 IN1, IN2, IN3, IN4 | `GP4`, `GP5`, `GP6`, `GP9` |
| DRV8833 enable | `GP28` |
| ST7789 SCK, MOSI, RES, DC | `GP10`, `GP11`, `GP12`, `GP13` |
| Buttons 1, 2, 3 | `GP16`, `GP17`, `GP18` to GND |

See the parent [MK2 README](../../README.md) for the complete wiring and power
notes.

## Before Fabrication

At minimum, a new hardware revision needs:

1. Pico/Pico W symbols and footprints that match the chosen board revision.
2. A complete schematic-to-PCB netlist matching the firmware GPIO table.
3. Verified USB-C power circuitry, supply limits, grounding, decoupling, motor
   current, reverse-polarity protection, and battery protection.
4. A finished board outline, mounting holes, connector clearances, routed
   copper, power planes, and readable silkscreen.
5. Clean KiCad ERC and DRC reports reviewed by a qualified electronics engineer.
6. Bench validation with current-limited power and the motor/load disconnected.
7. Gerber, drill, BOM, and pick-and-place exports generated only from the
   reviewed release commit.

This remains an educational electronics prototype and is not a medical-device
hardware design.

## License

These design sources are distributed with the repository under the terms in
the root [`LICENSE`](../../../LICENSE). Third-party symbols, footprints, and
component documentation retain their own applicable terms.
