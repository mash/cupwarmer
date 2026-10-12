# STWLC38 DA01 config programming — 2026-10-04

The user requested programming the prototype and replied `ready` to the stated
bench conditions: insulated/disconnected heater H+, Qi removed, external USB
5 V supply, and CP2112 connected to the Mac. These are user attestations;
the supply voltage and physical wiring were not independently measured today.

Adapter: CP2112 serial `00E1E3D6`. Tool: `stwlc38_da01.py`, with hidapi via uv.
The initial sandboxed USB open failed; execution with USB access succeeded.

Read-only preflight confirmed chip 38, revision 3, ROM 353, cut 3, DC mode 1,
patch `0x1656`, config `0x1078`, and zero errors.

The pinned 384-byte DA01 candidate passed its hash, exact-delta and CRC checks:
SHA-256 `09a3a6e379bb09d29a3a27a5cb3b1644465bd9dcac1bc91a1809b3291ed8b03c`.
The programming command completed successfully, including both volatile-buffer
checks and restoration of the source boot state before NVM programming.

Only config sector 126 (256 bytes) and sector 127 (128 bytes) were committed.
Patch sectors were not rewritten. After software reset, boot IDs were
`0x1656` / `0xDA01`, DC mode 1, errors 0. A separate read-only invocation then
confirmed the same IDs and zero errors.

DA01 enables ADC NTC protection, EPT and VOUT-off with a nominal 600 mV
threshold. Its approximately 69°C interpretation remains an uncalibrated
estimate. This operation confirms programming/boot status, not thermal
protection, recovery behavior, full NVM byte readback, or cold power-cycle
persistence. The heater was not instructed to be reconnected.

Next: disconnect both USB supplies, wait, restore external 5 V then CP2112,
with Qi removed and heater H+ still isolated, and read IDs/errors again.
Candidate provenance and remaining thermal limitations are recorded in
`2026-09-26-stwlc38-ntc-candidate.md`.

## Cold power-cycle verification

The user replied `戻した` after the above power-cycle instructions. A fresh
read-only inspection confirmed patch `0x1656`, config `0xDA01`, DC mode 1,
and errors 0 (chip 38, revision 3, ROM 353, cut 3). DA01 therefore persisted
after the user-reported cold power cycle. No additional NVM write or reset
was issued. Thermal behavior remains untested.

## Qi symptom and approved reference comparison

With DA01, the user reported blinking D2 and VOUT 0 V. Qi-only I2C reads
failed. Reported voltages while on Qi: PCA9306 VREF1 1.0–1.7 V, NTC
approximately 0.6–1.0 V, VAA approximately 0.9–1.6 V. NTC was 1.57 V with
external 5 V. These DMM ranges do not establish instantaneous minimums,
timing or whether protection causes or follows the supply cycling.
Removing the J1 jumper connections did not resolve VAA fluctuation.

Measurement-point correction: the current assembled-PCB file maps TP1 to
I_HEATER_MON, not RX_NTC. The user clarified the 1.57 V measurement was at
NTC. TP1 zero volts must not be interpreted as a zero NTC voltage. J1.1
maps to RX_VAA in that PCB file.

The user explicitly approved restoring official 1078 for comparison, then
confirmed `connected` after instructions to remove Qi, restore J1/CP2112
and external 5 V, keeping heater H+ disconnected. Fresh preflight confirmed
1656/DA01, DC mode 1, errors 0.

Added a pinned `--restore-1078` mode to the existing DA01 tool, with explicit
unprotected-comparison acknowledgement. It accepts only official 1078 and
the starting 1656/DA01 pair. 55 offline tests passed, including two-sector
payloads, rejected inputs and partial-failure/no-retry behavior.
The restore command committed only config sectors 126 (256 bytes) and 127
(128 bytes), then verified 1656/1078, DC mode 1, errors 0 after software reset.
Patch sectors were not rewritten. Current configuration is now **1078**;
DA01 temperature protection is no longer active.

After removing both USB connections and the J1 jumpers and placing the coil
on Qi again, the user reported **VOUT 5 V**. This supports a configuration-
dependent startup failure with DA01; it does not isolate which changed field
causes it. Heater H+ remains disconnected. No further NVM write was performed.

## Follow-up diagnosis

The preserved ST UM3154 Rev 2 section 9.1.7 describes the NTC measurement
as a signed, two-byte accumulated ADC value, with default accumulation 16
and a voltage conversion. This is distinct from the mirrored definition's
`u*0.1` interpretation used for the configuration threshold. The relationship
between those two encodings and patch 1656 has not yet been established.
Do not infer a replacement threshold merely by applying the measurement
conversion to the configuration field.

