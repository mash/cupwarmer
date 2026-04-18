"""Layout helpers for KiCad schematic editing via kiutils.

Provides high-level functions for moving components, drawing wires,
and placing labels with correct coordinate calculations.

KNOWN LIMITATION: kiutils roundtrip reformats the file. If the schematic has
raw-text-added pins in lib_symbols (like this project's STWLC38JRM_MIN),
the save() method preserves lib_symbols but other formatting changes may
still cause ERC differences. Works reliably when:
- The schematic has only kiutils-compatible content (no raw text pin additions)
- OR the kiutils lib_symbols bug is fixed upstream

For schematics with raw-text pins, prefer making layout changes in KiCad GUI,
or apply changes incrementally and verify ERC after each save.

Usage:
    import sys
    sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")
    sys.path.insert(0, "skills/kicad-schematic-edit/scripts")
    from layout_helpers import LayoutEditor

    ed = LayoutEditor("hardware/kicad/cupwarmer-hw/rx-power.kicad_sch")
    ed.move("C5", 76.2, 68.58)
    ed.wire_between("BOOT1@U1", "C5.2")
    ed.gnd_label("C5.1")
    ed.save()
"""
import sys
import copy
import math

sys.path.insert(0, "/Users/mash/src/github.com/mvnmgrx/kiutils/src")

from kiutils.schematic import Schematic
from kiutils.items.schitems import Connection, GlobalLabel
from kiutils.items.common import Position, Stroke, Justify, Effects, Font
from pin_calc import pin_schematic_pos, passive2_pins


# Pin definitions for known symbols (symbol-relative coordinates)
KNOWN_SYMBOLS = {
    "PASSIVE_2": {
        "1": (-5.08, 0),
        "2": (5.08, 0),
    },
    "STWLC38JRM_MIN": {
        "AC1": (-12.7, 5.08), "AC2": (-12.7, 0),
        "VOUT": (12.7, 5.08), "VRECT": (12.7, 2.54),
        "I2C_SCL": (12.7, 0), "I2C_SDA": (12.7, -5.08),
        "SYS_GND": (0, -26.67), "ENB": (-12.7, 2.54),
        "NTC": (-12.7, -2.54), "INTB": (12.7, -10.16),
        "IEXT": (12.7, -15.24), "BOOT1": (-12.7, -5.08),
        "BOOT2": (-12.7, -7.62), "VAA": (12.7, -7.62),
        "VDD": (12.7, -12.7), "VS": (-12.7, -10.16),
        "COMA1": (-12.7, -12.7), "COMA2": (-12.7, -15.24),
        "COMB1": (12.7, -17.78), "COMB2": (12.7, -20.32),
    },
    # Pin numbers map to pin names for STWLC38JRM_MIN
    "_STWLC38JRM_MIN_NUMBERS": {
        "1": "AC1", "2": "AC2", "3": "VOUT", "4": "I2C_SCL",
        "5": "I2C_SDA", "6": "SYS_GND", "7": "ENB", "8": "NTC",
        "9": "INTB", "10": "IEXT", "11": "BOOT1", "12": "BOOT2",
        "13": "VAA", "14": "VDD", "15": "VRECT", "16": "VS",
        "17": "COMA1", "18": "COMA2", "19": "COMB1", "20": "COMB2",
    },
}


