"""Offline DA03 commit and rejection tests; not thermal validation."""
import contextlib
import io
import unittest
from unittest.mock import patch

import stwlc38_da03 as candidate
from stwlc38_da01 import config_crc, load_reference
from stwlc38_program import STWLC38
from test_stwlc38_da02 import DiagnosticBus


class SignedDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.bus = DiagnosticBus()
        self.bus.target = 0xDA03
        self.bus.memory[10:12] = (0xDA02).to_bytes(2, "little")
        self.device = STWLC38(self.bus, sleep=lambda _: None)
        self.data = candidate.load()
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_signed_threshold_and_commit(self):
        self.assertEqual(int.from_bytes(self.data[0x7a:0x7c], "little", signed=True), -5461)
        self.assertEqual(self.data[0x6c:0x74], load_reference()[0x6c:0x74])
        self.assertEqual(candidate.program(self.device, self.data, acknowledged=True)["config"], 0xDA03)
        self.assertEqual(self.bus.commit_payloads, [(126, self.data[:256]), (127, self.data[256:])])

    def test_restore_exact_reference(self):
        self.bus.memory[10:12] = (0xDA03).to_bytes(2, "little")
        self.bus.target = 0x1078
        data = load_reference()
        self.assertEqual(candidate.program(self.device, data, acknowledged=True, restore=True)["config"], 0x1078)
        self.assertEqual(self.bus.commit_payloads, [(126, data[:256]), (127, data[256:])])

    def test_reject_modified_valid_crc(self):
        data = bytearray(self.data)
        data[0x7a] ^= 1
        data[-4:] = config_crc(data[:-4]).to_bytes(4, "little")
        with self.assertRaises(ValueError):
            candidate.program(self.device, data, acknowledged=True)
        self.assertEqual(self.bus.writes, [])

    def test_reject_wrong_source_and_qi(self):
        for address, value in ((10, 0x78), (14, 2)):
            with self.subTest(address=address):
                original = self.bus.memory[address]
                self.bus.memory[address] = value
                with self.assertRaises(RuntimeError):
                    candidate.program(self.device, self.data, acknowledged=True)
                self.bus.memory[address] = original
                self.assertEqual(self.bus.writes, [])

    def test_missing_ack_and_default_cli(self):
        with self.assertRaises(RuntimeError):
            candidate.program(self.device, self.data)
        self.assertEqual(self.bus.writes, [])
        with patch.object(candidate, "CP2112") as usb:
            candidate.main([])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                candidate.main(["--program"])
            usb.assert_not_called()

    def test_partial_failure_no_reset(self):
        self.bus.bad_after_first = True
        with self.assertRaises(RuntimeError):
            candidate.program(self.device, self.data, acknowledged=True)
        self.assertEqual(self.bus.commits, [126])
        self.assertNotEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))
        self.assertFalse(self.device.allow_commit)


if __name__ == "__main__":
    unittest.main()