Requested the NTC-to-GND DC voltage while official 1078 is receiving Qi with
VOUT 5 V. Next useful comparison is that meter value versus the NTC monitor
register in actual RX mode, once the read-only I2C connection is restored.
Earlier external-5-V/DC-mode telemetry is not a substitute for this check.

The user reported **NTC 1.57 V** in this stable 1078/Qi state. This is above
the intended 0.600 V threshold; a room-temperature trip cannot be explained
by that steady measured voltage alone. Threshold encoding/map compatibility
and startup-time behavior remain unresolved.

After restoring the read-only I2C connection, the first read returned DC mode
1. The user then said the coil was placed on Qi. Three consecutive reads now
confirmed **Qi RX mode 2**, patch 1656/config 1078, and errors 0.
Monitor bytes at 0x0092 (12 bytes per sample):

```
8c127e12250068016f00eefc
b5129812250067016f00f0fc
b7129d12250068016f00ecfc
```

NTC signed raw values are -786, -784, -788. Applying the UM3154 measurement
formula with its default accumulation value 16 gives about 1.627 V. The
accumulation setting itself was not read back. This is in the vicinity of,
but not identical to, the user's 1.57 V meter reading. VOUT telemetry is
4734–4765 mV during these reads. These measurements establish actual RX-mode
telemetry; they do not establish the encoding of the NTC protection threshold.
No STWLC38 reset, configuration change or NVM write was issued.

## Definition mismatch and next diagnostic candidate

Re-examined the original 2026-09-26 static-inspection tool output from this
chat. The mirrored definition maps `rx_ntc` to I2C 0x009c and labels its
conversion `u*0.01`, unit mV. Applying that unsigned conversion to the live
0xfcee gives 647.50 mV, unlike the meter's 1570 mV or the signed ADC
conversion's approximately 1627 mV. The threshold field separately specifies
`u*0.1`. This undermines assuming that all GUI scaling applies to patch 1656;
it does not prove the correct threshold encoding or which action caused DA01
startup failure. The old extracted executable/definition files are no longer
present in their temporary directory. A simple static Thumb search in the
official patch did not identify the threshold comparison routine.

Prepared, but DID NOT PROGRAM, a diagnostic-only DA02 image:
`candidates/STWLC38JRM_Config_DA02_NTC_DIAGNOSTIC_NO_SHUTDOWN.memh`.
It retains DA01's raw threshold 6000 and ADC NTC comparison enable, but leaves
NTC EPT and VOUT-off disabled as in official 1078. All other parameters match
1078. Its purpose is to observe the protection status while receiving Qi,
without the two newly enabled stop actions preventing telemetry. This is not
a corrected temperature-protection configuration and must not power the heater.

Decoded size 384 bytes; CRC 0x265de35b; LF SHA-256
`d7b844bdfd183b52f59cb2c5b2ed7e513eaf2991b378bed67fa0e0f83a2106b3`.
Added the separate `stwlc38_da02.py` workflow with pinned hash/exact-delta
validation, a 1656/1078 source guard, 1656/DA02 target verification, and an
explicit DA02-to-1078 restore mode. It reuses the tested config-only write
sequence; the DA01 and original official-image tools remain unchanged.
Default execution validates offline without opening USB. All 64 offline tests
pass, including nine DA02 tests for payloads, restoration, invalid changes,
missing acknowledgements, Qi-mode rejection and partial-failure handling.

After a fresh physical change to external 5 V with Qi removed and heater H+
disconnected, the prepared command is:

```
uv --cache-dir /private/tmp/cupwarmer-static-uv run --no-project --with hidapi python hardware/test/stwlc38_da02.py --program --serial 00E1E3D6 --dc-5v-heater-disconnected --acknowledge-no-ntc-shutdown
```

For restoration from DA02, replace `--program` with `--restore-1078`, retaining
the same physical conditions and flags. Neither command was run on hardware.
The present Qi-powered state must be changed before any NVM write.

## DA02 programming result

The user replied `done` to switching from Qi to external 5 V, with CP2112
connected and heater H+ disconnected. A fresh read-only preflight confirmed
1656/1078, DC mode 1, errors 0. The prepared DA02 command then completed the
volatile-buffer checks and committed only sectors 126 (256 bytes) and 127
(128 bytes). Software-reset verification returned patch 1656/config DA02,
DC mode 1, errors 0. Patch sectors were not rewritten.

