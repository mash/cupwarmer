#!/usr/bin/env python3
"""DA04 prototype: signed NTC threshold and shutdown actions; thermally unvalidated."""
import argparse
from pathlib import Path

from stwlc38_da01 import SERIAL, _program_config, check_crc, config_crc, load_reference, validate_reference
from stwlc38_program import CP2112, STWLC38, log, parse_memh

SOURCE_IDS = (0x1656, 0xDA03)
TARGET_IDS = (0x1656, 0xDA04)
REFERENCE_IDS = (0x1656, 0x1078)
IMAGE = Path(__file__).parent / "candidates/STWLC38JRM_Config_DA04_NTC_SIGNED_PROTOTYPE.memh"


def validate(data):
    check_crc(data)
    expected = bytearray(load_reference())
    expected[:2] = (0xDA04).to_bytes(2, "little")
    for offset in (0x68, 0x6C, 0x70):
        expected[offset] |= 4
    expected[0x7A:0x7C] = (-5461).to_bytes(2, "little", signed=True)
    expected[-4:] = config_crc(expected[:-4]).to_bytes(4, "little")
    if data != expected:
        raise ValueError("Not the exact DA04 diagnostic payload")


def load():
    data = parse_memh(IMAGE.read_bytes())
    validate(data)
    return data


def program(device, data, *, acknowledged=False, restore=False):
    if not acknowledged:
        raise RuntimeError("Thermally unvalidated prototype acknowledgement required")
    if restore:
        validate_reference(data)
        return _program_config(device, data, TARGET_IDS, REFERENCE_IDS, "da04_restored")
    validate(data)
    return _program_config(device, data, SOURCE_IDS, TARGET_IDS, "da04_verified")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--program", action="store_true")
    mode.add_argument("--restore-1078", action="store_true")
    parser.add_argument("--serial")
    parser.add_argument("--dc-5v-heater-disconnected", action="store_true")
    parser.add_argument("--acknowledge-unvalidated-prototype", action="store_true")
    args = parser.parse_args(argv)
    hardware = args.program or args.restore_1078
    if hardware and not (args.serial == SERIAL and args.dc_5v_heater_disconnected
                         and args.acknowledge_unvalidated_prototype):
        parser.error("Require exact serial, external 5V with no Qi, disconnected heater and diagnostic acknowledgement")
    data = load_reference() if args.restore_1078 else load()
    log("offline_validated", config=hex(int.from_bytes(data[:2], "little")),
        bytes=len(data), thermal_validation=False, ntc_shutdown_configured=not args.restore_1078)
    if not hardware:
        return 0
    bus = CP2112(args.serial)
    device = STWLC38(bus)
    try:
        program(device, data, acknowledged=True, restore=args.restore_1078)
        return 0
    except Exception as exc:
        log("aborted", reason=str(exc), commits_attempted=device.commits_attempted)
        return 1
    finally:
        bus.close()


if __name__ == "__main__":
    raise SystemExit(main())
