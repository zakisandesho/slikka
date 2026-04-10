"""QMK keycode definitions and decoding."""

# Basic keycodes (USB HID usage IDs)
BASIC_KEYCODES = {
    0x00: "KC_NO",
    0x01: "TRNS",
    0x04: "A", 0x05: "B", 0x06: "C", 0x07: "D", 0x08: "E", 0x09: "F",
    0x0A: "G", 0x0B: "H", 0x0C: "I", 0x0D: "J", 0x0E: "K", 0x0F: "L",
    0x10: "M", 0x11: "N", 0x12: "O", 0x13: "P", 0x14: "Q", 0x15: "R",
    0x16: "S", 0x17: "T", 0x18: "U", 0x19: "V", 0x1A: "W", 0x1B: "X",
    0x1C: "Y", 0x1D: "Z",
    0x1E: "1", 0x1F: "2", 0x20: "3", 0x21: "4", 0x22: "5",
    0x23: "6", 0x24: "7", 0x25: "8", 0x26: "9", 0x27: "0",
    0x28: "ENT", 0x29: "ESC", 0x2A: "BSPC", 0x2B: "TAB", 0x2C: "SPC",
    0x2D: "-", 0x2E: "=", 0x2F: "[", 0x30: "]", 0x31: "\\",
    0x32: "#", 0x33: ";", 0x34: "'", 0x35: "`", 0x36: ",", 0x37: ".",
    0x38: "/", 0x39: "CAPS",
    0x3A: "F1", 0x3B: "F2", 0x3C: "F3", 0x3D: "F4", 0x3E: "F5", 0x3F: "F6",
    0x40: "F7", 0x41: "F8", 0x42: "F9", 0x43: "F10", 0x44: "F11", 0x45: "F12",
    0x46: "PSCR", 0x47: "SCRL", 0x48: "PAUS",
    0x49: "INS", 0x4A: "HOME", 0x4B: "PGUP",
    0x4C: "DEL", 0x4D: "END", 0x4E: "PGDN",
    0x4F: "RGHT", 0x50: "LEFT", 0x51: "DOWN", 0x52: "UP",
    0x53: "NLCK", 0x54: "P/", 0x55: "P*", 0x56: "P-", 0x57: "P+",
    0x58: "PENT", 0x59: "P1", 0x5A: "P2", 0x5B: "P3", 0x5C: "P4",
    0x5D: "P5", 0x5E: "P6", 0x5F: "P7", 0x60: "P8", 0x61: "P9",
    0x62: "P0", 0x63: "P.",
    0x65: "APP",  # Application / Menu key
    0xE0: "LCTL", 0xE1: "LSFT", 0xE2: "LALT", 0xE3: "LGUI",
    0xE4: "RCTL", 0xE5: "RSFT", 0xE6: "AltGr", 0xE7: "RGUI",
}

# Well-known QMK special keycodes
SPECIAL_KEYCODES = {
    0x7C73: "CW_TOG",   # Caps Word Toggle
    0x7C7C: "QK_LLCK",  # Layer Lock
    0x7C00: "QK_BOOT",  # Bootloader
    0x7C01: "QK_RBT",   # Reboot
    0x7C02: "DB_TOGG",  # Debug Toggle
    0x7C03: "EE_CLR",   # EEPROM Clear
}


def _decode_mods(mod_bits: int) -> str:
    """Decode a 5-bit modifier field into a string."""
    right = bool(mod_bits & 0x10)
    prefix = "R" if right else "L"
    parts = []
    if mod_bits & 0x01:
        parts.append(f"{prefix}C")
    if mod_bits & 0x02:
        parts.append(f"{prefix}S")
    if mod_bits & 0x04:
        parts.append(f"{prefix}A")
    if mod_bits & 0x08:
        parts.append(f"{prefix}G")
    return "+".join(parts) if parts else "?"


def decode_keycode(kc: int) -> str:
    """Decode a 16-bit QMK keycode to a human-readable string."""
    if kc in SPECIAL_KEYCODES:
        return SPECIAL_KEYCODES[kc]

    # Basic keycodes: 0x0000 - 0x00FF
    if kc <= 0x00FF:
        return BASIC_KEYCODES.get(kc, f"0x{kc:02X}")

    # QK_MODS: 0x0100 - 0x1FFF (modifier + basic keycode)
    if 0x0100 <= kc <= 0x1FFF:
        mods = (kc >> 8) & 0x1F
        base = kc & 0xFF
        mod_str = _decode_mods(mods)
        if base:
            base_str = BASIC_KEYCODES.get(base, f"0x{base:02X}")
            return f"{mod_str}({base_str})"
        return mod_str

    # QK_MOD_TAP: 0x2000 - 0x3FFF
    if 0x2000 <= kc <= 0x3FFF:
        mods = (kc >> 8) & 0x1F
        base = kc & 0xFF
        mod_str = _decode_mods(mods)
        base_str = BASIC_KEYCODES.get(base, f"0x{base:02X}")
        return f"MT({mod_str},{base_str})"

    # QK_LAYER_TAP: 0x4000 - 0x4FFF
    if 0x4000 <= kc <= 0x4FFF:
        layer = (kc >> 8) & 0x0F
        base = kc & 0xFF
        if base == 0:
            return f"MO({layer})"  # LT(layer, KC_NO) is effectively MO
        base_str = BASIC_KEYCODES.get(base, f"0x{base:02X}")
        return f"LT{layer}({base_str})"

    # QK_TO: 0x5000 - 0x501F
    if 0x5000 <= kc <= 0x501F:
        return f"TO({kc & 0x1F})"

    # QK_MOMENTARY: 0x5100 - 0x511F
    if 0x5100 <= kc <= 0x511F:
        return f"MO({kc & 0x1F})"

    # QK_DEF_LAYER: 0x5200 - 0x521F
    if 0x5200 <= kc <= 0x521F:
        return f"DF({kc & 0x1F})"

    # QK_PERSISTENT_DEF_LAYER: 0x5220 - 0x523F
    if 0x5220 <= kc <= 0x523F:
        return f"PDF({kc & 0x1F})"

    # QK_TOGGLE_LAYER: 0x5300 - 0x531F
    if 0x5300 <= kc <= 0x531F:
        return f"TG({kc & 0x1F})"

    # QK_ONE_SHOT_LAYER: 0x5400 - 0x541F
    if 0x5400 <= kc <= 0x541F:
        return f"OSL({kc & 0x1F})"

    # QK_ONE_SHOT_MOD: 0x5500 - 0x551F
    if 0x5500 <= kc <= 0x551F:
        return f"OSM({_decode_mods(kc & 0x1F)})"

    # QK_LAYER_TAP_TOGGLE: 0x5600 - 0x561F
    if 0x5600 <= kc <= 0x561F:
        return f"TT({kc & 0x1F})"

    # QK_KB (keyboard-specific custom keycodes): 0x7700 - 0x77FF
    if 0x7700 <= kc <= 0x77FF:
        return f"KB_{kc & 0xFF}"

    # QK_USER (user-defined custom keycodes): 0x7E00 - 0x7EFF
    if 0x7E00 <= kc <= 0x7EFF:
        return f"USER_{kc & 0xFF}"

    return f"0x{kc:04X}"
