"""CLI entry point: python -m slikka"""

import argparse
import sys
import webbrowser

from .protocol import VialKeyboard, KeyboardNotFoundError
from .layout import get_silakka54_layout
from .renderer import render_all_layers, render_layer, render_map


def main():
    parser = argparse.ArgumentParser(
        description="Read, display, and edit the keymap on a Vial-enabled keyboard."
    )
    parser.add_argument(
        "--vid",
        type=lambda x: int(x, 16),
        default=0xFEED,
        help="USB Vendor ID in hex (default: FEED).",
    )
    parser.add_argument(
        "--pid",
        type=lambda x: int(x, 16),
        default=0x1212,
        help="USB Product ID in hex (default: 1212).",
    )

    sub = parser.add_subparsers(dest="command")

    # show (default)
    show_p = sub.add_parser("show", help="Show keymap in terminal (default).")
    show_p.add_argument(
        "-l", "--layer", type=int, default=None,
        help="Show only this layer number.",
    )
    show_p.add_argument(
        "--all-layers", action="store_true",
        help="Show all layers, including empty/transparent ones.",
    )

    # gui
    gui_p = sub.add_parser("gui", help="Open web UI.")
    gui_p.add_argument(
        "-p", "--port", type=int, default=8378,
        help="Port for the web UI (default: 8378).",
    )

    # map
    map_p = sub.add_parser("map", help="Show position map for editing.")
    map_p.add_argument(
        "-l", "--layer", type=int, default=0,
        help="Layer to show (default: 0).",
    )

    # backup
    backup_p = sub.add_parser("backup", help="Save full keymap to a JSON file.")
    backup_p.add_argument(
        "file", nargs="?", default=None,
        help="Output file (default: keymap_YYYYMMDD_HHMMSS.json).",
    )

    # restore
    restore_p = sub.add_parser("restore", help="Restore keymap from a JSON file.")
    restore_p.add_argument(
        "file", type=str,
        help="JSON backup file to restore from.",
    )

    # set
    set_p = sub.add_parser("set", help="Set a key by position number.")
    set_p.add_argument(
        "position", type=int,
        help="Key position number (see 'map' command).",
    )
    set_p.add_argument(
        "keycode", type=str,
        help="Keycode name (e.g. A, ESC, MO(2), LT1(A), LC(C)) or hex (0x1234).",
    )
    set_p.add_argument(
        "-l", "--layer", type=int, default=0,
        help="Layer number (default: 0).",
    )

    args = parser.parse_args()

    # Default to 'show' when no subcommand given
    if args.command is None:
        args.command = "show"
        args.layer = None
        args.all_layers = False

    try:
        if args.command == "gui":
            run_gui(args)
        elif args.command == "map":
            run_map(args)
        elif args.command == "set":
            run_set(args)
        elif args.command == "backup":
            run_backup(args)
        elif args.command == "restore":
            run_restore(args)
        else:
            run_show(args)
    except KeyboardNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_show(args):
    keys = get_silakka54_layout()

    print("Connecting to keyboard...")
    with VialKeyboard(vid=args.vid, pid=args.pid) as kb:
        version = kb.get_protocol_version()
        layer_count = kb.get_layer_count()
        print(f"VIA protocol version: {version}")
        print(f"Layer count: {layer_count}")
        print(f"Reading keymap ({layer_count} layers, 10 rows, 6 cols)...")

        keymap = kb.get_keymap(rows=10, cols=6, layers=layer_count)

    print()
    if args.layer is not None:
        if args.layer >= layer_count:
            print(f"Error: layer {args.layer} does not exist (max: {layer_count - 1})")
            sys.exit(1)
        print(render_layer(keys, keymap[args.layer], args.layer))
    else:
        print(render_all_layers(keys, keymap, skip_empty=not args.all_layers))


def run_gui(args):
    from .web import read_keyboard, serve

    print("Connecting to keyboard...")
    keymap_data = read_keyboard(vid=args.vid, pid=args.pid)
    print(f"Starting web UI...")
    webbrowser.open(f"http://localhost:{args.port}")
    serve(keymap_data, port=args.port)


def run_map(args):
    keys = get_silakka54_layout()

    print("Connecting to keyboard...")
    with VialKeyboard(vid=args.vid, pid=args.pid) as kb:
        layer_count = kb.get_layer_count()

        if args.layer >= layer_count:
            print(f"Error: layer {args.layer} does not exist (max: {layer_count - 1})",
                  file=sys.stderr)
            sys.exit(1)

        # Read only the requested layer
        layer_data = []
        for row in range(10):
            row_data = []
            for col in range(6):
                kc = kb.get_keycode(args.layer, row, col)
                row_data.append(kc)
            layer_data.append(row_data)

    print()
    print(render_map(keys, layer_data, args.layer))