class LayoutEditor:
    """High-level editor for KiCad schematic layout changes.

    Handles component positioning, wire routing, and label placement
    with correct coordinate calculations.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        # Preserve original lib_symbols text (kiutils roundtrip breaks pin connectivity)
        with open(filepath) as f:
            self._original_content = f.read()
        self.sch = Schematic.from_file(filepath)
        self._build_index()

    def _build_index(self):
        """Build lookup tables for components."""
        self.symbols = {}
        for sym in self.sch.schematicSymbols:
            ref = next((p.value for p in sym.properties if p.key == "Reference"), None)
            if ref:
                entry = sym.entryName if hasattr(sym, 'entryName') else ""
                self.symbols[ref] = {
                    "sym": sym,
                    "entry": entry,
                    "x": sym.position.X,
                    "y": sym.position.Y,
                    "angle": sym.position.angle or 0,
                }

    def _resolve_pin(self, spec):
        """Resolve a pin spec like 'C5.1', 'C5.2', 'BOOT1@U1' to (x, y).

        Formats:
            'REF.PIN_NUM'     - e.g. 'C5.1', 'C5.2', 'R4.1'
            'PIN_NAME@REF'    - e.g. 'BOOT1@U1', 'AC1@U1'
        """
        if "@" in spec:
            pin_name, ref = spec.split("@")
            info = self.symbols.get(ref)
            if not info:
                raise ValueError(f"Symbol {ref} not found")
            entry = info["entry"]
            sym_pins = KNOWN_SYMBOLS.get(entry, {})
            if pin_name in sym_pins:
                px, py = sym_pins[pin_name]
            else:
                raise ValueError(f"Pin {pin_name} not found in {entry}")
            return pin_schematic_pos(info["x"], info["y"], info["angle"], px, py)

        elif "." in spec:
            ref, pin_num = spec.split(".")
            info = self.symbols.get(ref)
            if not info:
                raise ValueError(f"Symbol {ref} not found")
            entry = info["entry"]

            # For PASSIVE_2, pins are "1" and "2"
            sym_pins = KNOWN_SYMBOLS.get(entry, {})
            if pin_num in sym_pins:
                px, py = sym_pins[pin_num]
            elif entry == "STWLC38JRM_MIN":
                # Try number-to-name lookup
                name = KNOWN_SYMBOLS["_STWLC38JRM_MIN_NUMBERS"].get(pin_num)
                if name and name in sym_pins:
                    px, py = sym_pins[name]
                else:
                    raise ValueError(f"Pin {pin_num} not found in {entry}")
            else:
                raise ValueError(f"Pin {pin_num} not found in {entry}")
            return pin_schematic_pos(info["x"], info["y"], info["angle"], px, py)

        else:
            raise ValueError(f"Invalid pin spec: {spec}. Use 'REF.PIN' or 'NAME@REF'")

    def symbol_pin_positions(self, ref):
        """Return absolute pin positions for a symbol keyed by known pin names."""
        info = self.symbols.get(ref)
        if not info:
            raise ValueError(f"Symbol {ref} not found")
        entry = info["entry"]
        sym_pins = KNOWN_SYMBOLS.get(entry, {})
        return {
            pin_name: pin_schematic_pos(info["x"], info["y"], info["angle"], px, py)
            for pin_name, (px, py) in sym_pins.items()
        }

    def _update_symbol_position(self, ref, x, y, angle=None):
        """Update symbol origin and index without touching attached geometry."""
        info = self.symbols.get(ref)
        if not info:
            raise ValueError(f"Symbol {ref} not found")
        sym = info["sym"]
        sym.position.X = x
        sym.position.Y = y
        if angle is not None:
            sym.position.angle = angle
        info["x"] = x
        info["y"] = y
        info["angle"] = sym.position.angle or 0

    def shift_symbol_properties(self, ref, dx, dy, angle=None):
        """Shift all symbol properties by a delta, preserving relative offsets."""
        info = self.symbols.get(ref)
        if not info:
            raise ValueError(f"Symbol {ref} not found")
        sym = info["sym"]
        for p in sym.properties:
            p.position.X = round(p.position.X + dx, 2)
            p.position.Y = round(p.position.Y + dy, 2)
            if angle is not None:
                p.position.angle = angle

    def move_symbol_only(self, ref, x, y, angle=None):
        """Move a symbol without adjusting properties or wires."""
        self._update_symbol_position(ref, x, y, angle=angle)

    def move_symbol_with_default_text(self, ref, x, y, angle=None):
        """Move a symbol and reset common property positions to the default layout."""
        self._update_symbol_position(ref, x, y, angle=angle)
        info = self.symbols[ref]
        a = angle if angle is not None else info["angle"]
        sym = info["sym"]
        for p in sym.properties:
            if p.key == "Reference":
                p.position = Position(X=x, Y=y - 3.81 if a == 0 else y, angle=a)
            elif p.key == "Value":
                p.position = Position(X=x, Y=y + 3.81 if a == 0 else y, angle=a)
            elif p.key in ("Footprint", "Datasheet", "Description"):
                p.position = Position(X=x, Y=y)

    def shift_wires_touching_points(self, points, dx, dy, tolerance=0.1):
        """Move wire endpoints that sit on any of the given coordinates."""
        for gi in self.sch.graphicalItems:
            if getattr(gi, "type", None) != "wire" or len(getattr(gi, "points", [])) != 2:
                continue
            for p in gi.points:
                if any(abs(p.X - x) < tolerance and abs(p.Y - y) < tolerance for x, y in points):
                    p.X = round(p.X + dx, 2)
                    p.Y = round(p.Y + dy, 2)

    def move_symbol_with_attached_wires(self, ref, x, y, angle=None, tolerance=0.1, move_properties=True):
        """Move a symbol and drag wire endpoints that were attached to its pins."""
        info = self.symbols.get(ref)
        if not info:
            raise ValueError(f"Symbol {ref} not found")
        before = list(self.symbol_pin_positions(ref).values())
        dx = round(x - info["x"], 2)
        dy = round(y - info["y"], 2)
        self._update_symbol_position(ref, x, y, angle=angle)
        self.shift_wires_touching_points(before, dx, dy, tolerance=tolerance)
        if move_properties:
            self.shift_symbol_properties(ref, dx, dy, angle=angle)

    def move(self, ref, x, y, angle=None):
        """Move a component and reset visible property placement.

        Does NOT redraw wires — call wire() or wire_between() after moving.
        """
        self.move_symbol_with_default_text(ref, x, y, angle=angle)

    def wire(self, x1, y1, x2, y2):
        """Add a wire between two absolute coordinates."""
        w = Connection()
        w.points = [
            Position(X=round(x1, 2), Y=round(y1, 2)),
            Position(X=round(x2, 2), Y=round(y2, 2)),
        ]
        w.stroke = Stroke(width=0, type="solid")
        self.sch.graphicalItems.append(w)

    def wire_between(self, pin_a, pin_b):
        """Add a wire between two pin specs (e.g., 'BOOT1@U1', 'C5.2')."""
        ax, ay = self._resolve_pin(pin_a)
        bx, by = self._resolve_pin(pin_b)
        self.wire(ax, ay, bx, by)

    def wire_L(self, pin_a, pin_b, via_x=None, via_y=None):
        """Route an L-shaped wire between two pins through an intermediate point.

        If via_x is given: horizontal from A to via_x, then vertical to B.
        If via_y is given: vertical from A to via_y, then horizontal to B.
        """
        ax, ay = self._resolve_pin(pin_a) if isinstance(pin_a, str) else pin_a
        bx, by = self._resolve_pin(pin_b) if isinstance(pin_b, str) else pin_b
        if via_x is not None:
            self.wire(ax, ay, via_x, ay)
            self.wire(via_x, ay, via_x, by)
            if abs(via_x - bx) > 0.01:
                self.wire(via_x, by, bx, by)
        elif via_y is not None:
            self.wire(ax, ay, ax, via_y)
            self.wire(ax, via_y, bx, via_y)
            if abs(via_y - by) > 0.01:
                self.wire(bx, via_y, bx, by)
        else:
            # Default: horizontal then vertical
            self.wire(ax, ay, bx, ay)
            self.wire(bx, ay, bx, by)

    def label(self, text, x, y, angle=0, justify="left", shape="passive"):
        """Add a global label at the given position."""
        if not self.sch.globalLabels:
            raise RuntimeError("No existing labels to clone from")
        gl = copy.deepcopy(self.sch.globalLabels[0])
        gl.text = text
        gl.shape = shape
        gl.position = Position(X=round(x, 2), Y=round(y, 2), angle=angle)
        gl.effects = copy.deepcopy(self.sch.globalLabels[0].effects)
        gl.effects.justify = Justify(horizontally=justify, vertically=None, mirror=False)
        self.sch.globalLabels.append(gl)

    def label_at(self, text, pin_spec, angle=0, justify="left", shape="passive"):
        """Add a global label at a pin position."""
        x, y = self._resolve_pin(pin_spec)
        self.label(text, x, y, angle, justify, shape)

    def gnd_label(self, pin_spec, angle=0, justify="right"):
        """Add a SYS_GND label at a pin position."""
        self.label_at("SYS_GND", pin_spec, angle, justify)

    def wire_stub_label(self, pin_spec, text, length=7.62, direction="left",
                        shape="passive", justify=None):
        """Draw a short wire from a pin and place a label at the end.

        direction: 'left', 'right', 'up', 'down'
        """
        px, py = self._resolve_pin(pin_spec)
        dx = {"left": -length, "right": length, "up": 0, "down": 0}[direction]
        dy = {"left": 0, "right": 0, "up": -length, "down": length}[direction]
        ex, ey = px + dx, py + dy
        self.wire(px, py, ex, ey)

        if justify is None:
            justify = {"left": "right", "right": "left", "up": "left", "down": "left"}[direction]
        angle = {"left": 0, "right": 0, "up": 90, "down": 270}[direction]
        self.label(text, ex, ey, angle, justify, shape)

    def clear_wires(self):
        """Remove all wires from the schematic."""
        self.sch.graphicalItems = []

    def clear_labels(self):
        """Remove all global labels from the schematic."""
        self.sch.globalLabels = []

    def remove_wires_touching(self, x, y, tolerance=0.1):
        """Remove wires that have an endpoint near (x, y)."""
        self.sch.graphicalItems = [
            gi for gi in self.sch.graphicalItems
            if not (hasattr(gi, 'points') and gi.points and
                    any(abs(p.X - x) < tolerance and abs(p.Y - y) < tolerance
                        for p in gi.points))
        ]

    def remove_labels_at(self, x, y, tolerance=0.1):
        """Remove labels near (x, y)."""
        self.sch.globalLabels = [
            gl for gl in self.sch.globalLabels
            if not (abs(gl.position.X - x) < tolerance and
                    abs(gl.position.Y - y) < tolerance)
        ]

    def pin_pos(self, spec):
        """Get absolute schematic position of a pin. Returns (x, y)."""
        return self._resolve_pin(spec)

    def save(self, filepath=None):
        """Save the schematic, preserving original lib_symbols section.

        kiutils reformats lib_symbols during roundtrip, which breaks
        pin connectivity for pins added via raw text. This method
        writes via kiutils, then restores the original lib_symbols.
        """
        import re
        target = filepath or self.filepath
        self.sch.to_file(target)

        # Restore original lib_symbols section
        with open(target) as f:
            new_content = f.read()

        orig_libs = self._extract_lib_symbols(self._original_content)
        new_libs = self._extract_lib_symbols(new_content)

        if orig_libs and new_libs:
            new_content = new_content.replace(new_libs, orig_libs)
            with open(target, 'w') as f:
                f.write(new_content)

    @staticmethod
    def _extract_lib_symbols(content):
        """Extract the (lib_symbols ...) block from schematic content."""
        start = content.find("(lib_symbols")
        if start < 0:
            return ""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    return content[start:i + 1]
            i += 1
        return ""


if __name__ == "__main__":
    # Quick self-test
    print("Testing LayoutEditor...")

    # Test pin resolution (without loading a real file)
    from pin_calc import pin_schematic_pos
    x, y = pin_schematic_pos(106.68, 63.5, 0, -12.7, 5.08)
    assert abs(x - 93.98) < 0.01 and abs(y - 58.42) < 0.01
    print("  pin_calc: OK")

    x, y = pin_schematic_pos(76.2, 68.58, 0, 5.08, 0)
    assert abs(x - 81.28) < 0.01 and abs(y - 68.58) < 0.01
    print("  passive2 pin2: OK")

    x, y = pin_schematic_pos(86.36, 77.47, 90, -5.08, 0)
    assert abs(x - 86.36) < 0.01 and abs(y - 82.55) < 0.01
    print("  passive2@90 pin1: OK")

    print("All tests PASS")
