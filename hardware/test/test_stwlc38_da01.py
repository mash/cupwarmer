"""Offline tests only. Fake bus does NOT prove hardware or thermal behavior."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import stwlc38_da01 as candidate
from stwlc38_program import STWLC38, parse_memh
from test_stwlc38_program import FakeBus


class ConfigBus(FakeBus):
    def __init__(self):
        super().__init__()
        self.memory[6:8] = (0x1656).to_bytes(2, "little")
        self.memory[10:12] = (0x1078).to_bytes(2, "little")
        self.commit_payloads = []
        self.bad_after_first = False
        self.bad_boot = False
        self.close_count = 0

    def close(self):
        self.close_count += 1

    def read(self, pointer, count):
        if self.bad_after_first and self.commits and pointer == b"\x01\x80":
            return bytes(count)
        return super().read(pointer, count)

    def write(self, payload):
        if payload == b"\x00\x20\x04":
            sector = self.memory[0x24]
            length = {126: 256, 127: 128}[sector]
            self.commit_payloads.append((sector, bytes(self.memory[0x180:0x180+length])))
        super().write(payload)
        if payload == bytes.fromhex("fa2001f20001") and self.commits:
            config_id = 0x1078 if self.bad_boot else 0xDA01
            self.memory[10:12] = config_id.to_bytes(2, "little")


class RestoreBus(ConfigBus):
    def __init__(self):
        super().__init__()
        self.memory[10:12] = (0xDA01).to_bytes(2, "little")

    def write(self, payload):
        super().write(payload)
        if payload == bytes.fromhex("fa2001f20001") and self.commits:
            config_id = 0xDA01 if self.bad_boot else 0x1078
            self.memory[10:12] = config_id.to_bytes(2, "little")


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.config = candidate.load_reference()
        self.bus = RestoreBus()
        self.device = STWLC38(self.bus, sleep=lambda _: None)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def run_restore(self):
        return candidate.restore_1078(self.device, self.config, acknowledge_unprotected=True)

    def test_official_two_sectors_only(self):
        self.assertEqual(candidate.ids(self.run_restore()), candidate.BEFORE_IDS)
        self.assertEqual(self.bus.commits, [126, 127])
        self.assertEqual(self.bus.commit_payloads,
                         [(126, self.config[:256]), (127, self.config[256:])])
        self.assertFalse(self.device.allow_commit)

    def test_wrong_source_rejected(self):
        self.bus.memory[10:12] = (0x1078).to_bytes(2, "little")
        with self.assertRaisesRegex(RuntimeError, "Require patch"):
            self.run_restore()
        self.assertEqual(self.bus.writes, [])

    def test_ack_required(self):
        with self.assertRaisesRegex(RuntimeError, "acknowledgement"):
            candidate.restore_1078(self.device, self.config)
        self.assertEqual(self.bus.writes, [])

    def test_unapproved_valid_crc_rejected(self):
        data = bytearray(self.config)
        data[0x143] ^= 1
        data[-4:] = candidate.config_crc(data[:-4]).to_bytes(4, "little")
        with self.assertRaisesRegex(ValueError, "pinned official"):
            candidate.restore_1078(self.device, data, acknowledge_unprotected=True)
        self.assertEqual(self.bus.writes, [])

    def test_partial_failure_no_retry_or_reset(self):
        self.bus.bad_after_first = True
        with self.assertRaisesRegex(RuntimeError, "Buffer mismatch"):
            self.run_restore()
        self.assertEqual(self.bus.commits, [126])
        self.assertNotEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))
        self.assertFalse(self.device.allow_commit)

    def test_commit_timeout_no_retry(self):
        self.bus.timeout = True
        with self.assertRaises(TimeoutError):
            self.run_restore()
        self.assertEqual(self.bus.commits, [126])
        self.assertEqual(self.bus.writes[-1], b"\x00\x20\x04")

    def test_bad_boot_not_success(self):
        self.bus.bad_boot = True
        with self.assertRaisesRegex(RuntimeError, "Post-reset"):
            self.run_restore()
        self.assertEqual(self.bus.commits, [126, 127])

    def test_cli_requires_bench_ack_before_usb(self):
        with patch.object(candidate, "CP2112") as usb:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                candidate.main(["--restore-1078", "--serial", candidate.SERIAL])
            usb.assert_not_called()


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.config = candidate.load_candidate()
        self.bus = ConfigBus()
        self.device = STWLC38(self.bus, sleep=lambda _: None)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def run_program(self):
        return candidate.program_da01(self.device, self.config, acknowledge_experimental=True)

    def test_crc_vectors(self):
        self.assertEqual(candidate.config_crc(b"123456789"), 0xFC891918)
        original = parse_memh((candidate.FIRMWARE / candidate.CONFIG_NAME).read_bytes())
        self.assertEqual(candidate.config_crc(original[:-4]), 0x4F2119CA)
        self.assertEqual(candidate.config_crc(self.config[:-4]), 0x9578196F)

    def test_only_six_words_changed(self):
        original = parse_memh((candidate.FIRMWARE / candidate.CONFIG_NAME).read_bytes())
        changed = [i//4+1 for i in range(0,384,4) if original[i:i+4] != self.config[i:i+4]]
        self.assertEqual(changed, [1, 27, 28, 29, 31, 96])

    def test_lengths_rejected(self):
        for size in (0, 128, 383, 385, 512):
            with self.assertRaisesRegex(ValueError, "384"):
                candidate.check_crc(bytes(size))

    def test_corruption_rejected(self):
        for offset in (0, 0x68, 0x7A, 0x143, 383):
            broken = bytearray(self.config)
            broken[offset] ^= 1
            with self.assertRaisesRegex(ValueError, "CRC"):
                candidate.validate_candidate(broken)

    def test_valid_crc_not_sufficient(self):
        data = bytearray(self.config)
        data[0x143] ^= 1  # An unapproved EPP voltage change.
        data[-4:] = candidate.config_crc(data[:-4]).to_bytes(4, "little")
        with self.assertRaisesRegex(ValueError, "pinned"):
            candidate.validate_candidate(data)

    def test_wrong_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "wrong.memh"
            source.write_bytes(b"00000000\n")
            with self.assertRaisesRegex(ValueError, "Reference"):
                candidate.load_candidate(source=source)

    def test_wrong_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "wrong.memh"
            source.write_bytes(b"00000000\n")
            with self.assertRaisesRegex(ValueError, "Candidate file"):
                candidate.load_candidate(candidate=source)

    def test_default_never_opens_usb(self):
        with patch.object(candidate, "CP2112") as usb:
            self.assertEqual(candidate.main([]), 0)
            usb.assert_not_called()

    def test_cli_missing_ack_or_serial_never_opens_usb(self):
        for args in (["--program"], ["--program", "--serial", candidate.SERIAL],
                     ["--inspect-device"], ["--inspect-device", "--serial", "wrong"]):
            with self.subTest(args=args), patch.object(candidate, "CP2112") as usb:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    candidate.main(args)
                usb.assert_not_called()

    def test_invalid_file_before_usb_open(self):
        with patch.object(candidate, "load_candidate", side_effect=ValueError("bad file")), \
             patch.object(candidate, "CP2112") as usb:
            with self.assertRaises(ValueError):
                candidate.main(["--inspect-device", "--serial", candidate.SERIAL])
            usb.assert_not_called()

    def test_inspection_writes_no_stwlc38_registers(self):
        with patch.object(candidate, "CP2112", return_value=self.bus):
            self.assertEqual(candidate.main(["--inspect-device", "--serial", candidate.SERIAL]), 0)
        self.assertEqual(self.bus.writes, [])
        self.assertEqual(self.bus.close_count, 1)

    def test_inspection_accepts_da01_without_retry(self):
        self.bus.memory[10:12] = (0xDA01).to_bytes(2, "little")
        with patch.object(candidate, "CP2112", return_value=self.bus):
            self.assertEqual(candidate.main(["--inspect-device", "--serial", candidate.SERIAL]), 0)
        self.assertEqual(self.bus.writes, [])

    def test_no_ack_no_writes(self):
        with self.assertRaisesRegex(RuntimeError, "acknowledgement"):
            candidate.program_da01(self.device, self.config)
        self.assertEqual(self.bus.writes, [])

    def test_bad_direct_payload_no_writes(self):
        with self.assertRaises(ValueError):
            candidate.program_da01(self.device, bytes(384), acknowledge_experimental=True)
        self.assertEqual(self.bus.writes, [])

    def test_fresh_session_required(self):
        for attr in ("allow_commit", "commits_attempted"):
            setattr(self.device, attr, 1)
            with self.assertRaisesRegex(RuntimeError, "fresh"):
                self.run_program()
            setattr(self.device, attr, 0)
        self.assertEqual(self.bus.writes, [])

    def test_wrong_source_ids_no_writes(self):
        for patch_id, config_id in ((0x1299, 0x1078), (0x1656, 0xDA01), (0x1656, 0x1026)):
            self.bus.memory[6:8] = patch_id.to_bytes(2, "little")
            self.bus.memory[10:12] = config_id.to_bytes(2, "little")
            with self.assertRaisesRegex(RuntimeError, "Require patch"):
                self.run_program()
            self.assertEqual(self.bus.writes, [])

    def test_rx_mode_rejected_before_writes(self):
        self.bus.memory[14] = 2
        with self.assertRaisesRegex(RuntimeError, "DC"):
            self.run_program()
        self.assertEqual(self.bus.writes, [])

    def test_errors_rejected_before_writes(self):
        self.bus.memory[0x2C] = 4
        with self.assertRaisesRegex(RuntimeError, "error"):
            self.run_program()
        self.assertEqual(self.bus.writes, [])

    def test_two_config_sectors_and_patch_unchanged(self):
        info = self.run_program()
        self.assertEqual(candidate.ids(info), candidate.AFTER_IDS)
        self.assertEqual(self.bus.commits, [126, 127])
        self.assertEqual(self.bus.commit_payloads, [(126,self.config[:256]), (127,self.config[256:])])
        self.assertEqual(self.device.commits_attempted, 2)
        self.assertFalse(self.device.allow_commit)
        selected = [p[2] for p in self.bus.writes if p[:2] == b"\x00\x24"]
        self.assertEqual(selected, [126, 127, 126, 127])

    def test_buffer_corruption_never_commits(self):
        self.bus.corrupt = True
        with self.assertRaisesRegex(RuntimeError, "Buffer mismatch"):
            self.run_program()
        self.assertEqual(self.bus.commits, [])
        self.assertFalse(self.device.allow_commit)
        self.assertEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))

    def test_second_stage_failure_does_not_retry_or_reset(self):
        self.bus.bad_after_first = True
        with self.assertRaisesRegex(RuntimeError, "Buffer mismatch"):
            self.run_program()
        self.assertEqual(self.bus.commits, [126])
        self.assertFalse(self.device.allow_commit)
        self.assertNotEqual(self.bus.writes[-1], bytes.fromhex("fa2001f20001"))

    def test_commit_timeout_does_not_retry_or_reset(self):
        self.bus.timeout = True
        with self.assertRaises(TimeoutError):
            self.run_program()
        self.assertEqual(self.bus.commits, [126])
        self.assertEqual(self.device.commits_attempted, 1)
        self.assertFalse(self.device.allow_commit)
        self.assertEqual(self.bus.writes[-1], b"\x00\x20\x04")

    def test_failed_post_boot_is_not_success(self):
        self.bus.bad_boot = True
        with self.assertRaisesRegex(RuntimeError, "Post-reset"):
            self.run_program()
        self.assertEqual(self.bus.commits, [126, 127])
        self.assertFalse(self.device.allow_commit)


if __name__ == "__main__":
    unittest.main()
