# KiCad Schematic File Format (.kicad_sch) Specification

Source: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
Source: https://dev-docs.kicad.org/en/file-formats/sexpr-intro/
Fetched: 2026-04-12

## File Structure Overview

A `.kicad_sch` file uses S-expression format. Sections appear in this order:

1. Header (required)
2. Unique Identifier
3. Page Settings
4. Title Block
5. Library Symbol Definitions
6. Junctions
7. No Connect markers
8. Bus Entries
9. Wires and Buses
10. Images
11. Graphical Lines (polyline)
12. Graphical Text
13. Local Labels
14. Global Labels
15. Hierarchical Labels
16. Symbols
17. Hierarchical Sheets
18. Root Sheet Instance

---

## Root / Header

```sexpr
(kicad_sch
  (version VERSION)              ;; YYYYMMDD date format, required
  (generator GENERATOR)          ;; program identifier string, required
  (generator_version VERSION)    ;; generator version string (v8+, undocumented)
  (uuid UUID)                    ;; required, Version 4 random UUID
  ;; ...sections...
  (embedded_fonts yes|no)        ;; v8+, undocumented
)
```

NOTE: `generator_version` and `embedded_fonts` are used by KiCad v8+ but not yet in official docs.

---

## Common Tokens

### Position Identifier

```sexpr
(at X Y [ANGLE])
```
- X, Y: float coordinates
- ANGLE: optional float, degrees (symbol text uses tenths of a degree)

### Coordinate Point List

```sexpr
(pts
  (xy X Y)
  ...
)
```

### Stroke Definition

```sexpr
(stroke
  (width WIDTH)                  ;; float
  (type TYPE)                    ;; dash|dash_dot|dash_dot_dot|dot|default|solid
  (color R G B A)                ;; 0-255 integers + alpha
)
```

### Fill Definition

```sexpr
(fill
  (type none|outline|background) ;; fill type
  (color R G B A)                ;; optional, v7+
)
```

### Text Effects

```sexpr
(effects
  (font
    [(face FACE_NAME)]           ;; TrueType font family or "KiCad Font", optional
    (size HEIGHT WIDTH)          ;; float
    [(thickness THICKNESS)]      ;; float, optional
    [bold]                       ;; bare token, optional
    [italic]                     ;; bare token, optional
    [(line_spacing SPACING)]     ;; float, optional
    [(color R G B A)]            ;; optional, v7+
  )
  [(justify [left|right] [top|bottom] [mirror])]  ;; optional
  [hide]                         ;; bare token, optional
  [(href URL)]                   ;; optional, v7+
)
```

### Page Settings

```sexpr
(paper PAPER_SIZE [portrait])
;; or
(paper WIDTH HEIGHT [portrait])
```

Valid sizes: A0, A1, A2, A3, A4, A5, A, B, C, D, E

### Title Block

```sexpr
(title_block
  [(title "TITLE")]
  [(date "YYYY-MM-DD")]
  [(rev "REVISION")]
  [(company "COMPANY")]
  [(comment N "COMMENT")]        ;; N = 1-9
)
```

### Property

```sexpr
(property
  "KEY"                          ;; string, must be unique within parent
  "VALUE"                        ;; string
  [(id N)]                       ;; int, required in v6, optional v7+
  (at X Y [ANGLE])               ;; position
  [(show_name [yes|no])]         ;; v7+, bare (show_name) = yes
  [(do_not_autoplace [yes|no])]  ;; v8+, undocumented
  [(effects ...)]                ;; optional text effects
)
```

### UUID

```sexpr
(uuid UUID)                      ;; Version 4 random UUID
```

### Image

```sexpr
(image
  (at X Y)
  [(scale SCALAR)]               ;; float, optional
  [(layer LAYER)]                ;; optional
  (uuid UUID)
  (data "BASE64_PNG_DATA"...)    ;; MIME base64 encoded PNG
)
```

---

## Schematic Elements

### Junction

```sexpr
(junction
  (at X Y)
  (diameter DIAMETER)            ;; float, default 0
  (color R G B A)
  (uuid UUID)
)
```

### No Connect

```sexpr
(no_connect
  (at X Y)
  (uuid UUID)
)
```

### Bus Entry

```sexpr
(bus_entry
  (at X Y)
  (size X Y)
  (stroke ...)
  (uuid UUID)
)
```

### Wire

```sexpr
(wire
  (pts (xy X1 Y1) (xy X2 Y2) ...)
  (stroke ...)
  (uuid UUID)
)
```

### Bus

```sexpr
(bus
  (pts (xy X1 Y1) (xy X2 Y2) ...)
  (stroke ...)
  (uuid UUID)
)
```

### Polyline (Graphical Line)

```sexpr
(polyline
  (pts (xy X1 Y1) (xy X2 Y2) ...)
  (stroke ...)
  (uuid UUID)
)
```

### Text

```sexpr
(text "TEXT"
  (exclude_from_sim yes|no)      ;; v8+, undocumented
  (at X Y [ANGLE])
  (effects ...)
  (uuid UUID)
)
```

### Text Box

```sexpr
(text_box "TEXT"
  (exclude_from_sim yes|no)      ;; v8+, undocumented
  (at X Y [ANGLE])
  (size W H)
  (stroke ...)
  (fill ...)
  (effects ...)
  (uuid UUID)
)
```

### Local Label

