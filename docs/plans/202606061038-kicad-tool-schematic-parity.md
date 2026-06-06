# TODO: kicad-tool PCB validate schematic parity

- Update `kicad-tool pcb validate` so its DRC step invokes KiCad CLI with `--schematic-parity` by default.
- Do not add a new user-facing `kicad-tool` flag for this; parity checking should be part of the default validate behavior.
- Ensure the validate summary reports schematic parity field mismatches such as footprint/symbol property differences, not only missing or extra board items.
