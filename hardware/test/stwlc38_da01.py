#!/usr/bin/env python3
"""Experimental, pinned DA01 config-only workflow. Default: OFFLINE validation.

No hardware is opened unless --inspect-device or --program is specified.
DA01 is a bench experiment, not an approved heater/thermal configuration.
Do not run --program without a fresh physical bench-safety confirmation.
See 2026-09-26-stwlc38-ntc-candidate.md for provenance and remaining gates.
"""
import argparse
import hashlib
from pathlib import Path

from stwlc38_program import CP2112, STWLC38, FIRMWARE, CONFIG_NAME, log, parse_memh

SERIAL = "00E1E3D6"
SOURCE_HASH = "ba9a1cc8e4915c3ebfc65410ee237bb87c2e6e70d27004d94d04a38176d1e542"
CANDIDATE = Path(__file__).parent / "candidates" / (
    "STWLC38JRM_Config_DA01_cut1.2_EPP12V_NTC600mV_UNVALIDATED.memh"
)
CANDIDATE_HASH = "09a3a6e379bb09d29a3a27a5cb3b1644465bd9dcac1bc91a1809b3291ed8b03c"
BEFORE_IDS = (0x1656, 0x1078)
AFTER_IDS = (0x1656, 0xDA01)
SECTORS = ((126, 0, 256), (127, 256, 128))


