"""Terminal renderer for keyboard layouts."""

from .keycodes import decode_keycode
from .layout import Key

# Characters per KLE unit
CELL_W = 8
CELL_H = 3

# Box drawing characters (ASCII-safe for Windows console)
TL = "+"
TR = "+"
BL = "+"
BR = "+"
HZ = "-"
VT = "|"


def render_layer(keys: list[Key], keymap_layer: list[list[int]], layer_num: int) -> str:
    """Render a single keymap layer as ASCII art.

    Args:
        keys: Physical key positions from the layout.
        keymap_layer: 2D array [row][col] of keycodes for this layer.
        layer_num: Layer number (for the header).

    Returns:
        A string with the rendered layout.
    """
    # Determine grid size
    max_x = max(k.x + k.w for k in keys)
    max_y = max(k.y + k.h for k in keys)
    grid_w = int(round(max_x * CELL_W)) + 2
    grid_h = int(round(max_y * CELL_H)) + 2

    # Create character grid (filled with spaces)
    grid = [[" "] * grid_w for _ in range(grid_h)]

    for key in keys:
        kc = keymap_layer[key.row][key.col]
        name = decode_keycode(kc)

        # Convert to character coordinates
        px = int(round(key.x * CELL_W))
        py = int(round(key.y * CELL_H))
        pw = int(round(key.w * CELL_W))
        ph = int(round(key.h * CELL_H))

        # Clamp to grid bounds
        if px < 0 or py < 0 or px + pw > grid_w or py + ph > grid_h:
            continue

        inner_w = pw - 2  # space between vertical borders

        # Draw box
        # Top border
        grid[py][px] = TL
        for i in range(1, pw - 1):
            grid[py][px + i] = HZ
        grid[py][px + pw - 1] = TR

        # Bottom border
        grid[py + ph - 1][px] = BL
        for i in range(1, pw - 1):
            grid[py + ph - 1][px + i] = HZ
        grid[py + ph - 1][px + pw - 1] = BR

        # Side borders
        for j in range(1, ph - 1):
            grid[py + j][px] = VT
            grid[py + j][px + pw - 1] = VT

        # Key label (centered in the middle row)
        mid_y = py + ph // 2
        # Truncate name to fit
        display_name = name[:inner_w]
        # Center the name
        pad_left = (inner_w - len(display_name)) // 2
        for ci, ch in enumerate(display_name):
            grid[mid_y][px + 1 + pad_left + ci] = ch

    # Build output string
    header = f"  Layer {layer_num}"
    lines = [header, "  " + "=" * (grid_w - 2)]
    for row in grid:
        line = "".join(row).rstrip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def render_all_layers(
    keys: list[Key],
    keymap: list[list[list[int]]],
    skip_empty: bool = True,
) -> str:
    """Render all keymap layers.

    Args:
        keys: Physical key positions.
        keymap: 3D array [layer][row][col] of keycodes.
        skip_empty: If True, skip layers that are all KC_TRNS or KC_NO.

    Returns:
        A string with all rendered layers.
    """
    parts = []
    for layer_idx, layer_data in enumerate(keymap):
        if skip_empty:
            # Check if layer has any non-transparent, non-empty keys
            has_content = False
            for row in layer_data:
                for kc in row:
                    if kc not in (0x0000, 0x0001):  # KC_NO, KC_TRNS
                        has_content = True
                        break
                if has_content:
                    break
            if not has_content:
                continue

        parts.append(render_layer(keys, layer_data, layer_idx))
        parts.append("")  # blank line between layers

    return "\n".join(parts)