def run_set(args):
    from .keycodes import encode_keycode, decode_keycode

    keys = get_silakka54_layout()

    # Validate position
    if args.position < 0 or args.position >= len(keys):
        print(f"Error: position {args.position} out of range (0-{len(keys) - 1}).",
              file=sys.stderr)
        sys.exit(1)

    # Encode the keycode
    keycode = encode_keycode(args.keycode)

    key = keys[args.position]

    print("Connecting to keyboard...")
    with VialKeyboard(vid=args.vid, pid=args.pid) as kb:
        layer_count = kb.get_layer_count()

        if args.layer >= layer_count:
            print(f"Error: layer {args.layer} does not exist (max: {layer_count - 1})",
                  file=sys.stderr)
            sys.exit(1)

        # Read current value
        old_kc = kb.get_keycode(args.layer, key.row, key.col)
        old_name = decode_keycode(old_kc)

        # Write new value
        kb.set_keycode(args.layer, key.row, key.col, keycode)

        # Read back to confirm
        verify_kc = kb.get_keycode(args.layer, key.row, key.col)

    new_name = decode_keycode(verify_kc)

    if verify_kc == keycode:
        print(f"Position #{args.position} (row={key.row}, col={key.col}), layer {args.layer}:")
        print(f"  {old_name} -> {new_name}")
    else:
        print(f"Warning: verification failed!", file=sys.stderr)
        print(f"  Wrote: 0x{keycode:04X} ({decode_keycode(keycode)})", file=sys.stderr)
        print(f"  Read:  0x{verify_kc:04X} ({new_name})", file=sys.stderr)
        sys.exit(1)


def run_backup(args):
    import json
    from datetime import datetime
    from .keycodes import decode_keycode

    filename = args.file
    if filename is None:
        filename = f"keymap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print("Connecting to keyboard...")
    with VialKeyboard(vid=args.vid, pid=args.pid) as kb:
        layer_count = kb.get_layer_count()
        print(f"Reading keymap ({layer_count} layers)...")
        keymap = kb.get_keymap(rows=10, cols=6, layers=layer_count)

    # Build backup data with raw codes + human-readable names
    layers = []
    for layer_data in keymap:
        layer_rows = []
        for row in layer_data:
            layer_rows.append([
                {"code": kc, "name": decode_keycode(kc)} for kc in row
            ])
        layers.append(layer_rows)

    backup = {
        "vid": f"0x{args.vid:04X}",
        "pid": f"0x{args.pid:04X}",
        "timestamp": datetime.now().isoformat(),
        "rows": 10,
        "cols": 6,
        "layer_count": layer_count,
        "keymap": layers,
    }

    with open(filename, "w") as f:
        json.dump(backup, f, indent=2)

    print(f"Saved {layer_count} layers to {filename}")


def run_restore(args):
    import json
    from .keycodes import decode_keycode

    with open(args.file) as f:
        backup = json.load(f)

    layer_count = backup["layer_count"]
    rows = backup["rows"]
    cols = backup["cols"]
    keymap = backup["keymap"]

    print(f"Restoring from {args.file} ({layer_count} layers)...")
    print("Connecting to keyboard...")
    with VialKeyboard(vid=args.vid, pid=args.pid) as kb:
        kb_layers = kb.get_layer_count()
        if layer_count > kb_layers:
            print(f"Warning: backup has {layer_count} layers but keyboard has {kb_layers}.",
                  file=sys.stderr)
            print(f"Restoring first {kb_layers} layers only.", file=sys.stderr)
            layer_count = kb_layers

        total = layer_count * rows * cols
        done = 0
        for layer_idx in range(layer_count):
            for row_idx in range(rows):
                for col_idx in range(cols):
                    entry = keymap[layer_idx][row_idx][col_idx]
                    kc = entry["code"]
                    kb.set_keycode(layer_idx, row_idx, col_idx, kc)
                    done += 1
            pct = done * 100 // total
            sys.stderr.write(f"\r  Writing... {pct}% (layer {layer_idx}/{layer_count})")
            sys.stderr.flush()
        sys.stderr.write("\r  Writing... done!              \n")

    print(f"Restored {layer_count} layers.")


if __name__ == "__main__":
    main()
