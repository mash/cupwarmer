# CP2112 / STWLC38 bench programmer

This is a custom, experimental adapter, **not an ST-supported programming tool**.
It passed a volatile buffer round-trip and programmed the bench device on
2026-09-23; see [the session record](2026-09-23-stwlc38-nvm-programming.md).
The default operation reads chip information only (CP2112's volatile bus settings
are temporarily configured and restored). Never connect Qi power or the heater
while using a mutating mode. Keep a stable external 5 V on VOUT, VAA at about 2.5 V,
CP2112 VREF2 at 3.3 V, and all grounds connected.

## Sources and provenance

- ST reference sequence: `stwlc38/stwlc38.c` and `.h`, driver v1.0.0 (2023),
  preserved in [this repository](https://github.com/Andrew0050/STWirelessCharging-C-Drivers/tree/ea0110e4b7088c8dcd9d824da8c645105c26bc51/stwlc38).
  The former `STMicroelectronics/STWirelessCharging-C-Drivers` repository was not
  accessible on 2026-09-23. The preserved history attributes the code to ST, but
  it is a third-party mirror, not a currently official distribution endpoint.
  Source C SHA-256: `7e0736267875a4bec0f99c6a10c0a98107dfeb733f92967c42694b18b5a5171b`.
- CP2112 framing and bounds: [Silicon Labs AN495](https://www.silabs.com/documents/public/application-notes/an495-cp2112-interface-specification.pdf).
- Firmware source and hashes: [staging README](../firmware/stwlc38/README.md).
- Byte order cross-check: the preserved WPSTUDIO-generated `nvm_data.h` arrays
  are compared with their original `.memh` words as 32-bit little-endian bytes.

## Modes

Run with `uv run --no-project --with hidapi python hardware/test/stwlc38_program.py`.
Every operation requires `--serial 00E1E3D6` (the confirmed bench adapter).

- No mode flag: validate pinned files, then read chip/ROM/revision/cut/IDs/errors/mode.
- `--buffer-test --dc-5v-heater-disconnected`: reset without NVM loading, unlock
  the programming interface, stage 256 bytes in the volatile AUX buffer in
  32-byte chunks, read back all bytes, unmap and reset. The NVM commit command is
  blocked in this mode. Original IDs/error status must match after reset.
- `--program --dc-5v-heater-disconnected`: run the buffer test first, then write
  patch sectors from 0 and configuration sectors from 126, following the ST
  reference sequence. Verify every staged buffer before issuing its commit.
  Reset and require patch `0x1656`, configuration `0x1078`, and no system/NVM error.

The reference C driver sends a whole 256-byte sector buffer in one transaction.
CP2112 can send only 61 I2C bytes per report, including the register address.
This adapter uses explicitly addressed 32-byte chunks. Its critical additional
validation is the real-device buffer test: offline tests do not prove the chip
accepts this change. Do not bypass a failed buffer test.

The reset command may NACK according to the ST reference README. Only address
NACK / incomplete write on the exact reset operations is tolerated, followed by
mandatory chip reads. Other failures abort. There are **no automatic NVM retries**.

This is not a full backup of the previous NVM. The read-only register snapshot
records identity/status, not a recoverable firmware image. A partial write can
leave the target unable to boot its previous patch. If programming fails, retain
stable DC power, keep the heater isolated, and inspect the log before any retry.

After successful programming, perform a manual DC power cycle and read-only
verification. The reference 12 V configuration still requires protection, FOD,
and thermal validation before connecting the heater.

Offline tests:

```sh
python3 -m unittest discover -s hardware/test -p 'test_stwlc38_program.py' -v
```

## ST reference license (BSD 3-Clause)

Copyright (c) 2023, STMicroelectronics - All Rights Reserved
Author(s): ACD (Analog Custom Devices) Software Team for STMicroelectronics.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
