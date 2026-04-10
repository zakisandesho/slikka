"""CLI entry point: python -m slikka"""

import argparse
import sys
import webbrowser

from .protocol import VialKeyboard, KeyboardNotFoundError
from .layout import get_silakka54_layout
from .renderer import render_all_layers, render_layer


def main():
    parser = argparse.ArgumentParser(
        description="Read and display the keymap from a Vial-enabled keyboard."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="show",
        choices=["show", "gui"],
        help="'show' for terminal output (default), 'gui' for web UI.",
    )
    parser.add_argument(
        "-l", "--layer",
        type=int,
        default=None,
        help="Show only this layer number (default: show all non-empty layers).",
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
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8378,
        help="Port for the web UI (default: 8378).",
    )
    parser.add_argument(
        "--all-layers",
        action="store_true",
        help="Show all layers, including empty/transparent ones.",
    )
    args = parser.parse_args()

    try:
        if args.command == "gui":
            run_gui(args)
        else:
            run_show(args)
    except KeyboardNotFoundError as e:
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


if __name__ == "__main__":
    main()