```sexpr
(label "TEXT"
  (at X Y ANGLE)
  [(fields_autoplaced)]
  (effects ...)
  (uuid UUID)
)
```

### Global Label

```sexpr
(global_label "TEXT"
  (shape input|output|bidirectional|tri_state|passive)
  [(fields_autoplaced)]
  (at X Y ANGLE)
  (effects ...)
  (uuid UUID)
  [(property ...)]               ;; inter-sheet reference properties
)
```

### Hierarchical Label

```sexpr
(hierarchical_label "TEXT"
  (shape input|output|bidirectional|tri_state|passive)
  (at X Y ANGLE)
  (effects ...)
  (uuid UUID)
)
```

### Netclass Flag (v7+)

```sexpr
(netclass_flag "TEXT"
  (length LENGTH)
  (shape round|rectangle|dot|diamond)
  [(fields_autoplaced)]
  (at X Y ANGLE)
  (effects ...)
  (uuid UUID)
  [(property ...)]
)
```

---

## Symbol Instance (in schematic)

```sexpr
(symbol
  [(lib_name "EDITED_LIB_NAME")]  ;; only if edited in schematic
  (lib_id "LIBRARY:SYMBOL")
  (at X Y [ANGLE])
  [(mirror x|y)]
  (unit UNIT)
  (exclude_from_sim yes|no)       ;; v8+, undocumented
  (in_bom yes|no)
  (on_board yes|no)
  [(dnp yes|no)]                  ;; v7+
  [(fields_autoplaced)]
  (uuid UUID)
  (property ...)                  ;; 0 or more
  (pin "NUMBER" (uuid UUID))      ;; 0 or more
  (instances
    (project "PROJECT_NAME"       ;; 1 or more, sorted alphabetically
      (path "PATH"
        (reference "REF")
        (unit UNIT)
      )
    )
  )
)
```

---

## Hierarchical Sheet

```sexpr
(sheet
  (at X Y)
  (size WIDTH HEIGHT)
  (exclude_from_sim yes|no)       ;; v8+, undocumented
  (in_bom yes|no)                 ;; v8+, undocumented
  (on_board yes|no)               ;; v8+, undocumented
  (dnp yes|no)                    ;; v8+, undocumented
  [(fields_autoplaced)]
  (stroke ...)
  (fill (color R G B A))
  (uuid UUID)
  (property "Sheetname" "NAME" ...) ;; required, sheet name
  (property "Sheetfile" "FILE" ...) ;; required, file path
  (pin "NAME" input|output|bidirectional|tri_state|passive
    (at X Y ANGLE)
    (effects ...)
    (uuid UUID)
  )
  (instances
    (project "PROJECT_NAME"
      (path "PATH"
        (page "PAGE")
      )
    )
  )
)
```

---

## Library Symbol Definition (inside lib_symbols)

```sexpr
(symbol "LIBRARY_ID"
  [(extends "PARENT_LIBRARY_ID")]
  [(pin_numbers [hide])]          ;; or (pin_numbers (hide no))
  [(pin_names [(offset OFFSET)] [hide])]
  (exclude_from_sim yes|no)       ;; v8+, undocumented
  (in_bom yes|no)
  (on_board yes|no)
  [(power)]                       ;; bare token, power symbol flag
  (property "KEY" "VALUE" (id N) (at X Y ANGLE) (effects ...))  ;; mandatory: Reference, Value, Footprint, Datasheet
  ;; child units:
  (symbol "UNIT_ID"
    ;; graphic items:
    (arc (start X Y) (mid X Y) (end X Y) (stroke ...) (fill ...))
    (circle (center X Y) (radius R) (stroke ...) (fill ...))
    (polyline (pts ...) (stroke ...) (fill ...))
    (rectangle (start X Y) (end X Y) (stroke ...) (fill ...))
    (bezier (pts ...) (stroke ...) (fill ...))
    (text "TEXT" (at X Y ANGLE) (effects ...))
    (text_box "TEXT" (at X Y ANGLE) (size W H) (stroke ...) (fill ...) (effects ...))
    ;; pins:
    (pin ELECTRICAL_TYPE GRAPHIC_STYLE
      (at X Y ANGLE)
      (length LENGTH)
      [hide]
      (name "NAME" (effects ...))
      (number "NUMBER" (effects ...))
      [(alternate "NAME" ELECTRICAL_TYPE GRAPHIC_STYLE)]
    )
  )
)
```

### Pin Electrical Types
input, output, bidirectional, tri_state, passive, free, unspecified,
power_in, power_out, open_collector, open_emitter, no_connect

### Pin Graphic Styles
line, inverted, clock, inverted_clock, input_low, clock_low,
output_low, edge_clock_high, non_logic

---

## Sheet/Symbol Instances

### sheet_instances (legacy, pre-v7)

```sexpr
(sheet_instances
  (path "/"
    (page "1")
  )
)
```

### symbol_instances (legacy, pre-v7)

```sexpr
(symbol_instances
  (path "/UUID"
    (reference "REF")
    (unit UNIT)
    (value "VALUE")
    (footprint "FOOTPRINT")
  )
)
```

---

## Reserved Property Keys

- `ki_keywords`: Search keywords
- `ki_description`: Symbol description
- `ki_locked`: Prevents footprint changes
- `ki_fp_filters`: Footprint filter patterns (space-separated)
