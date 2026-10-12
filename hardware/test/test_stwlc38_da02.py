"""DA02 offline guards and config-only commits; no hardware access."""
import contextlib
import io
import unittest
from unittest.mock import patch

import stwlc38_da02 as diagnostic
from stwlc38_da01 import config_crc, load_reference
from stwlc38_program import STWLC38
from test_stwlc38_da01 import ConfigBus


class DiagnosticBus(ConfigBus):
    target = 0xDA02

    def write(self, payload):
        super().write(payload)
        if payload == bytes.fromhex("fa2001f20001") and self.commits and not self.bad_boot:
            self.memory[10:12] = self.target.to_bytes(2, "little")


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.bus = DiagnosticBus()
        self.device = STWLC38(self.bus, sleep=lambda _: None)
        self.data = diagnostic.load_diagnostic()
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_default_no_usb(self):
        with patch.object(diagnostic, "CP2112") as usb:
            self.assertEqual(diagnostic.main([]), 0)
            usb.assert_not_called()

    def test_cli_guard_before_usb(self):
        with patch.object(diagnostic, "CP2112") as usb, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                diagnostic.main(["--program"])
            usb.assert_not_called()

    def test_missing_ack_no_writes(self):
        with self.assertRaises(RuntimeError):
            diagnostic.program(self.device, self.data)
        self.assertEqual(self.bus.writes, [])

    def test_payload_and_restoration(self):
        result = diagnostic.program(self.device, self.data, acknowledged=True)
        self.assertEqual(result["config"], 0xDA02)
        self.assertEqual(self.bus.commit_payloads, [(126, self.data[:256]), (127, self.data[256:])])
        self.bus = DiagnosticBus()
        self.bus.memory[10:12] = (0xDA02).to_bytes(2, "little")
        self.bus.target = 0x1078
        self.device = STWLC38(self.bus, sleep=lambda _: None)
        data = load_reference()
        result = diagnostic.program(self.device, data, acknowledged=True, restore=True)
        self.assertEqual(result["config"], 0x1078)
        self.assertEqual(self.bus.commit_payloads, [(126, data[:256]), (127, data[256:])])

    def test_reject_extra_change_with_valid_crc(self):
        data = bytearray(self.data)
        data[0x6c] |= 4
        data[-4:] = config_crc(data[:-4]).to_bytes(4, "little")
        with self.assertRaises(ValueError):
            diagnostic.program(self.device, data, acknowledged=True)
        self.assertEqual(self.bus.writes, [])

    def test_qi_mode_rejected_without_writes(self):
        self.bus.memory[14] = 2
        with self.assertRaises(RuntimeError):
            diagnostic.program(self.device, self.data, acknowledged=True)
        self.assertEqual(self.bus.writes, [])

    def test_wrong_source_rejected(self):
        self.bus.memory[10:12] = (0xDA01).to_bytes(2, "little")
        with self.assertRaises(RuntimeError):
            diagnostic.program(self.device, self.data, acknowledged=True)
        self.assertEqual(self.bus.writes, [])

    def test_partial_failure_no_reset_or_retry(self):
        self.bus.bad_after_first = True
        with self.assertRaises(RuntimeError):
            diagnostic.program(self.device, self.data, acknowledged=True)
        self.assertEqual(self.bus.commits, [126])
        self.assertNotEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))
        self.assertFalse(self.device.allow_commit)

    def test_bad_boot_rejected(self):
        self.bus.bad_boot = True
        with self.assertRaises(RuntimeError):
            diagnostic.program(self.device, self.data, acknowledged=True)
        self.assertFalse(self.device.allow_commit)


if __name__ == "__main__":
    unittest.main()
