"""Simple web server for the keyboard layout GUI."""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .keycodes import decode_keycode
from .layout import get_silakka54_layout
from .protocol import VialKeyboard

STATIC_DIR = Path(__file__).parent / "static"


def read_keyboard(vid: int, pid: int) -> dict:
    """Connect to the keyboard and read the full keymap."""
    keys = get_silakka54_layout()

    with VialKeyboard(vid=vid, pid=pid) as kb:
        layer_count = kb.get_layer_count()
        print(f"  Layer count: {layer_count}")
        keymap = kb.get_keymap(rows=10, cols=6, layers=layer_count)

    # Build layout data
    layout = []
    for k in keys:
        layout.append({
            "x": k.x, "y": k.y, "w": k.w, "h": k.h,
            "row": k.row, "col": k.col,
        })

    # Build layer data with decoded keycode names
    layers = []
    for layer_idx, layer_data in enumerate(keymap):
        layer_keys = {}
        for k in keys:
            kc = layer_data[k.row][k.col]
            layer_keys[f"{k.row},{k.col}"] = {
                "code": kc,
                "name": decode_keycode(kc),
            }
        layers.append(layer_keys)

    return {
        "layout": layout,
        "layers": layers,
        "layer_count": layer_count,
    }


def make_handler(keymap_data: dict):
    """Create an HTTP request handler with the keymap data baked in."""

    keymap_json = json.dumps(keymap_data).encode("utf-8")

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/keymap":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(keymap_json))
                self.end_headers()
                self.wfile.write(keymap_json)
            elif self.path == "/":
                # Serve index.html
                self._serve_static("index.html")
            elif self.path.startswith("/static/"):
                filename = self.path[len("/static/"):]
                self._serve_static(filename)
            else:
                self.send_error(404)

        def _serve_static(self, filename: str):
            filepath = STATIC_DIR / filename
            if not filepath.is_file():
                self.send_error(404)
                return

            content = filepath.read_bytes()
            self.send_response(200)

            ext = filepath.suffix.lower()
            content_types = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json",
                ".png": "image/png",
                ".svg": "image/svg+xml",
            }
            ct = content_types.get(ext, "application/octet-stream")
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format, *args):
            pass  # Suppress request logging

    return Handler


def serve(keymap_data: dict, port: int = 8378):
    """Start the web server."""
    handler = make_handler(keymap_data)
    server = HTTPServer(("127.0.0.1", port), handler)
    print(f"  Open http://localhost:{port} in your browser")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
