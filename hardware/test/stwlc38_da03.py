#!/usr/bin/env python3
"""DA03 signed-NTC diagnostic. No NTC shutdown; default is offline only."""
import argparse
from pathlib import Path

from stwlc38_da01 import SERIAL, _program_config, check_crc, config_crc, load_reference, validate_reference
from stwlc38_program import CP2112, STWLC38, log, parse_memh

SOURCE_IDS = (0x1656, 0xDA02)
TARGET_IDS = (0x1656, 0xDA03)
REFERENCE_IDS = (0x1656, 0x1078)
IMAGE = Path(__file__).parent / "candidates/STWLC38JRM_Config_DA03_NTC_SIGNED_DIAGNOSTIC.memh"


def validate(data):
    check_crc(data)
    expected = bytearray(load_reference())
    expected[:2] = (0xDA03).to_bytes(2, "little")
    expected[0x68] |= 4
    expected[0x7A:0x7C] = (-5461).to_bytes(2, "little", signed=True)
    expected[-4:] = config_crc(expected[:-4]).to_bytes(4, "little")
    if data != expected:
        raise ValueError("Not the exact DA03 diagnostic payload")


def load():
    data = parse_memh(IMAGE.read_bytes())
    validate(data)
    return data


def program(device, data, *, acknowledged=False, restore=False):
    if not acknowledged:
        raise RuntimeError("No-NTC-shutdown diagnostic acknowledgement required")
    if restore:
        validate_reference(data)
        return _program_config(device, data, TARGET_IDS, REFERENCE_IDS, "da03_restored")
    validate(data)
    return _program_config(device, data, SOURCE_IDS, TARGET_IDS, "da03_verified")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--program", action="store_true")
    mode.add_argument("--restore-1078", action="store_true")
    parser.add_argument("--serial")
    parser.add_argument("--dc-5v-heater-disconnected", action="store_true")
    parser.add_argument("--acknowledge-no-ntc-shutdown", action="store_true")
    args = parser.parse_args(argv)
    hardware = args.program or args.restore_1078
    if hardware and not (args.serial == SERIAL and args.dc_5v_heater_disconnected
                         and args.acknowledge_no_ntc_shutdown):
        parser.error("Require exact serial, external 5V with no Qi, disconnected heater and diagnostic acknowledgement")
    data = load_reference() if args.restore_1078 else load()
    log("offline_validated", config=hex(int.from_bytes(data[:2], "little")),
        bytes=len(data), diagnostic_only=True, ntc_shutdown=False)
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
