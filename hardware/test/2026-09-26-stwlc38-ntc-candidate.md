# STWLC38 NTC protection candidate — NOT APPROVED FOR PROGRAMMING

## Scope / status

Offline proposal based on the unchanged official config 1078 and the mirrored
WPSTUDIO 2.1.0 WLC38 definition. A CRC-consistent **unvalidated bench candidate**
has now been produced under `candidates/`; no board access or firmware write
occurred. The guarded programmer still rejects it. This is an overtemperature
protection proposal, not a thermostat or validated product configuration.

Provenance and interpretation limits:
[offline inspection](2026-09-26-wpstudio-offline-inspection.md).
The reference file SHA-256 is
`ba9a1cc8e4915c3ebfc65410ee237bb87c2e6e70d27004d94d04a38176d1e542`.

## Proposed ADC protection settings

| GUI field | Reference 1078 | Candidate |
|---|---|---|
| RX ADC NTC EN PROT | Disabled | Enabled |
| RX ADC NTC EPT | Disabled | Enabled |
| RX ADC NTC VOUT OFF | Disabled | Enabled |
| RX THRES NTC | 0 mV | 600.0 mV, pending calibration |

DS14078 RX protection tables publicly document bit 2 for these three ADC NTC
actions. UM3154 Rev 2 §5.9.6 describes a low NTC voltage threshold, with optional
EPT and output-off actions. The Config **file offsets and 0.1 mV/LSB encoding**
come from the mirrored definition, not the public datasheet. Exact compatibility
with patch 1656/cut 1.2 must still be verified before committing a modified NVM.

Do not change the separate bit-4 NTC TSHUT fields or `ntc_ref_sel`: although
internal names exist in the mirrored definition, the public protection tables
mark bit 4 reserved. Do not substitute their internal 300 mV label for the
datasheet's external comparator threshold or treat those paths as equivalent.

## Nominal temperature calculation

Existing design target: about 69°C at the heater NTC, not the cup or accessible
surface. Assumptions: R25 = 100 kΩ, B25/85 ≈ 4260 K, pull-up = 51 kΩ,
VAA = 2.5 V, no input bias, ideal thermal contact.

`R(T) = 100000 × exp(4260 × (1/(T+273.15) − 1/298.15))`

`VNTC = 2.5 × R(T) / (51000 + R(T))`

| NTC temperature | Nominal resistance | Nominal VNTC |
|---|---:|---:|
| 25°C | 100.00 kΩ | 1655.6 mV |
| 60°C | 22.29 kΩ | 760.3 mV |
| 65°C | 18.45 kΩ | 664.1 mV |
| 69°C | 15.92 kΩ | 594.8 mV |
| 70°C | 15.36 kΩ | 578.5 mV |

600 mV corresponds to 16.105 kΩ and approximately **68.69°C** in this model;
590 mV corresponds to about 69.29°C. These are nominal estimates, not guaranteed
trip temperatures. B25/85 is a reference constant, not an exact curve across all
temperatures. The received heater's actual NTC identity, bias current, VAA,
resistor/ADC tolerances, and thermal contact/lag must be measured. In particular,
the earlier handled-at-room-temperature 90 kΩ reading is not a calibrated curve.

