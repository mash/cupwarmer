# WPSTUDIO offline inspection — 2026-09-26

## Scope and isolation

Inspect the existing ST configuration `0x1078` without connecting or programming
the receiver. The working Windows VM has no network adapter, USB sharing,
shared directory, or shared clipboard. A separate clean VM backup was made
before running the third-party-mirrored executable. Do not connect this working
VM to the network or physical receiver as part of this inspection.

The inspected application is `STSW-WPSTUDIO V2.1.0.exe`, SHA-256
`33f6058f19d2de1abf7c2dabf5aa983f81adba1151ec1f0c0b417cad3991ac3f`.
This identifies the mirrored file, not its authenticity or suitability for
hardware programming. It was executed only inside the isolated Windows VM.

## Observations

- Programming → CONFIG → Load accepted
  `STWLC38JRM_Config_1078_cut1.2_EPP12V.memh` and displayed
  `CONFIG VERSION: 0x1078`. This establishes version recognition only.
- RX Registers showed no register rows. Its Read/Write/Save/Load controls
  appeared disabled. The Programming view identified the target as
  `[Empty]WLC38`.
- Connection revealed Chip 1 and Chip 2 both set to `Empty`, model `WLC38`,
  address `0x61`, status `Disconnected`.
- The `Empty` dropdown offers `TX` and `RX`. Thus `Empty` is an unselected
  role; it is not itself evidence of a missing/corrupt device definition.
- Static inspection of the executable found a distinct `Load for RX` action
  whose embedded UI help says it populates RX register UI fields from a saved
  MEMH file. This is separate from Programming → CONFIG → Load.
- The staged and original `Project/WLC38.json.enc` files have identical
  SHA-256 `0452957adc3e7b097817b377606fa0078a3dfe7c5a0253c76f18e9c3a77678fe`.
  The file is 720184 bytes. It was subsequently decoded during static inspection
  below; compatibility with this hardware/firmware still requires cross-checking.
- `gzip -t DataFile.bin` succeeds; the generic `file` utility's initial
  "truncated" description is not sufficient evidence of corruption.

During the attempt to select RX, Windows entered `Shutting down` without an
intentional shutdown command. Earlier evaluation-license warnings are a possible
explanation, not a confirmed diagnosis. The result of RX selection was not
observed before shutdown. Do not change licensing, network isolation, or force
power-off merely to bypass this interruption.

## Follow-up after host unlock

Normal shutdown completed and the working VM was restarted without changing
its isolation settings. Windows sign-in and WPSTUDIO startup succeeded; its
JSON loading dialog appeared and closed. After a host-lock interruption, Chip 1
was successfully changed to `RX`, model `WLC38`, address `0x61`, still
`Disconnected`. The Connection dialog was closed without clicking Connect.

Common Registers and RX Registers now display their register categories and
fields. RX selection therefore resolves the previously empty register UI.
However, `Load for RX` remains greyed out alongside Read/Write/Save. Clicking
the visible Load button did not open a file dialog. The Settings dialog contains
logging, chart, and coil-plot options, but no visible offline-mode switch; no
settings were changed. This establishes a limitation of the observed disconnected
GUI state, not proof that a physical adapter is the only possible solution.

RX Registers → Rx Protections visibly includes:

- `RX ADC NTC EN PROT`
- `RX ADC NTC EPT`
- `RX ADC NTC VOUT OFF`

These boxes are unchecked in the uninitialized GUI. **They are not values read
from config 1078 or from the physical receiver.** `RX Protection Threshold` is
also present as a category, but its values have not been decoded.

The VM remains offline with no USB passthrough. Do not attach the physical
receiver merely to enable GUI controls. A next non-hardware route is to inspect
the file-loading logic/device definitions without executing the mirrored
application on the host, then cross-check any mapping against official material.

## Static inspection of config 1078

