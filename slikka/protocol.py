"""VIA / Vial USB HID protocol for communicating with QMK keyboards."""

import struct
import hid

# VIA protocol command IDs
CMD_GET_PROTOCOL_VERSION = 0x01
CMD_DYNAMIC_KEYMAP_GET_KEYCODE = 0x04
CMD_DYNAMIC_KEYMAP_SET_KEYCODE = 0x05
CMD_DYNAMIC_KEYMAP_GET_BUFFER = 0x0C
CMD_DYNAMIC_KEYMAP_SET_BUFFER = 0x0D
CMD_DYNAMIC_KEYMAP_GET_LAYER_COUNT = 0x11
CMD_VIAL = 0xFE

# Vial sub-commands
VIAL_GET_KEYBOARD_ID = 0x00
VIAL_GET_DEFINITION_SIZE = 0x01
VIAL_GET_DEFINITION = 0x02

# Default HID report size for VIA/Vial
REPORT_SIZE = 32

# Raw HID usage page/usage for VIA/Vial
VIA_USAGE_PAGE = 0xFF60
VIA_USAGE = 0x61


class KeyboardNotFoundError(Exception):
    pass


class VialKeyboard:
    """Communicates with a Vial-enabled QMK keyboard over USB HID."""

    def __init__(self, vid: int = 0xFEED, pid: int = 0x1212):
        self.vid = vid
        self.pid = pid
        self.dev = hid.device()
        self._path = None

    def open(self) -> None:
        """Find and open the raw HID interface for VIA/Vial."""
        devices = hid.enumerate(self.vid, self.pid)
        if not devices:
            raise KeyboardNotFoundError(
                f"No HID device found with VID=0x{self.vid:04X} PID=0x{self.pid:04X}. "
                "Is the keyboard plugged in?"
            )

        # Find the raw HID interface (usage_page 0xFF60, usage 0x61)
        for d in devices:
            if d.get("usage_page") == VIA_USAGE_PAGE and d.get("usage") == VIA_USAGE:
                self._path = d["path"]
                break

        if self._path is None:
            # Fallback: some systems don't report usage_page, try the first
            # interface that isn't a keyboard/mouse
            for d in devices:
                if d.get("usage_page", 0) not in (0x01, 0x0C):
                    self._path = d["path"]
                    break

        if self._path is None:
            # Last resort: just try the first device
            self._path = devices[0]["path"]

        self.dev.open_path(self._path)
        self.dev.set_nonblocking(False)

    def close(self) -> None:
        self.dev.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def _send(self, data: list[int]) -> list[int]:
        """Send a raw HID report and receive the response."""
        # Pad to report size
        msg = data[:REPORT_SIZE]
        msg += [0x00] * (REPORT_SIZE - len(msg))
        # Prepend report ID 0x00 (required on Windows)
        self.dev.write([0x00] + msg)
        # Read response
        resp = self.dev.read(REPORT_SIZE, timeout_ms=1000)
        if not resp:
            raise TimeoutError("No response from keyboard")
        return list(resp)

    def get_protocol_version(self) -> int:
        """Get the VIA protocol version."""
        resp = self._send([CMD_GET_PROTOCOL_VERSION])
        return (resp[1] << 8) | resp[2]

    def get_layer_count(self) -> int:
        """Get the number of dynamic keymap layers."""
        resp = self._send([CMD_DYNAMIC_KEYMAP_GET_LAYER_COUNT])
        return resp[1]

    def get_keycode(self, layer: int, row: int, col: int) -> int:
        """Get a single keycode from the dynamic keymap."""
        resp = self._send([CMD_DYNAMIC_KEYMAP_GET_KEYCODE, layer, row, col])
        return (resp[4] << 8) | resp[5]

    def set_keycode(self, layer: int, row: int, col: int, keycode: int) -> None:
        """Set a single keycode in the dynamic keymap."""
        self._send([
            CMD_DYNAMIC_KEYMAP_SET_KEYCODE,
            layer, row, col,
            (keycode >> 8) & 0xFF,
            keycode & 0xFF,
        ])

    def get_keymap(self, rows: int, cols: int, layers: int) -> list[list[list[int]]]:
        """Read the entire dynamic keymap using individual keycode reads.

        Returns a 3D list: keymap[layer][row][col] = keycode (16-bit).
        """
        import sys
        total = layers * rows * cols
        done = 0

        keymap = []
        for layer in range(layers):
            layer_data = []
            for row in range(rows):
                row_data = []
                for col in range(cols):
                    kc = self.get_keycode(layer, row, col)
                    row_data.append(kc)
                    done += 1
                layer_data.append(row_data)
            keymap.append(layer_data)
            # Progress per layer
            pct = done * 100 // total
            sys.stderr.write(f"\r  Reading... {pct}% (layer {layer}/{layers})")
            sys.stderr.flush()
        sys.stderr.write("\r  Reading... done!              \n")
        return keymap

    def get_vial_keyboard_id(self) -> tuple[int, bytes]:
        """Get Vial protocol version and keyboard UID."""
        resp = self._send([CMD_VIAL, VIAL_GET_KEYBOARD_ID])
        vial_version = struct.unpack_from("<I", bytes(resp), 0)[0]
        uid = bytes(resp[4:12])
        return vial_version, uid

    def get_vial_definition(self) -> bytes:
        """Get the LZMA-compressed Vial keyboard definition."""
        # Get size
        resp = self._send([CMD_VIAL, VIAL_GET_DEFINITION_SIZE])
        size = struct.unpack_from("<I", bytes(resp), 0)[0]

        # Read definition in chunks
        data = bytearray()
        offset = 0
        while offset < size:
            chunk_size = min(28, size - offset)
            resp = self._send([
                CMD_VIAL, VIAL_GET_DEFINITION,
                (offset >> 8) & 0xFF,
                offset & 0xFF,
                chunk_size,
            ])
            data.extend(resp[4:4 + chunk_size])
            offset += chunk_size
        return bytes(data[:size])
