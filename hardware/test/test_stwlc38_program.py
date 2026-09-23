"""Offline tests; no USB hardware is opened by this module."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from stwlc38_program import (
    CHUNK, CONFIG_NAME, CP2112, PATCH_NAME, STWLC38, TARGET_IDS,
    TransferError, load_images, parse_memh,
)


class FakeBus:
    def __init__(self):
        self.memory = bytearray(0x300)
        self.memory[:15] = bytes.fromhex("260003006101991200002610070001")
        self.writes = []
        self.reads = []
        self.commits = []
        self.corrupt = False
        self.timeout = False
        self.fail_staging = False
        self.reset_nack = False
        self.cut = 3

    def read(self, pointer, count):
        self.reads.append((pointer, count))
        if pointer == bytes.fromhex("fa2001c002"):
            return bytes([self.cut])
        address = int.from_bytes(pointer, "big")
        if address == 0x20 and self.timeout:
            return b"\x04"
        data = bytes(self.memory[address:address + count])
        if address == 0x180 and self.corrupt:
            return bytes([data[0] ^ 1]) + data[1:]
        return data

    def write(self, payload):
        if len(payload) > 61:
            raise AssertionError("Oversized CP2112 write")
        self.writes.append(payload)
        if payload == bytes.fromhex("fa2001f20001"):
            if self.commits:
                self.memory[6:8] = TARGET_IDS[0].to_bytes(2, "little")
                self.memory[10:12] = TARGET_IDS[1].to_bytes(2, "little")
            if self.reset_nack:
                raise TransferError(3, 0, 1)
            return
        address = int.from_bytes(payload[:2], "big")
        if address >= 0x180 and self.fail_staging:
            raise TransferError(3, 4, 1)
        data = payload[2:]
        self.memory[address:address + len(data)] = data
        if address == 0x20 and data == b"\x04":
            self.commits.append(self.memory[0x24])
            self.memory[0x20] = 0


class ProgrammingTests(unittest.TestCase):
    def setUp(self):
        self.bus = FakeBus()
        self.device = STWLC38(self.bus, sleep=lambda _: None)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_memh_little_endian(self):
        self.assertEqual(parse_memh(b"00001078\r\n12345678\n"), bytes.fromhex("7810000078563412"))

    def test_invalid_memh(self):
        for raw in (b"", b"@0010", b"123", b"123456789", b"zzzzzzzz"):
            with self.assertRaises(ValueError):
                parse_memh(raw)

    def test_approved_images(self):
        patch, cfg = load_images()
        self.assertEqual(len(patch), 27680)
        self.assertEqual(len(cfg), 384)
        self.assertEqual(cfg[:4], bytes.fromhex("78100000"))

    def test_modified_image_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / PATCH_NAME).write_bytes(b"12345678\n")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_images(root)

    def test_preflight_read_only(self):
        self.assertEqual(self.device.preflight()["mode"], 1)
        self.assertEqual(self.bus.writes, [])

    def test_reject_wrong_chip_revision_rom_mode_and_errors(self):
        for address, value in ((0, 0), (2, 4), (4, 0), (14, 2), (0x2C, 1)):
            bus = FakeBus()
            bus.memory[address] = value
            dev = STWLC38(bus, sleep=lambda _: None)
            with self.assertRaises(RuntimeError):
                dev.buffer_test(bytes(256))
            self.assertEqual(bus.writes, [])
        self.bus.cut = 4
        with self.assertRaises(RuntimeError):
            self.device.preflight()

    def test_buffer_test_no_commit(self):
        self.device.buffer_test(bytes(range(256)))
        self.assertEqual(self.bus.commits, [])
        self.assertEqual(self.device.commits_attempted, 0)
        blocks = [w for w in self.bus.writes if 0x180 <= int.from_bytes(w[:2], "big") < 0x280]
        self.assertEqual(len(blocks), 8)
        self.assertTrue(all(len(w) == CHUNK + 2 for w in blocks))
        self.assertEqual(b"".join(w[2:] for w in blocks), bytes(range(256)))
        self.assertEqual([int.from_bytes(w[:2], "big") for w in blocks], list(range(0x180, 0x280, 32)))
        self.assertEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))

    def test_buffer_corruption_never_commits_and_resets(self):
        self.bus.corrupt = True
        with self.assertRaisesRegex(RuntimeError, "Buffer mismatch"):
            self.device.buffer_test(bytes(256))
        self.assertEqual(self.bus.commits, [])
        self.assertEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))

    def test_commit_guard(self):
        for reg, data in ((0x20, b"\x04"), (0x1F, b"\x00\x04")):
            with self.assertRaisesRegex(RuntimeError, "forbidden"):
                self.device.write(reg, data)
        self.assertEqual(self.bus.writes, [])

    def test_program_requires_opt_in(self):
        with self.assertRaises(RuntimeError):
            self.device.program(bytes(256), bytes(384))
        self.assertEqual(self.bus.writes, [])

    def test_buffer_test_rejects_commit_enabled(self):
        self.device.allow_commit = True
        with self.assertRaises(RuntimeError):
            self.device.buffer_test(bytes(256))

    def test_program_sector_boundaries_and_partial_last_sector(self):
        self.device.allow_commit = True
        self.device.program(bytes(260), bytes(384))
        self.assertEqual(self.bus.commits, [0, 1, 126, 127])
        self.assertEqual(self.device.commits_attempted, 4)
        self.assertEqual(self.device.preflight()["patch"], TARGET_IDS[0])

    def test_full_image_sector_sequence(self):
        self.device.allow_commit = True
        self.device.program(*load_images())
        self.assertEqual(self.bus.commits, list(range(109)) + [126, 127])

    def test_corrupt_buffer_stops_before_first_commit(self):
        self.device.allow_commit = True
        self.bus.corrupt = True
        with self.assertRaises(RuntimeError):
            self.device.program(bytes(260), bytes(384))
        self.assertEqual(self.bus.commits, [])

    def test_transport_failure_stops_before_commit(self):
        self.device.allow_commit = True
        self.bus.fail_staging = True
        with self.assertRaises(TransferError):
            self.device.program(bytes(260), bytes(384))
        self.assertEqual(self.bus.commits, [])

    def test_timeout_does_not_retry_or_reset(self):
        self.device.allow_commit = True
        self.bus.timeout = True
        with self.assertRaises(TimeoutError):
            self.device.program(bytes(260), bytes(384))
        self.assertEqual(self.bus.commits, [0])
        self.assertNotIn(bytes.fromhex("fa2001f20001"), self.bus.writes)

    def test_skip_already_matching_ids(self):
        self.bus.memory[6:8] = TARGET_IDS[0].to_bytes(2, "little")
        self.bus.memory[10:12] = TARGET_IDS[1].to_bytes(2, "little")
        self.device.allow_commit = True
        self.device.program(bytes(260), bytes(384))
        self.assertEqual(self.bus.writes, [])

    def test_reset_nack_only_ignored_for_known_error(self):
        self.bus.reset_nack = True
        self.device.reset()
        def error(_):
            raise TransferError(3, 2, 1)
        self.bus.write = error
        with self.assertRaises(TransferError):
            self.device.reset()

    def test_invalid_dimensions(self):
        for index, data in ((128, b"x"), (-1, b"x"), (0, b""), (0, bytes(257))):
            with self.assertRaises(ValueError):
                self.device.stage(index, data)
        self.device.allow_commit = True
        for patch, config in ((b"", bytes(384)), (bytes(32257), bytes(384)), (bytes(4), bytes(513))):
            with self.assertRaises(ValueError):
                self.device.program(patch, config)
        self.assertEqual(self.bus.writes, [])


class FakeHID:
    def __init__(self, responses):
        self.responses = list(responses)
        self.sent = []

    def write(self, packet):
        self.sent.append(packet)
        return len(packet)

    def read(self, size, timeout_ms):
        return self.responses.pop(0) if self.responses else []


class HIDTests(unittest.TestCase):
    def bridge(self, responses):
        bus = CP2112.__new__(CP2112)
        bus.device = FakeHID(responses)
        return bus

    def test_read_framing(self):
        bus = self.bridge([[0x16, 2, 5, 0, 0, 0, 2], [0x13, 2, 2, 0x26, 0]])
        self.assertEqual(bus.read(b"\0\0", 2), b"\x26\0")
        self.assertEqual(bus.device.sent[0][:7], bytes.fromhex("11c20002020000"))
        self.assertTrue(all(len(p) == 64 for p in bus.device.sent))

    def test_write_framing(self):
        bus = self.bridge([[0x16, 2, 5, 0, 0, 0, 0]])
        bus.write(bytes.fromhex("01807810"))
        self.assertEqual(bus.device.sent[0][:7], bytes.fromhex("14c20401807810"))

    def test_nack(self):
        bus = self.bridge([[0x16, 3, 0, 0, 1, 0, 0]])
        with self.assertRaises(TransferError):
            bus.write(b"\0\0\x01")

    def test_incomplete_read(self):
        for responses in (
            [[0x16, 2, 5, 0, 0, 0, 1]],
            [[0x16, 2, 5, 0, 0, 0, 2], [0x13, 2, 1, 0x26]],
            [[0x16, 2, 5, 0, 0, 0, 2], [0x13, 3, 2, 0x26, 0]],
        ):
            with self.assertRaises(RuntimeError):
                self.bridge(responses).read(b"\0\0", 2)

    def test_oversize_rejected(self):
        bus = self.bridge([])
        with self.assertRaises(ValueError):
            bus.write(bytes(62))
        with self.assertRaises(ValueError):
            bus.read(b"\0\0", 62)
        self.assertEqual(bus.device.sent, [])


if __name__ == "__main__":
    unittest.main()