The executable was parsed as PE/.NET data with `dnfile`/`dncil`; it was **not
executed on the Mac**. The bundled WLC38 definition was decoded in memory using
the application's embedded resource and Fernet authentication verification.
Neither the resource value nor the full decoded definition was written to this
repository. Definition metadata: version `1.0.0`, target `polaris`, JSON version
`1.5.29`. These are provenance details, not a vendor authenticity guarantee.

`RegistersCommonViewModel.ToConfigBytes` (method token `0x06000722`) parses each
MEMH line as UInt32 hexadecimal and uses `BitConverter.GetBytes`. On the x86
Windows VM this yields four little-endian bytes per line, matching the existing
programmer's `parse_memh`. `LoadRxMemh` (`0x0600071c`) uses the Config memory map.
Its helper `WriteToI2CRegister` (`0x0600071f`) assembles mapped bitfields and sets
the UI model's Value; the method name alone is not evidence of a hardware write.
The Value setter raises events, so this partial call-path analysis is not a
guarantee that invoking Load on a connected device is side-effect-free.

The UI resources contain `VM.RxChipState.IsConnected` bindings near the load
controls, consistent with the observed disconnected/disabled state. RAM shortage
is not established as the cause of the disabled Load button.

Input: `STWLC38JRM_Config_1078_cut1.2_EPP12V.memh`, 384 decoded bytes, SHA-256
`ba9a1cc8e4915c3ebfc65410ee237bb87c2e6e70d27004d94d04a38176d1e542`.
The following are **file-derived values interpreted with the mirrored WLC38
definition**, not GUI defaults and not a fresh read of the physical receiver.
Offsets below are Config-file byte offsets, **not I2C register addresses**.

| Field | Config offset / bits | File value | Interpretation from definition |
|---|---|---|---|
| `ovtp_adc_ntc_en` | `0x68`, bit 2 | 0 | ADC NTC protection disabled |
| `ovtp_adc_ntc_ept_en` | `0x6c`, bit 2 | 0 | ADC NTC EPT action disabled |
| `ovtp_adc_ntc_vout_off_en` | `0x70`, bit 2 | 0 | ADC NTC VOUT-off action disabled |
| `ovtp_ntc_tshut_en` | `0x68`, bit 4 | 0 | NTC TSHUT path disabled |
| `ovtp_ntc_ept_en` / `ovtp_ntc_vout_off_en` | `0x6c` / `0x70`, bit 4 | 0 / 0 | NTC TSHUT EPT / VOUT-off disabled |
| `ovtp_adc_ntc_thres` | `0x7a`, 16 bits | 0 | 0 mV according to `u*0.1` scaling; not a usable temperature limit |
| BPP VOUT high / low | `0x3a` / `0x39` bits 6–7 | 45 / 0 | 5.0 V |
| EPP VOUT high / low | `0x143` / `0x142` bits 6–7 | 115 / 0 | 12.0 V |

Independent raw-text checks: MEMH lines 27–29 are `0003A401`, `00030401`,
`00030401`; bit 2 and bit 4 are clear in each. Line 31 is `00000002`, so bytes
`0x7a–0x7b` are zero. Line 81 is `7300A216`, placing `0x73` at offset `0x143`.
The VOUT interpretations agree with the EPP12V filename, a useful consistency
check but not proof of all map/firmware compatibility.

UM3154 Rev 2 §5.9.6 independently describes the external NTC divider, low-voltage
threshold at the maximum permitted temperature, and optional VOUT-off/EPT
actions. It does not establish this config file's offsets or recovery behavior.
Existing design notes target approximately 69°C with a 100k/B4260 NTC and 51k
pull-up; that target is not validated merely by loading the generic config.

**Do not reconnect the heater based on generic config 1078 alone.** Next checks
are exact map/firmware compatibility, actual NTC part/thermal contact, threshold
selection, and power-off/recovery testing with the heater disconnected first.
Recovery/latching behavior and actual hardware protection remain unverified.
No firmware/config was modified, and no hardware reads/writes occurred.

## GUI edit and Save RX experiment

At the user's suggestion, tested whether changing an RX value enables export
without a receiver. In RX Registers / Rx Protections, toggling
`RX ADC NTC EN PROT` produced a checked box and the text `Enable`. Thus the
disconnected GUI does allow this model value to be edited.