Murata lists the specified NCP18WF104F12RB as 100 kΩ and B25/85 4260 K (reference):
[manufacturer product page](https://www.murata.com/products/productdetail?partno=NCP18WF104F12RB).
The order specified this part; the received assembly's exact MPN is not yet
independently established. An open low-side NTC drives the divider high, so this
low-threshold mechanism alone does **not** provide open-sensor protection.

## Initial parameter-only delta (incomplete without CRC)

These are **file offsets / one-based MEMH lines, NOT I2C addresses or commands**.

| MEMH line | File offset | Original word | Proposed word |
|---:|---|---|---|
| 27 | 0x68 | 0003A401 | 0003A405 |
| 28 | 0x6c | 00030401 | 00030405 |
| 29 | 0x70 | 00030401 | 00030405 |
| 31 | 0x78 | 00000002 | 17700002 |

The last word retains bytes 0x78–0x79 and sets 0x7a–0x7b to little-endian
6000 (`0x1770`), using the definition's 0.1 mV/LSB scale. Do not type 600 as the
raw code: that would mean 60 mV under this interpretation.

In-memory checks passed: source hash, 384-byte size, exactly five changed bytes
(0x68, 0x6c, 0x70, 0x7a, 0x7b), unchanged bit-4 paths/hardware threshold settings,
unchanged FOD/EPP region and configuration ID. Keeping the ID unchanged here is
only a comparison convenience: ID 1078 alone could not distinguish a modified
candidate from the vendor original. The initial four-word delta above is NOT a
complete image: changing those fields invalidates the trailing CRC. The format
audit and complete experimental delta below supersede that initial proposal.
Do not relax the programmer's pinned-input checks to accept this proposal.

## Save-format audit and experimental DA01 candidate

Static inspection of the same mirrored executable (not execution on the host)
found the following:

- `SaveRxToMemh` (`0x0600071a`) copies Config RawData, updates `cfg_id` and
  CFG-related values from the I2C model, recalculates CRC, then serializes MEMH.
- The Save click handler starts the custom ID at decimal 55808 (`0xDA00`),
  ORs it with the user-entered byte, and passes the result to the saver.
  `ConfigIdDialog.GetByteId` parses a byte, not an arbitrary 16-bit number.
  This establishes the GUI's `DAxx` convention, not a claim that the chip
  rejects all other IDs. Local experimental revision 01 is therefore `DA01`.
- `DeviceTypeEnum.WLC38` is 3. In `ReCalculateCRC` (`0x06000720`), its branch
  covers all bytes except the final four (no eight-byte skip).
- `WlcCRC.CalculateUintCRC` in the embedded `STM.CoreLib2.IOFiles` assembly
  processes little-endian word bytes in file-byte order: polynomial
  `0x04C11DB7`, initial `0xFFFFFFFF`, non-reflected/MSB-first shifts, final XOR
  `0xFFFFFFFF`. The result is stored little-endian in the last four bytes.
- Independent bitwise and embedded-table calculations both reproduced the
  original 380-byte payload CRC **`4F2119CA`**. Skipping eight bytes instead
  produced `D2B8E108`, which does not match. Parameter-only edits retain a stale
  CRC and fail validation.
- The click handler also checks dirty RX registers. Its warning states that
  changes not written to RAM will not be included in the saved file. A checkbox
  change alone is therefore not proof that Save would capture the edit.
  This supports UM3154 §4.3's Read / edit / Write-to-temp-memory / Save sequence.
  No Write command was invoked to investigate this.

Experimental artifact:
[DA01 NTC600mV UNVALIDATED](candidates/STWLC38JRM_Config_DA01_cut1.2_EPP12V_NTC600mV_UNVALIDATED.memh).
It is generated from official 1078, not from uninitialized GUI defaults.

| One-based MEMH line | Original | Experimental DA01 |
|---:|---|---|
| 1 | `00001078` | `0000DA01` |
| 27 | `0003A401` | `0003A405` |
| 28 | `00030401` | `00030405` |
| 29 | `00030401` | `00030405` |
| 31 | `00000002` | `17700002` |
| 96 | `4F2119CA` | `9578196F` |

Size: 384 decoded bytes / 96 words. LF-file SHA-256:
`09a3a6e379bb09d29a3a27a5cb3b1644465bd9dcac1bc91a1809b3291ed8b03c`.
Ten bytes differ: ID bytes 0–1, parameter bytes `68/6c/70/7a/7b`, and CRC bytes
`17c/17e/17f` (hex offsets); CRC byte `17d` happens to be unchanged.
All other bytes, including FOD/EPP values, remain exactly as in 1078.
The saved artifact was re-read and matched the generated bytes exactly. The
bitwise CRC also passed the `123456789` check vector (`FC891918`); all 3072
single-bit corruptions of the 384-byte artifact were detected by the separate
embedded-table calculation. Existing programmer tests remain 24/24 passing.
These are file-integrity tests, not hardware/protection-function tests.

This resolves file CRC and GUI ID-format questions, **not** physical acceptance,
exact patch/map compatibility, temperature calibration, or safe recovery. The
existing programmer remains pinned to 1078 and would either reject this file
by hash or skip programming when its fixed target IDs are already present.
It must not be repurposed by simply renaming this candidate. The separate
experimental workflow below has been added; bench approval and post-boot
verification remain required.

## Separate DA01 bench workflow (not executed on hardware)

`stwlc38_da01.py` leaves the original official-image programmer and its hash
allowlist unchanged. Default invocation is offline and never opens HID:

```sh
python3 hardware/test/stwlc38_da01.py
python3 -m unittest discover -s hardware/test -p 'test_stwlc38*.py' -v
```

The new workflow validates both source and candidate hashes, exact parameter
delta, 384-byte size, and CRC before opening hardware. Even a modified payload
with a valid new CRC is rejected. It exposes these explicitly selected modes:

- `--inspect-device --serial 00E1E3D6`: read-only STWLC38 identity/error/mode
  inspection; CP2112 volatile bus configuration is restored on close. Accepts
  only patch 1656 with config 1078 or DA01. Does not reset or program STWLC38.
- `--program`: requires the exact serial plus
  `--dc-5v-heater-disconnected` and `--acknowledge-experimental-da01`. These
  flags are human attestations, not electrical measurements. Do not execute
  based on a stale wiring confirmation. Requires chip 0x26/revision 3/ROM 0x161/
  cut 3, DC mode, no system error, and source patch 1656/config 1078.
- First tests both 256-byte and 128-byte buffers with commits disabled,
  restores/reset-checks the original state, then repeats source checks.
- Programs only sector 126 (256 bytes) and 127 (128 bytes), with per-buffer
  byte comparisons and bounded commit polling. Never rewrites patch sectors.
  The embedded WPSTUDIO POLARISFlash config-only branch corroborates this size
  and sector split; see the offline inspection record.
- On a partial NVM failure, does not retry or reset automatically. DA01 already
  present is rejected by program mode; use inspect mode, not a repeated write.
- After reset, requires 1656/DA01, DC mode and zero system errors. This verifies
  boot IDs/error status, not a full NVM dump, cold power cycle or NTC behavior.

Verification: 23 new offline tests plus 24 unchanged programmer tests pass.
Cases include wrong IDs/mode/errors, malformed/unapproved payloads, both-sector
buffer checks, exact two-sector commit payloads, partial failure, commit timeout,
no retries, post-boot mismatch, and default/inspect no STWLC38 writes.
No DA01 hardware inspection, reset, buffer test or programming has been run.
The user has been asked for the current physical bench state before proceeding.

## Recovery: what is and is not established

- UM3154 §5.15 says interrupt **status** clears when its triggering condition
  disappears; interrupt **latch** remains until explicitly cleared.
- That does not establish whether VOUT restarts automatically after NTC EPT or
  VOUT-off, nor whether the transmitter will repeatedly ping/restart while hot.
- The datasheet's 50/125/150 mV external-comparator hysteresis is not established
  as the ADC firmware threshold's recovery hysteresis. Do not calculate a
  guaranteed recovery temperature from it.
- The internal `vout_err_latch_en` field is 0 in the reference, but its scope is
  undocumented here. Do not change it or infer recovery behavior from its name.
- Neither clearing an interrupt nor sending VOUT ON/EPT-restart is an approved
  recovery procedure for an overheated assembly.

## Validation sequence / gates

1. Keep heater H+ disconnected and insulated. Confirm exact config-map/firmware
   compatibility and ADC voltage scaling against a meter before any NVM change.
2. Measure the NTC resistance at known stable temperatures with independent
   contact temperature measurement. Resistance mode requires an unpowered,
   electrically isolated sensor measurement; do not use an ohmmeter on a powered
   divider. Do not assume an IR reading equals the embedded NTC temperature.
3. After a separately approved programming procedure and verified cold boot,
   test the low-voltage threshold **without powering the heater**. Use controlled
   sensor warming or a reviewed passive resistance substitution with all wiring
   changes unpowered. Do not inject an external voltage into NTC/VAA.
4. Observe DMM VNTC/VOUT, available I2C telemetry, overtemperature status/latch,
   transmitter behavior, and time to output removal as voltage crosses the
   threshold downward. DMM output-off alone does not prove an EPT was sent.
5. While still above the temperature limit, observe repeated transmitter pings
   and power reapplication. Record any output pulses/restarts. Then let the
   sensor cool and record whether/when power returns; do not clear or force ON
   during this observation. A short observation without restart is not proof of
   a permanent latch.
6. Resolve unsafe cycling, missing protection, or sensor faults before powered
   heater tests. Only proceed after FOD/stack validation and independent F1
   operation are also checked. No unattended or empty-cup heater test.

Public ST sources used from locally preserved text: DS14078 protection sections
and RX protection tables; UM3154 Rev 2 §§5.9.6, 5.15, 9.1.7. On 2026-09-26 the
live ST datasheet fetch failed and the old Community PDF URL redirected to the
community home page; those fetches did not verify a newer document revision.

## VM experiment

The scheduled heartbeat later observed the working VM stopped, changed its
memory once from 8 to 12 GiB, and restarted it with all isolation unchanged.
See the offline-inspection record for the retry outcome. More RAM does not
validate this configuration or establish why Load for RX is disabled while
disconnected.
