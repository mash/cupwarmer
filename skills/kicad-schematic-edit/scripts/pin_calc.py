"""Pin absolute position calculator for KiCad schematics.

KiCad 10 coordinate mapping:
  Symbol coords: Y up (math convention)
  Schematic coords: Y down (screen convention)

For a symbol at (sx, sy) with rotation angle:
  angle=0:   schematic = (sx + px, sy - py)
  angle=90:  rotate CCW 90: (px,py) -> (-py, px)  -> (sx - py, sy - px)
  angle=180: rotate 180:    (px,py) -> (-px, -py)  -> (sx - px, sy + py)
  angle=270: rotate CW 90:  (px,py) -> (py, -px)   -> (sx + py, sy + px)
"""
import math


def pin_schematic_pos(sym_x, sym_y, sym_angle, pin_x, pin_y):
    """Calculate absolute schematic position of a pin.

    Args:
        sym_x, sym_y: Symbol placement position in schematic
        sym_angle: Symbol rotation (0, 90, 180, 270)
        pin_x, pin_y: Pin position in symbol coordinates

    Returns:
        (sch_x, sch_y): Absolute schematic coordinates of pin connection point
    """
    angle = int(sym_angle) % 360
    if angle == 0:
        return (sym_x + pin_x, sym_y - pin_y)
    elif angle == 90:
        return (sym_x - pin_y, sym_y - pin_x)
    elif angle == 180:
        return (sym_x - pin_x, sym_y + pin_y)
    elif angle == 270:
        return (sym_x + pin_y, sym_y + pin_x)
    else:
        # General rotation (shouldn't happen in practice)
        rad = math.radians(angle)
        rx = pin_x * math.cos(rad) - pin_y * math.sin(rad)
        ry = pin_x * math.sin(rad) + pin_y * math.cos(rad)
        return (sym_x + rx, sym_y - ry)


def passive2_pins(cx, cy, angle):
    """Return (pin1_x, pin1_y, pin2_x, pin2_y) for PASSIVE_2 symbol.

    PASSIVE_2 has pin1 at (-5.08, 0) and pin2 at (5.08, 0) in symbol coords.
    """
    p1x, p1y = pin_schematic_pos(cx, cy, angle, -5.08, 0)
    p2x, p2y = pin_schematic_pos(cx, cy, angle, 5.08, 0)
    return (p1x, p1y, p2x, p2y)


# Verification against known good values from ERC
if __name__ == "__main__":
    # U1 at (106.68, 63.5, angle=0)
    # AC1 at symbol (-12.7, 5.08) -> should be (93.98, 58.42)
    x, y = pin_schematic_pos(106.68, 63.5, 0, -12.7, 5.08)
    assert abs(x - 93.98) < 0.01 and abs(y - 58.42) < 0.01, f"AC1: ({x}, {y})"

    # BOOT1 at symbol (-12.7, -5.08) -> should be (93.98, 68.58)
    x, y = pin_schematic_pos(106.68, 63.5, 0, -12.7, -5.08)
    assert abs(x - 93.98) < 0.01 and abs(y - 68.58) < 0.01, f"BOOT1: ({x}, {y})"

    # PASSIVE_2 at (83.82, 68.58, angle=0) -> pin1 (78.74, 68.58), pin2 (88.9, 68.58)
    p1x, p1y, p2x, p2y = passive2_pins(83.82, 68.58, 0)
    assert abs(p1x - 78.74) < 0.01, f"P2 pin1: ({p1x}, {p1y})"
    assert abs(p2x - 88.9) < 0.01, f"P2 pin2: ({p2x}, {p2y})"

    # PASSIVE_2 at (86.36, 77.47, angle=90)
    # pin1 at symbol (-5.08, 0): angle=90 -> (86.36 - 0, 77.47 - (-5.08)) = (86.36, 82.55)
    # pin2 at symbol (5.08, 0):  angle=90 -> (86.36 - 0, 77.47 - 5.08) = (86.36, 72.39)
    p1x, p1y, p2x, p2y = passive2_pins(86.36, 77.47, 90)
    assert abs(p1x - 86.36) < 0.01 and abs(p1y - 82.55) < 0.01, f"P2@90 pin1: ({p1x}, {p1y})"
    assert abs(p2x - 86.36) < 0.01 and abs(p2y - 72.39) < 0.01, f"P2@90 pin2: ({p2x}, {p2y})"

    print("All verification tests PASS")
