# STWLC38JRM firmware/configuration staging

## Selected files for the v1 receiver

The installed receiver reported chip revision `0x03`, which corresponds to
STWLC38JRM cut 1.2. The safe starting pair is therefore:

- patch: `STWLC38JRM_Patch_1656_rtx.memh`
- configuration: `STWLC38JRM_Config_1078_cut1.2_EPP12V.memh`

ST supplied both files in the official Community attachment linked below and
states that patch 1656 supports revisions 03 and 04. Configuration 1078 is the
cut 1.2 EPP 12 V reference configuration.

Source:
<https://community.st.com/others-hardware-and-software-57/reduced-wireless-charging-efficiency-when-transition-stwlc38-from-chip-revision-0x3-to-0x4-166043>

The 12 V configuration words are staged here with Unix line endings. Run
`./fetch-official-files.sh` from this directory to download and verify the
complete ST package, including patch 1656.

## Important limitation

Configuration 1078 is an ST reference configuration, not a finished
cupwarmer production configuration. Its FOD coefficients are not calibrated
for the LD81FP008-1H coil, ferrite, PCB, enclosure, heater, and cup stack. Do
not connect the heater power lead until the NVM write is verified, protection
actions are checked, and the assembled receiver passes FOD/thermal bring-up.

Before a final release, verify or tune these items in STSW-WPSTUDIO:

- EPP negotiation enabled and EPP VOUT set to 12 V
- external NTC protection enabled, with EPT and VOUT-off actions
- IC overtemperature, OCP, HOVP, and SOVP actions
- GPIO0 function if the status LED is used
- coil/stack-specific BPP and EPP FOD coefficients
- LDO headroom table under the intended load

## DC-mode wiring for NVM programming

Remove the receiver coil from the Qi transmitter and disconnect/insulate the
heater H+ lead. With all sources initially off:

- external USB +5 V -> `J2 pin 1` (`VOUT_12V`, H+ pad)
- external USB GND -> `J2 pin 3` (`SYS_GND`)
- CP2112/PCA9306 GND remains connected to the same `SYS_GND`
- do not apply 5 V to `J1 pin 1` (`RX_VAA`) or to the CP2112 3.3 V pin

Verify approximately 5 V at `J2 pin 1` and approximately 2.5 V at `J1 pin 1`
before attempting an NVM write. Never program the NVM while Qi power is active.

## Provenance hashes

```text
f949f542c16c30c5d133c36dd29a9876bf52f8f2560f69d99f4dc5d9e8b72e6b  STWLC38JRM_config_and_patch_cut1.2_cut1.3.zip
5495b35e175f6fa1c1768e71306692035688e69677a72f423723a2ce27b2efef  STWLC38JRM_Patch_1656_rtx.memh
bff5fe71331070fd3bdb3b2c3d872481dad90ce8b62aed0aed0f91d57576ad6b  STWLC38JRM_Config_1078_cut1.2_EPP12V.memh
ba9a1cc8e4915c3ebfc65410ee237bb87c2e6e70d27004d94d04a38176d1e542  staged config (same words, LF line endings)
```
