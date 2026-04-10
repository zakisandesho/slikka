"""Parse KLE-style Vial layout definitions into key positions."""

from dataclasses import dataclass

# The silakka54 Vial layout definition (from vial.json).
# This is the KLE-style keymap array that defines physical key positions
# and their matrix coordinates.
SILAKKA54_VIAL_LAYOUT = [
    [{"x": 2}, "0,2", "0,3", {"x": 5.25}, "5,3", "5,2"],
    [{"y": -0.75}, "0,0", "0,1", {"x": 2}, "0,4", {"x": 3.25}, "5,4", {"x": 2}, "5,1", "5,0"],
    [{"y": -0.75, "x": 5}, "0,5", {"x": 1.25}, "5,5"],
    [{"y": -0.5, "x": 2}, "1,2", "1,3", {"x": 5.25}, "6,3", "6,2"],
    [{"y": -0.75}, "1,0", "1,1", {"x": 2}, "1,4", {"x": 3.25}, "6,4", {"x": 2}, "6,1", "6,0"],
    [{"y": -0.75, "x": 5}, "1,5", {"x": 1.25}, "6,5"],
    [{"y": -0.5, "x": 2}, "2,2", "2,3", {"x": 5.25}, "7,3", "7,2"],
    [{"y": -0.75}, "2,0", "2,1", {"x": 2}, "2,4", {"x": 3.25}, "7,4", {"x": 2}, "7,1", "7,0"],
    [{"y": -0.75, "x": 5}, "2,5", {"x": 1.25}, "7,5"],
    [{"y": -0.5, "x": 2}, "3,2", "3,3", {"x": 5.25}, "8,3", "8,2"],
    [{"y": -0.75}, "3,0", "3,1", {"x": 2}, "3,4", {"x": 3.25}, "8,4", {"x": 2}, "8,1", "8,0"],
    [{"y": -0.75, "x": 5}, "3,5", {"x": 1.25}, "8,5"],
    [{"y": 0.25, "x": 2.75}, "4,3", "4,4", {"x": 0.25}, "4,5", {"x": 1.25}, "9,5", {"x": 0.25}, "9,4", "9,3"],
]


@dataclass
class Key:
    """A physical key with its position, size, and matrix coordinate."""
    x: float
    y: float
    w: float
    h: float
    row: int
    col: int


def parse_kle_layout(kle_rows: list) -> list[Key]:
    """Parse a KLE-style layout into a list of Key objects.

    Each row in kle_rows is a JSON array from the Vial layout definition.
    Items are either dicts (formatting) or strings (matrix coords like "0,2").
    """
    keys = []
    current_x = 0.0
    current_y = -1.0  # Will be incremented to 0 at first row

    for row in kle_rows:
        current_x = 0.0
        current_y += 1.0
        next_w = 1.0
        next_h = 1.0

        for item in row:
            if isinstance(item, dict):
                current_x += item.get("x", 0)
                current_y += item.get("y", 0)
                next_w = item.get("w", 1.0)
                next_h = item.get("h", 1.0)
            elif isinstance(item, str):
                parts = item.split(",")
                matrix_row = int(parts[0])
                matrix_col = int(parts[1])
                keys.append(Key(
                    x=current_x,
                    y=current_y,
                    w=next_w,
                    h=next_h,
                    row=matrix_row,
                    col=matrix_col,
                ))
                current_x += next_w
                next_w = 1.0
                next_h = 1.0

    return keys


def get_silakka54_layout() -> list[Key]:
    """Get the parsed physical layout for the silakka54 keyboard."""
    return parse_kle_layout(SILAKKA54_VIAL_LAYOUT)
