# STWLC38 NVM programming — 2026-09-23

Bench session: approximately 18:20 EEST. No Qi power; heater H+ disconnected
and insulated. External USB 5 V supplied to VOUT. All grounds made common.
User confirmed approximately 5 V VOUT, 2.5 V VREF1 and 3.3 V VREF2.
CP2112 VID/PID `10C4:EA90`, serial `00E1E3D6`; STWLC38 address `0x61`.

## Before

Read-only bytes at `0x0000..0x000E`:

```text
26 00 03 00 61 01 99 12 00 00 26 10 07 00 01
```

- Chip ID `0x0026`, revision `0x03`, hardware cut ID `3`, ROM `0x0161`.
- NVM patch `0x1299`, configuration `0x1026`.
- Operation mode `0x01` (standalone/DC), system error register `0x00000000`.

## Validation and write

- Custom adapter: `stwlc38_program.py`, based on the documented ST reference
  sequence and CP2112 AN495. Provenance/limitations: `stwlc38-programming.md`.
- 24 offline tests passed before touching the programming buffer.
- MEMH little-endian conversion independently matched **all** bytes of the
  preserved WPSTUDIO-generated example arrays: 384 config bytes / 12604 patch bytes.
- Input file SHA-256 hashes matched the pinned ST package:
  - Patch: `5495b35e175f6fa1c1768e71306692035688e69677a72f423723a2ce27b2efef`.
  - LF-normalized config: `ba9a1cc8e4915c3ebfc65410ee237bb87c2e6e70d27004d94d04a38176d1e542`.
- A volatile-only 256-byte buffer test passed on the actual chip, with NVM
  commit blocked. IDs and error status were unchanged after reset.
- The programming command repeated that buffer test successfully before writing.
- Patch 1656: 27680 bytes, sectors **0–108** (109 sectors).
- Config 1078 (cut 1.2 EPP 12 V reference): 384 bytes, sectors **126–127**.
- Every buffer was written in 32-byte I2C chunks and read back byte-for-byte
  before its NVM commit. All **111** sector operations reported completion.
- No automatic retry was needed or performed. Hardware reset and ID/error
  verification completed successfully. No other NVM sectors were selected.

## Independent post-reset readback

The separate, existing `cp2112_probe.py` confirmed:

```text
0x61: ACK register=0x0000 (bytes=15, data=26 00 03 00 61 01 56 16 00 00 78 10 07 00 01)
0x61: ACK register=0x002C (bytes=4, data=00 00 00 00)
```

- NVM patch ID **`0x1656`**.
- Configuration ID **`0x1078`**.
- System/NVM error bytes all zero.
- Still in standalone/DC mode.

This first check confirmed successful boot after a software reset, not a full
NVM byte-for-byte dump. The byte comparisons above verify the programming buffer
before each commit. No full backup of the old NVM was made.

## Cold power-cycle verification

The user confirmed disconnecting both USB sources, waiting, and reconnecting
the external supply followed by CP2112, with Qi and heater H+ still disconnected.
The default read-only mode of `stwlc38_program.py` then reported:

```json
{"chip":38,"config":4216,"cut":3,"errors":0,"mode":1,"patch":5718,"revision":3,"rom":353}
```

Patch `0x1656` and configuration `0x1078` persisted after the reported cold power
cycle. System/NVM errors remained zero and the device stayed in DC mode. No
additional NVM writes were issued for this check.

## Pending bench steps

1. Verify NTC/protection actions, Qi negotiation and coil/stack-specific FOD
   behavior before connecting the heater. The ST reference configuration is
   not a validated production cupwarmer configuration.