Current chip configuration is **DA02**, diagnostic-only, with NTC EPT and
NTC VOUT-off disabled. Cold power-cycle and Qi protection-status observations
are pending. The heater must remain disconnected for this diagnostic.

## DA02 Qi observation after user-reported power cycle

The user confirmed disconnecting both USB supplies, waiting, restoring only
CP2112 USB and placing the coil on Qi. Three reads returned patch 1656/config
DA02, Qi RX mode 2 and system errors 0. Monitor samples at 0x0092:

```
b214751324006d016f0003fd
b414771324006e016f0002fd
b214751324006d016f0001fd
```

VOUT is 4981/4983/4981 mV; NTC raw is 0xfd03/0xfd02/0xfd01 (signed
-765/-766/-767). RX status at 0x008c is 0x00000041 in all three samples:
OVTP status bit 0 and output-on bit 6 are set. A separate read of the actual
RX interrupt latch at 0x0088 returned `410c0000`, also with OVTP set.
An earlier log mistakenly named a read of 0x0084 `da02_rx_latch`; 0x0084 is
the interrupt-clear register, not the latch. It was only read, never written.

Thus DA02 sustains Qi output while reporting overtemperature. Together with
DA01's shutdown and the unchanged reference protection fields, this strongly
implicates the enabled NTC comparison/actions. The shared OVTP bit alone does
not uniquely identify the sensor source, and the correct threshold encoding
is still unproven. No interrupt clear, configuration write or reset was issued.

## Patch1656 signed-threshold evidence and DA03 preparation

Static Thumb disassembly of the pinned official patch (SHA-256
`5495b35e175f6fa1c1768e71306692035688e69677a72f423723a2ce27b2efef`)
identified the function at decoded-file offset 0x1bbe. Its pointer 0x00081bbf
is present at file offset 0x5728. Offsets here are file offsets, NOT I2C
addresses. Capstone parsed the bytes on the host; no firmware was executed.

Relevant instructions:

```
1bc2 movs r2, #0x68
1bc6 ldr  r1, [r4, #8]
1bc8 ldrb r2, [r2, r1]
1bca lsls r2, r2, #0x1d   ; test bit 2, comparison enable
1bcc bpl  0x1c2e
1bce adds r1, #0x62
1bd0 ldrb r2, [r1, #0x19] ; byte 0x7b
1bd2 ldrb r3, [r1, #0x18] ; byte 0x7a
1bd4 lsls r1, r2, #0x18
1bd8 asrs r1, r1, #0x10   ; sign-extend high byte
1bde orrs r1, r3          ; signed little-endian 16-bit threshold
...
1bea cmp  r0, r1
1bec bge  0x1c14          ; non-trigger branch for sample >= threshold
```

The trigger path then tests config 0x6c bit 2 (EPT) and 0x70 bit 2
(VOUT-off), independently corroborating that this is the NTC protection
routine and matching our three changed enable bits. The code also applies
`(threshold * 9) >> 3` under an internal state bit before comparison; full
recovery behavior remains unvalidated. Input r0 comes through a function
table/caller not traced here, so its exact measurement scaling is still an
inference, not a complete call-path proof.

This establishes SIGNED threshold storage, unlike the previous GUI-derived
unsigned voltage assumption. With the UM3154 default-accumulation ADC formula,
600 mV corresponds to round((0.6 - 1.8) * 1024 * 16 / 3.6) = -5461,
encoded 0xeaab. Positive 6000 would correspond to 3.118 V under that same
formula, which explains the observed room-temperature trip if r0 is raw ADC.
The old `6000 = 600 mV` interpretation is not usable for this firmware.

Prepared DA03, still with NTC shutdown actions disabled, changing only the
threshold to -5461 relative to DA02 (plus ID/CRC). It is a diagnostic candidate,
not thermally validated. File:
`candidates/STWLC38JRM_Config_DA03_NTC_SIGNED_DIAGNOSTIC.memh`;
SHA-256 `ca1cd14c72a27c32aa287a66a9fc495ab13b7ba4a866e9edf27712be4b0a2473`.
`stwlc38_da03.py` validates the exact payload against official 1078, requires
source 1656/DA02 in DC mode, writes only the two config sectors, and supports
explicit DA03-to-1078 restoration. Default execution is offline. All 70 tests
pass; no DA03 hardware access or write has occurred.

Next: with fresh external-5V/no-Qi/heater-disconnected confirmation, use
`stwlc38_da03.py --program --serial 00E1E3D6 --dc-5v-heater-disconnected
--acknowledge-no-ntc-shutdown` through the existing uv/hidapi invocation.
Check room-temperature OVTP clears under Qi, then validate threshold crossing
before enabling shutdown actions or connecting heater power.

