#!/usr/bin/env python3
"""Read-only CP2112 probe for one 7-bit I2C address."""

from __future__ import annotations

import argparse
import time

import hid


VID = 0x10C4
PID = 0xEA90

REPORT_DATA_READ_REQUEST = 0x10
REPORT_DATA_WRITE_READ_REQUEST = 0x11
REPORT_DATA_READ_FORCE = 0x12
REPORT_DATA_READ_RESPONSE = 0x13
REPORT_TRANSFER_STATUS_REQUEST = 0x15
REPORT_TRANSFER_STATUS_RESPONSE = 0x16
REPORT_CANCEL_TRANSFER = 0x17

STATUS_IDLE = 0x00
STATUS_BUSY = 0x01
STATUS_COMPLETE = 0x02
STATUS_ERROR = 0x03


def probe(
    address: int,
    serial: str | None,
    register: int | None,
    length: int,
) -> int:
    matches = [
        entry
        for entry in hid.enumerate(VID, PID)
        if serial is None or entry.get("serial_number") == serial
    ]
    if not matches:
        print("CP2112 not found")
        return 2

    device = hid.device()
    device.open_path(matches[0]["path"])
    try:
        print(f"CP2112: {device.get_product_string()}")
        print(f"Serial: {device.get_serial_number_string()}")

        # CP2112 expects the target address in 8-bit wire format. STWLC38
        # expects the 16-bit register pointer high byte first.
        if register is None:
            device.write(
                [REPORT_DATA_READ_REQUEST, address << 1, length >> 8, length & 0xFF]
            )
        else:
            device.write(
                [
                    REPORT_DATA_WRITE_READ_REQUEST,
                    address << 1,
                    length >> 8,
                    length & 0xFF,
                    0x02,
                    register >> 8,
                    register & 0xFF,
                ]
            )

        for _ in range(30):
            device.write([REPORT_TRANSFER_STATUS_REQUEST, 0x01])
            response = device.read(64, timeout_ms=100)
            if not response or response[0] != REPORT_TRANSFER_STATUS_RESPONSE:
                time.sleep(0.01)
                continue

            status0 = response[1]
            status1 = response[2]
            retries = (response[3] << 8) | response[4]
            bytes_read = (response[5] << 8) | response[6]

            if status0 in (STATUS_IDLE, STATUS_BUSY):
                time.sleep(0.01)
                continue

            if status0 == STATUS_ERROR:
                print(
                    f"0x{address:02X}: NACK/error "
                    f"(detail=0x{status1:02X}, retries={retries})"
                )
                return 1

            if status0 == STATUS_COMPLETE:
                device.write(
                    [REPORT_DATA_READ_FORCE, length >> 8, length & 0xFF]
                )
                data_response = device.read(64, timeout_ms=200)
                if (
                    data_response
                    and data_response[0] == REPORT_DATA_READ_RESPONSE
                    and len(data_response) >= 3
                ):
                    response_length = data_response[2]
                    data = bytes(data_response[3 : 3 + response_length])
                    location = (
                        ""
                        if register is None
                        else f" register=0x{register:04X}"
                    )
                    print(
                        f"0x{address:02X}: ACK{location} "
                        f"(bytes={bytes_read}, data={data.hex(' ')})"
                    )
                else:
                    print(f"0x{address:02X}: ACK (bytes={bytes_read})")
                return 0

            print(f"0x{address:02X}: unexpected status 0x{status0:02X}")
            return 2

        device.write([REPORT_CANCEL_TRANSFER, 0x01])
        print(f"0x{address:02X}: timed out")
        return 2
    finally:
        device.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=lambda value: int(value, 0), nargs="?", default=0x61)
    parser.add_argument("--serial")
    parser.add_argument("--register", type=lambda value: int(value, 0))
    parser.add_argument("--length", type=int, default=1)
    args = parser.parse_args()

    if not 0x03 <= args.address <= 0x77:
        parser.error("address must be a 7-bit I2C address from 0x03 to 0x77")
    if args.register is not None and not 0 <= args.register <= 0xFFFF:
        parser.error("register must be from 0x0000 to 0xFFFF")
    if not 1 <= args.length <= 61:
        parser.error("length must be from 1 to 61")
    return probe(args.address, args.serial, args.register, args.length)


if __name__ == "__main__":
    raise SystemExit(main())
