import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pico_modules.pico_transmitpackets import CRSFPacketProcessor


class DummySignal:
    def __init__(self):
        self.emitted = []

    def emit(self, payload):
        self.emitted.append(payload)


class DummySerial:
    def __init__(self, frame: bytes):
        self._buffer = bytearray(frame)

    def bytesAvailable(self) -> int:
        return len(self._buffer)

    def readAll(self) -> bytes:
        data = bytes(self._buffer)
        self._buffer.clear()
        return data


def _build_handset_frame(rate: int, offset: int) -> bytes:
    subtype = 0x10
    dest = 0xEA
    orig = 0xEE
    payload = bytes([dest, orig, subtype]) + rate.to_bytes(4, "big") + offset.to_bytes(4, "big")
    frame = bytearray([CRSFPacketProcessor.TELEMETRY_SYNC, len(payload) + 2, 0x3A])
    frame.extend(payload)
    crc = CRSFPacketProcessor.crc8_data(frame[2:])
    frame.append(crc)
    return bytes(frame)


@pytest.mark.parametrize("rate, offset", [(1000, 200), (5000, 0)])
def test_handset_frame_not_dropped(rate, offset):
    frame = _build_handset_frame(rate, offset)

    processor = CRSFPacketProcessor.__new__(CRSFPacketProcessor)
    processor.serial = DummySerial(frame)
    processor.serial_data = DummySignal()
    processor.telemetry_ready = DummySignal()
    processor.error = DummySignal()
    processor._rx_buffer = bytearray()

    processor.read_serial_data()

    assert processor.serial_data.emitted, "Serial bytes should be forwarded"
    assert processor.telemetry_ready.emitted, "Handset telemetry should not be dropped"

    event = processor.telemetry_ready.emitted[0]
    assert event[0] == "handset_timing"
    assert event[1] == 0x10
    assert event[2] == rate
    assert event[3] == offset
    assert event[4] == 0xEA
    assert event[5] == 0xEE


def test_decode_handset_piggyback_payload():
    subtype = 0x10
    rate = 2000
    offset = 50
    payload = bytes([subtype]) + rate.to_bytes(4, "big") + offset.to_bytes(4, "big")

    processor = CRSFPacketProcessor.__new__(CRSFPacketProcessor)
    processor.telemetry_ready = DummySignal()

    consumed = processor._decode_payload(0x3A, payload)

    assert consumed == len(payload)
    assert processor.telemetry_ready.emitted == [
        ("handset_timing", subtype, rate, offset, None, None)
    ]


def test_default_channels_are_neutral_raw_crsf_values():
    processor = CRSFPacketProcessor.__new__(CRSFPacketProcessor)

    channels = processor._normalise_channels([])

    assert channels == [CRSFPacketProcessor.CHANNEL_CENTER] * 16


def test_channel_normalisation_pads_and_clamps_raw_crsf_values():
    processor = CRSFPacketProcessor.__new__(CRSFPacketProcessor)

    channels = processor._normalise_channels([0, 172, 992, 1811, 2500])

    assert channels[:5] == [172, 172, 992, 1811, 1811]
    assert channels[5:] == [CRSFPacketProcessor.CHANNEL_CENTER] * 11
