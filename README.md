# Slikka

A lightweight Python CLI tool for reading and editing the keymap on a [Vial](https://get.vial.today/)-enabled QMK keyboard over USB HID. Built for situations where you can't install the Vial GUI (e.g. a locked-down work machine).

## Prerequisites

- Python 3.8+
- The keyboard must be connected via USB

### Windows

You may need to install a USB driver for the raw HID interface. If the keyboard is not detected, try [Zadig](https://zadig.akeo.ie/) to install a WinUSB or libusb driver for the HID interface.

## Installation

```bash
pip install -r requirements.txt
```

This installs `hidapi`, the only dependency.

## Usage

### Terminal view (default)

```bash
python -m slikka
```

This connects to the keyboard, reads all layers, and renders them as ASCII art in the terminal. Empty/transparent layers are skipped by default.

#### Show a specific layer

```bash
python -m slikka show -l 2
```

#### Show all layers (including empty ones)

```bash
python -m slikka show --all-layers
```

### Web UI

```bash
python -m slikka gui
```

This reads the keymap and starts a local web server on `http://localhost:8378`, opening it in your default browser.

#### Use a different port

```bash
python -m slikka gui -p 9090
```

### Position map

```bash
python -m slikka map
```

Shows the keyboard layout with numbered positions (`#0`, `#1`, ...) and the current keycode for each key. Use this to find the position number you need for editing.

#### Show a different layer

```bash
python -m slikka map -l 1
```

### Editing keys

```bash
python -m slikka set <position> <keycode> [-l <layer>]
```

Set a key by its position number (from the `map` command). The layer defaults to 0 if not specified. The change is written to the keyboard's EEPROM immediately.

Examples:

```bash
python -m slikka set 12 ESC              # set position #12 to Escape on layer 0
python -m slikka set 12 "LS(#)" -l 1     # set position #12 to * (Swedish layout) on layer 1
python -m slikka set 5 "MO(2)"           # set position #5 to momentary layer 2
python -m slikka set 8 "LT1(A)"          # set position #8 to layer-tap (hold=layer 1, tap=A)
python -m slikka set 0 "LC(C)"           # set position #0 to Ctrl+C
python -m slikka set 3 0x7C73            # set by raw hex keycode
```

Supported keycode formats:

| Format | Example | Description |
|--------|---------|-------------|
| Basic key | `A`, `ESC`, `BSPC`, `F1` | Standard keys (KC_ prefix optional) |
| Layer momentary | `MO(2)` | Activate layer while held |
| Layer toggle | `TG(3)` | Toggle layer on/off |
| Layer tap | `LT1(A)` | Hold for layer 1, tap for A |
| Mod tap | `MT(LC,ESC)` | Hold for LCtrl, tap for Escape |
| Modifier combo | `LC(C)`, `LS+LA(TAB)` | Key with modifiers applied |
| One-shot mod | `OSM(LS)` | One-shot Left Shift |
| Special | `CW_TOG`, `QK_BOOT` | QMK special keycodes |
| Transparent | `TRNS` | Fall through to layer below |
| No key | `KC_NO` | Disabled |
| Raw hex | `0x1234` | Any 16-bit QMK keycode |

### Custom USB IDs

By default slikka looks for VID `0xFEED` and PID `0x1212` (the silakka54). To target a different keyboard:

```bash
python -m slikka --vid FEED --pid 1212
```

## All options

```
python -m slikka [command] [options]

commands:
  show                  Show keymap in terminal (default).
  gui                   Open web UI.
  map                   Show position map for editing.
  set POS KEYCODE       Set a key by position number.

global options:
  --vid VID             USB Vendor ID in hex (default: FEED).
  --pid PID             USB Product ID in hex (default: 1212).

show options:
  -l, --layer LAYER     Show only this layer number.
  --all-layers          Show all layers, including empty/transparent ones.

gui options:
  -p, --port PORT       Port for the web UI (default: 8378).

map options:
  -l, --layer LAYER     Layer to show (default: 0).

set options:
  -l, --layer LAYER     Layer number (default: 0).
```