`Save RX` remained grey after the edit. Two clicks with the guest pointer visibly
on that button did not open a save dialog. No export was produced. This is
consistent with connection gating, not proof that memory is insufficient.
The temporary checkbox was returned to unchecked / `Disable` afterwards.
These were uninitialized GUI values, not a loaded config 1078. No original MEMH
file was overwritten, no Write/Programming command was used, and USB/network
isolation was preserved. An offline RX edit therefore did not unlock saving in
this session.

## USB adapter and config-only write paths

The current executable's `ChipStateModel.Enumeration` (`0x060005c0`) constructs
four backend instances: HidDongle, DingDongle, McpDongle and FT260. Its separate
Device.Net pre-enumeration filters VID/PID `1803:A222`. `ChipStateModel.Connect`
dispatches by backend type; no CP2112 backend was found in these paths.
HidDongle delegates to `stmicro_dongle_enumerate/open`, not a demonstrated
generic CP2112 protocol adapter. The console enumeration exposes FT260 alone.
These findings support treating this copy's CP2112 support as unestablished;
they do not substitute for a full audit of every native binary or all releases.
Windows USB passthrough support does not itself establish WPSTUDIO compatibility.

The embedded STWLC library also contains a distinct config-only branch:
`POLARISFlash.NvmWriting` passes a null patch, requires a 384-byte configuration,
and calls `NvmConfigWriting` (`0x06000188`). That method writes exactly 256 bytes
to sector 126 and 128 bytes to sector 127. It does not call NvmPatchWriting in
the null-patch branch. This corroborates limiting a custom-config update to
those two sectors. It is static evidence from the mirrored binary, not a newly
verified ST distribution or an actual DA01 programming test.

## Next shutdown experiment

The user requested a RAM increase at the next shutdown, not an immediate stop.
Mac physical memory was read as 36 GiB. The working VM was still `started` at
the last status check. A thread heartbeat (`wpstudio`, every 10 minutes) was
created to wait for a stopped state, check host memory pressure, increase only
the working VM from 8 to 12 GiB if there is headroom, restart and retry once,
then end the monitor. All isolation settings and the clean backup must remain
unchanged. More RAM is not claimed to fix connection gating or evaluation
license shutdowns.

### One-time increase performed (2026-09-26, approximately 20:06 UTC)

Heartbeat observed `stopped` without issuing a stop. `memory_pressure` reported
36 GiB physical memory and a system-wide memory free percentage of 72%; no
memory-pressure warning was reported. Through UTM's System UI, the working VM
was changed from 8192 to **12288 MiB** and saved. The saved plist was re-read:
USB sharing false, Network empty, Clipboard sharing false, DirectoryShareMode
None, CPU count 2. Clean Backup remains 4096 MiB and was not edited or started.
The working VM was started once. Windows startup / the offline retry is still
in progress at this record point. **Do not increase memory a second time.**

### One-time retry completed (2026-09-26, approximately 20:27 UTC)

Windows reached the desktop at 12288 MiB. The evaluation-license-expired
watermark remained; no licensing or network settings were changed. Launched
the existing WPSTUDIO V2.1.0 once in the isolated guest and waited for its
`Loading JSON file...` dialog to finish. Selected Chip 1 = RX, WLC38, address
0x61; its status was `Disconnected`. No Connect command was used.

After horizontally scrolling the operation toolbar, `Load for RX` and `Save RX`
were still grey. Clicking `Load for RX` did not open a file dialog. Therefore
config 1078 was **not loaded**: more RAM did not unlock offline loading in this
retry. This does not establish the cause of prior VM shutdowns or validate the
configuration. No Read, Write, Programming, USB passthrough or board operation
was performed. The working VM was left running, and Clean Backup was untouched.

Heartbeat `wpstudio` was changed to `PAUSED`; the automation tool confirmed
that status. This one-time memory experiment and its monitoring are finished.
Do not repeat the memory increase or automatically restart this monitor.
