#!/usr/bin/env python3
"""Guarded STWLC38JRM cut-1.2 programming through a CP2112.

Default operation is read-only. --buffer-test resets the chip and tests its
volatile programming buffer, but NEVER issues the NVM commit command (0x04).
--program requires explicit bench-safety acknowledgements and validates each
buffer before committing. No automatic NVM retries or arbitrary firmware input.

The programming sequence is adapted from ST's BSD-3-Clause stwlc38.c (2023),
preserved at Andrew0050/STWirelessCharging-C-Drivers, commit
ea0110e4b7088c8dcd9d824da8c645105c26bc51. See stwlc38-programming.md for provenance,
limitations, and the accompanying ST license. HID framing follows SiLabs AN495.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import time


VID, PID, ADDRESS = 0x10C4, 0xEA90, 0x61
FIRMWARE = Path(__file__).resolve().parents[1] / "firmware" / "stwlc38"
PATCH_NAME = "STWLC38JRM_Patch_1656_rtx.memh"
CONFIG_NAME = "STWLC38JRM_Config_1078_cut1.2_EPP12V.memh"
PATCH_HASH = "5495b35e175f6fa1c1768e71306692035688e69677a72f423723a2ce27b2efef"
CONFIG_HASHES = {
    "ba9a1cc8e4915c3ebfc65410ee237bb87c2e6e70d27004d94d04a38176d1e542",
    "bff5fe71331070fd3bdb3b2c3d872481dad90ce8b62aed0aed0f91d57576ad6b",
}
TARGET_IDS = (0x1656, 0x1078)
SECTOR_SIZE = 256
CHUNK = 32  # Aligned payload; plus the 2-byte address is below CP2112's 61.


def log(event: str, **fields) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


class TransferError(RuntimeError):
    def __init__(self, status: int, detail: int, retries: int):
        super().__init__(f"SMBus status={status:#x} detail={detail:#x} retries={retries}")
        self.status, self.detail = status, detail


class CP2112:
    def __init__(self, serial: str):
        import hid

        matches = [d for d in hid.enumerate(VID, PID) if d.get("serial_number") == serial]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one CP2112 serial {serial}, found {len(matches)}")
        self.device = hid.device()
        self.device.open_path(matches[0]["path"])
        self.old_config = None
        try:
            old = bytes(self.device.get_feature_report(0x06, 14))
            if len(old) != 14 or old[0] != 0x06:
                raise RuntimeError("Malformed CP2112 SMBus configuration")
            self.old_config = old
            # Volatile settings only: 100 kHz, polling, bounded timeouts/retries.
            config = bytes([6]) + struct.pack(">IBBHHBH", 100000, 2, 0, 1000, 1000, 1, 1)
            self.device.send_feature_report(config)
            if bytes(self.device.get_feature_report(6, 14)) != config:
                raise RuntimeError("CP2112 configuration readback mismatch")
            self.send(bytes([0x17, 1]))
            for _ in range(16):
                if not self.device.read(64, timeout_ms=5):
                    break
            else:
                raise RuntimeError("CP2112 input queue did not drain")
        except Exception:
            self.close()
            raise

    def close(self):
        try:
            if self.old_config is not None:
                self.device.send_feature_report(self.old_config)
        finally:
            self.device.close()

    def send(self, report: bytes):
        if not 1 <= len(report) <= 64:
            raise ValueError("Invalid HID report length")
        packet = report.ljust(64, b"\x00")
        if self.device.write(packet) != 64:
            raise RuntimeError("Short HID report write")

    def status(self, expected_read: int = 0):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            self.send(bytes([0x15, 1]))
            r = self.device.read(64, timeout_ms=200)
            if not r or r[0] != 0x16 or len(r) < 7:
                raise RuntimeError("Missing/malformed SMBus status response")
            if r[1] == 3:
                raise TransferError(r[1], r[2], (r[3] << 8) | r[4])
            if r[1] == 2:
                count = (r[5] << 8) | r[6]
                if expected_read and count != expected_read:
                    raise RuntimeError(f"Incomplete SMBus read: {count}/{expected_read}")
                return
            if r[1] not in (0, 1):
                raise RuntimeError(f"Unknown SMBus status: {r[1]}")
            time.sleep(0.002)
        self.send(bytes([0x17, 1]))
        raise TimeoutError("SMBus transfer timed out; cancelled")

    def read(self, pointer: bytes, count: int) -> bytes:
        if not 1 <= len(pointer) <= 16 or not 1 <= count <= 61:
            raise ValueError("Invalid read dimensions")
        self.send(bytes([0x11, ADDRESS << 1, 0, count, len(pointer)]) + pointer)
        self.status(count)
        self.send(bytes([0x12, 0, count]))
        r = self.device.read(64, timeout_ms=500)
        if (len(r) < 3 + count or r[0] != 0x13 or r[1] == 3 or r[2] != count):
            raise RuntimeError(f"Incomplete/invalid data response: {r}")
        return bytes(r[3:3 + count])

    def write(self, payload: bytes):
        if not 1 <= len(payload) <= 61:
            raise ValueError("CP2112 write exceeds 61 bytes")
        self.send(bytes([0x14, ADDRESS << 1, len(payload)]) + payload)
        self.status()


def parse_memh(raw: bytes) -> bytes:
    words = raw.decode("ascii").split()
    if not words or any(re.fullmatch(r"[0-9a-fA-F]{8}", w) is None for w in words):
        raise ValueError("Expected plain 32-bit hexadecimal words")
    return b"".join(int(word, 16).to_bytes(4, "little") for word in words)


def load_images(directory: Path = FIRMWARE) -> tuple[bytes, bytes]:
    images = []
    for name, hashes, maximum in (
        (PATCH_NAME, {PATCH_HASH}, 126 * SECTOR_SIZE),
        (CONFIG_NAME, CONFIG_HASHES, 2 * SECTOR_SIZE),
    ):
        raw = (directory / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest not in hashes:
            raise ValueError(f"Unapproved firmware checksum: {name}: {digest}")
        data = parse_memh(raw)
        if not 0 < len(data) <= maximum:
            raise ValueError(f"Invalid image size: {name}: {len(data)}")
        log("image_validated", file=name, sha256=digest, bytes=len(data))
        images.append(data)
    if int.from_bytes(images[1][:2], "little") != TARGET_IDS[1]:
        raise ValueError("Configuration ID mismatch")
    return images[0], images[1]


class STWLC38:
    def __init__(self, bus, allow_commit: bool = False, sleep=time.sleep):
        self.bus, self.allow_commit, self.sleep = bus, allow_commit, sleep
        self.commits_attempted = 0

    def read(self, reg: int, count: int) -> bytes:
        return b"".join(
            self.bus.read((reg + offset).to_bytes(2, "big"), min(CHUNK, count - offset))
            for offset in range(0, count, CHUNK)
        )

    def write(self, reg: int, data: bytes):
        # Safety gate applies to every path to the irreversible command.
        if reg <= 0x0020 < reg + len(data) and data[0x0020 - reg] & 4:
            if not self.allow_commit:
                raise RuntimeError("NVM commit forbidden in this mode")
            self.commits_attempted += 1
        for offset in range(0, len(data), CHUNK):
            payload = (reg + offset).to_bytes(2, "big") + data[offset:offset + CHUNK]
            self.bus.write(payload)

    def byte(self, reg: int, value: int):
        self.write(reg, bytes([value]))

    def info(self) -> dict:
        raw = self.read(0, 15)
        word = lambda i: int.from_bytes(raw[i:i + 2], "little")
        cut = self.bus.read(bytes.fromhex("fa2001c002"), 1)[0]
        return dict(chip=word(0), revision=raw[2], rom=word(4), patch=word(6),
                    config=word(10), mode=raw[14], cut=cut,
                    errors=int.from_bytes(self.read(0x002C, 4), "little"))

    def preflight(self) -> dict:
        info = self.info()
        log("chip_info", **info)
        if (info["chip"], info["revision"], info["rom"], info["cut"]) != (0x26, 3, 0x161, 3):
            raise RuntimeError("Unsupported chip/revision/ROM/cut; no writes made")
        if info["mode"] != 1:
            raise RuntimeError("Not in standalone/DC mode; no writes made")
        if info["errors"]:
            raise RuntimeError("Existing system/NVM error; no writes made")
        return info

    def reset(self):
        try:
            self.bus.write(bytes.fromhex("fa2001f20001"))
        except TransferError as exc:
            # ST documents a NACK on the reset command. No other errors ignored.
            if exc.status != 3 or exc.detail not in (0, 4):
                raise
            log("reset_nack", detail=exc.detail)
        self.sleep(0.1)

    def prepare(self):
        # ST reference sequence: reboot without NVM loading, then unlock.
        try:
            self.byte(0x0020, 0x40)
        except TransferError as exc:
            if exc.status != 3 or exc.detail not in (0, 4):
                raise
            log("reset_without_nvm_nack", detail=exc.detail)
        self.sleep(0.1)
        if self.read(0x000E, 1) != b"\x01":
            raise RuntimeError("DC mode lost after reset")
        self.byte(0x0022, 0xC5)

    def stage(self, sector: int, data: bytes):
        if not 0 <= sector < 128 or not 0 < len(data) <= SECTOR_SIZE:
            raise ValueError("Invalid sector dimensions")
        self.byte(0x0024, sector)
        self.byte(0x0020, 0x10)
        self.write(0x0180, data)
        actual = self.read(0x0180, len(data))
        if actual != data:
            mismatch = next(i for i, (a, b) in enumerate(zip(actual, data)) if a != b)
            raise RuntimeError(f"Buffer mismatch in sector {sector} at offset {mismatch}; NOT committed")

    def buffer_test(self, sample: bytes):
        if self.allow_commit:
            raise RuntimeError("Buffer test requires commits disabled")
        before = self.preflight()
        try:
            self.prepare()
            self.stage(126, sample[:SECTOR_SIZE])
            self.byte(0x0020, 0x20)
        finally:
            self.reset()
        after = self.preflight()
        if after != before:
            raise RuntimeError("Chip information changed after buffer test")
        log("buffer_test_passed", bytes=min(len(sample), SECTOR_SIZE), commits=0)

    def program(self, patch: bytes, config: bytes):
        if not self.allow_commit:
            raise RuntimeError("Programming not enabled")
        if not 0 < len(patch) <= 126 * SECTOR_SIZE or not 0 < len(config) <= 512:
            raise ValueError("Invalid image dimensions")
        before = self.preflight()
        if (before["patch"], before["config"]) == TARGET_IDS:
            log("already_programmed")
            return
        self.prepare()
        # No automatic retry. On a partial failure, preserve state for diagnosis.
        for name, data, start in (("patch", patch, 0), ("config", config, 126)):
            for offset in range(0, len(data), SECTOR_SIZE):
                sector = start + offset // SECTOR_SIZE
                self.stage(sector, data[offset:offset + SECTOR_SIZE])
                self.byte(0x0020, 4)
                for _ in range(20):
                    self.sleep(0.001)
                    if self.read(0x0020, 1)[0] & 4 == 0:
                        break
                else:
                    raise TimeoutError(f"NVM sector {sector} timed out; do not retry automatically")
                self.byte(0x0020, 0x20)
                log("sector_committed", image=name, sector=sector)
        self.reset()
        after = self.preflight()
        if (after["patch"], after["config"]) != TARGET_IDS:
            raise RuntimeError("Post-reset firmware IDs do not match")
        log("programming_verified", **after)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--buffer-test", action="store_true")
    mode.add_argument("--program", action="store_true")
    parser.add_argument("--dc-5v-heater-disconnected", action="store_true")
    args = parser.parse_args()
    if (args.buffer_test or args.program) and not args.dc_5v_heater_disconnected:
        parser.error("Confirm stable external 5V, no Qi, and disconnected/insulated heater H+")
    patch, config = load_images()  # Reject corrupted inputs before opening hardware.
    bus = CP2112(args.serial)
    device = STWLC38(bus)
    try:
        if args.buffer_test or args.program:
            device.buffer_test(config)
        else:
            device.preflight()
        if args.program:
            device.allow_commit = True
            device.program(patch, config)
        return 0
    except Exception as exc:
        log("aborted", reason=str(exc), commits_attempted=device.commits_attempted)
        return 1
    finally:
        bus.close()


if __name__ == "__main__":
    raise SystemExit(main())