def config_crc(data):
    """CRC-32/BZIP2 over file-byte order, not reflected zlib.crc32."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            crc = ((crc << 1) ^ (0x04C11DB7 if crc & 0x80000000 else 0)) & 0xFFFFFFFF
    return crc ^ 0xFFFFFFFF


def check_crc(data):
    if len(data) != 384:
        raise ValueError("WLC38 config must be exactly 384 bytes")
    if config_crc(data[:-4]) != int.from_bytes(data[-4:], "little"):
        raise ValueError("Configuration CRC mismatch")


def validate_candidate(data):
    """Also gate direct Python callers; accept only the pinned 96 MEMH words."""
    check_crc(data)
    canonical = "".join(
        f"{int.from_bytes(data[i:i + 4], 'little'):08X}\n" for i in range(0, 384, 4)
    ).encode("ascii")
    if hashlib.sha256(canonical).hexdigest() != CANDIDATE_HASH:
        raise ValueError("Not the pinned experimental DA01 configuration")


def load_candidate(source=FIRMWARE / CONFIG_NAME, candidate=CANDIDATE):
    original_raw, raw = source.read_bytes(), candidate.read_bytes()
    if hashlib.sha256(original_raw).hexdigest() != SOURCE_HASH:
        raise ValueError("Reference config hash mismatch")
    if hashlib.sha256(raw).hexdigest() != CANDIDATE_HASH:
        raise ValueError("Candidate file hash mismatch")
    original, data = parse_memh(original_raw), parse_memh(raw)
    check_crc(original)
    validate_candidate(data)
    expected = bytearray(original)
    expected[:2] = (0xDA01).to_bytes(2, "little")
    for offset in (0x68, 0x6C, 0x70):
        expected[offset] |= 4
    expected[0x7A:0x7C] = (6000).to_bytes(2, "little")
    expected[-4:] = config_crc(expected[:-4]).to_bytes(4, "little")
    if data != expected:
        raise ValueError("Candidate has an unexpected parameter delta")
    return data


def ids(info):
    return info["patch"], info["config"]


def load_reference():
    raw = (FIRMWARE / CONFIG_NAME).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError("Reference config hash mismatch")
    data = parse_memh(raw)
    validate_reference(data)
    return data


def validate_reference(data):
    check_crc(data)
    canonical = "".join(
        f"{int.from_bytes(data[i:i + 4], 'little'):08X}\n" for i in range(0, 384, 4)
    ).encode("ascii")
    if hashlib.sha256(canonical).hexdigest() != SOURCE_HASH:
        raise ValueError("Not the pinned official 1078 configuration")


def require_source(device, expected=BEFORE_IDS):
    info = device.preflight()
    if ids(info) != expected:
        raise RuntimeError(
            f"Require patch {expected[0]:04X}/config {expected[1]:04X}; "
            "no automatic retry or overwrite"
        )
    return info


def test_both_buffers(device, config, expected=BEFORE_IDS):
    if device.allow_commit:
        raise RuntimeError("Buffer checks require NVM commits disabled")
    before = require_source(device, expected)
    try:
        device.prepare()
        for sector, offset, length in SECTORS:
            device.stage(sector, config[offset:offset + length])
            device.byte(0x0020, 0x20)
    finally:
        # No NVM commit is possible in this phase. Restore the original boot.
        device.reset()
    if device.preflight() != before:
        raise RuntimeError("Chip state changed during volatile buffer checks")


def program_da01(device, config, *, acknowledge_experimental=False):
    if not acknowledge_experimental:
        raise RuntimeError("Experimental programming acknowledgement required")
    validate_candidate(config)
    return _program_config(device, config, BEFORE_IDS, AFTER_IDS, "da01_boot_ids_verified")


def restore_1078(device, config, *, acknowledge_unprotected=False):
    if not acknowledge_unprotected:
        raise RuntimeError("Unprotected comparison acknowledgement required")
    validate_reference(config)
    return _program_config(device, config, AFTER_IDS, BEFORE_IDS, "1078_restore_verified")


def _program_config(device, config, before_ids, after_ids, event):
    if device.allow_commit or device.commits_attempted:
        raise RuntimeError("Require a fresh device session with commits disabled")
    test_both_buffers(device, config, before_ids)
    require_source(device, before_ids)
    device.prepare()
    device.allow_commit = True
    try:
        # Config-only branch: never select or rewrite a patch sector.
        for sector, offset, length in SECTORS:
            device.stage(sector, config[offset:offset + length])
            device.byte(0x0020, 4)
            for _ in range(20):
                device.sleep(0.001)
                if device.read(0x0020, 1)[0] & 4 == 0:
                    break
            else:
                raise TimeoutError(f"Sector {sector} commit timed out; do not retry")
            device.byte(0x0020, 0x20)
            log("config_sector_committed", sector=sector, bytes=length)
        device.reset()
        after = device.preflight()
        if ids(after) != after_ids:
            raise RuntimeError("Post-reset IDs mismatch; do not retry automatically")
        log(event, **after, thermal_validation=False,
            cold_power_cycle_required=True, full_nvm_readback=False)
        return after
    finally:
        # No reset/retry on a partial NVM failure; retain state for diagnosis.
        device.allow_commit = False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--inspect-device", action="store_true")
    mode.add_argument("--program", action="store_true")
    mode.add_argument("--restore-1078", action="store_true")
    parser.add_argument("--serial")
    parser.add_argument("--dc-5v-heater-disconnected", action="store_true")
    parser.add_argument("--acknowledge-experimental-da01", action="store_true")
    parser.add_argument("--acknowledge-unprotected-comparison", action="store_true")
    args = parser.parse_args(argv)
    if args.program and not (args.dc_5v_heater_disconnected and args.acknowledge_experimental_da01):
        parser.error("Freshly confirm stable external 5V, no Qi, insulated heater H+, and experimental DA01")
    if args.restore_1078 and not (
        args.dc_5v_heater_disconnected and args.acknowledge_unprotected_comparison
    ):
        parser.error("Restore comparison requires external 5V, no Qi and insulated heater H+")
    hardware = args.inspect_device or args.program or args.restore_1078
    if hardware and args.serial != SERIAL:
        parser.error(f"Explicit bench adapter serial {SERIAL} required")
    config = load_reference() if args.restore_1078 else load_candidate()
    log("config_offline_validated", sha256=SOURCE_HASH if args.restore_1078 else CANDIDATE_HASH,
        bytes=len(config), config_id=f"0x{int.from_bytes(config[:2], 'little'):04X}",
        crc=f"0x{int.from_bytes(config[-4:], 'little'):08X}", sectors=[126, 127],
        patch_rewrite=False, thermal_validation=False)
    if not hardware:
        return 0
    bus = CP2112(args.serial)
    device = STWLC38(bus)
    try:
        if args.program:
            program_da01(device, config, acknowledge_experimental=True)
        elif args.restore_1078:
            restore_1078(device, config, acknowledge_unprotected=True)
        else:
            info = device.preflight()
            if ids(info) not in (BEFORE_IDS, AFTER_IDS):
                raise RuntimeError("Unexpected patch/config pair")
            log("da01_device_inspected", **info, writes_to_stwlc38=0)
        return 0
    except Exception as exc:
        log("aborted", reason=str(exc), commits_attempted=device.commits_attempted)
        return 1
    finally:
        bus.close()


if __name__ == "__main__":
    raise SystemExit(main())