## DA03 programming result

The user replied `done` to returning to external 5 V with Qi removed,
CP2112 connected and heater H+ disconnected. The DA03 command confirmed
1656/DA02, DC mode 1, errors 0, completed both volatile-buffer checks, and
committed config sectors 126 (256 bytes) and 127 (128 bytes) only.
Software-reset verification confirmed **1656/DA03, DC mode 1, errors 0**.
Patch sectors were not rewritten. Current configuration is diagnostic DA03;
NTC shutdown remains disabled. Cold power-cycle/Qi OVTP observation and
threshold-crossing validation remain pending.

## DA03 Qi readback

The first read after the user reported `connected` timed out (SMBus status 3,
detail 0). On the user's explicit retry, three consecutive samples succeeded:
1656/DA03, Qi RX mode 2, system errors 0. Monitor data at 0x0092:

```
e71477132400770185000bfd
e71476132400760185000afd
e71475132400770185000afd
```

VOUT is 4983/4982/4981 mV; NTC raw is -757/-758/-758.
All three RX status reads at 0x008c returned `40000000` (output-on, OVTP clear).
Latch reads at 0x0088 returned `400c0000` (OVTP also clear).
Thus changing the diagnostic threshold from +6000 to -5461 removes the
room-temperature OVTP indication while retaining Qi output. This supports
the signed-ADC interpretation, but does not yet establish the actual voltage
or temperature at which protection triggers, nor shutdown/recovery behavior.
No configuration write, interrupt clear or reset was performed during reads.

## User accepts prototype fix; thermal test deferred

The user chose to accept the fix after being told that the actual thermal
trip point is unverified. This does not turn the diagnostic DA03 into a
shutdown-enabled configuration. Prepared DA04 with signed threshold -5461
and all three ADC NTC comparison/EPT/VOUT-off bits enabled. Other parameters
remain official 1078 values. DA04 is a prototype configuration, not a
validated temperature-protection implementation.

Image: `candidates/STWLC38JRM_Config_DA04_NTC_SIGNED_PROTOTYPE.memh`.
Tool: `stwlc38_da04.py`, default offline, exact payload/CRC validation,
1656/DA03 source guard, 1656/DA04 post-reset verification, config-only writes,
and explicit DA04-to-1078 restoration. All 76 offline tests pass.
The programming flag is `--acknowledge-unvalidated-prototype`, alongside
`--program --serial 00E1E3D6 --dc-5v-heater-disconnected`.

DA04 HAS NOT BEEN WRITTEN. The last confirmed physical state was Qi-powered,
so a fresh switch to external 5 V with Qi removed is required before writing.
Current chip remains DA03 with NTC shutdown disabled. Actual trip threshold,
shutdown and recovery behavior remain untested; no heater reconnection was
authorized or instructed as part of accepting this prototype fix.

## DA04 programming completed

The user confirmed `done` after instructions to remove Qi and restore external
5 V, keeping CP2112 connected and heater H+ disconnected. The DA04 programmer
confirmed 1656/DA03, DC mode 1, errors 0 before writing. Both volatile-buffer
checks passed, and only config sectors 126 (256 bytes) and 127 (128 bytes)
were committed. After software reset: **1656/DA04, DC mode 1, errors 0**.
The patch was not rewritten. Current chip configuration is now DA04, with
ADC NTC comparison, EPT and VOUT-off configured and signed threshold -5461.
Cold-power-cycle persistence and room-temperature Qi startup with DA04 remain
pending. Thermal trip temperature, actual shutdown and recovery are untested.

## DA04 cold-power-cycle Qi confirmation

After the user confirmed the requested power cycle and Qi placement, all six
read-only samples reported 1656/DA04, Qi RX mode 2, errors 0, RX status
`40000000` (output on, OVTP clear). The first three latch reads were
`400c0000`, also with OVTP clear. DA04 persistence and room-temperature Qi
startup are therefore confirmed after the user-reported power cycle.

First three monitor blocks:
`95177613240080019100e4fc`, `5f115511240070016f00e7fc`,
`8a11781124006f016f00e5fc`.
VOUT was 4982, 4437, 4472 mV. A follow-up sampled 4454, 4549, 4625 mV,
with VRECT 4487, 4576, 4660 mV and NTC raw -793, -806, -795.
Thus output is on, but a stable 5 V output is NOT established in this run.
The source of voltage variation is not isolated. The user-accepted NTC
startup fix is installed; thermal trip/recovery remain unverified and heater
H+ remains disconnected. No further writes or interrupt clears were issued.
