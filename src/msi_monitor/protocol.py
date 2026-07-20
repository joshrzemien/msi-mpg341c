from __future__ import annotations

from .errors import MonitorError
from .profile import Feature

REPORT_ID = 0x01
REPORT_SIZE = 64


def make_report(payload: bytes) -> bytes:
    if len(payload) > REPORT_SIZE - 1:
        raise MonitorError("internal error: HID payload is too long")
    return bytes((REPORT_ID,)) + payload.ljust(REPORT_SIZE - 1, b"\0")


def make_query(feature_name: str, feature: Feature) -> tuple[bytes, bytes]:
    if feature.key is None:
        raise MonitorError(f"internal error: {feature_name} has no HID key")
    key = feature.key.encode("ascii")
    return make_report(b"58" + key + b"\r"), b"5b" + key


def make_write(feature_name: str, feature: Feature, target: int) -> bytes:
    if feature.key is None:
        raise MonitorError(f"internal error: {feature_name} has no HID key")
    if not 0 <= target <= 999:
        raise MonitorError(f"internal error: {feature_name} value does not fit the HID protocol")
    payload = b"5b" + feature.key.encode("ascii") + f"{target:03d}".encode("ascii") + b"\r"
    return make_report(payload)


def report_payload(report: bytes) -> bytes | None:
    if len(report) != REPORT_SIZE or report[0] != REPORT_ID:
        return None
    return report[1:].split(b"\0", 1)[0]


def decode_query_response(
    feature_name: str,
    feature: Feature,
    expected_prefix: bytes,
    payload: bytes,
) -> int:
    if len(payload) == 6 and payload[:2] == b"56" and payload[-1:] == b"\r":
        code = payload[4:5].decode("ascii", "replace")
        raise MonitorError(f"monitor rejected the {feature_name} query with code {code}")
    if len(payload) != 11 or payload[:7] != expected_prefix or payload[10] != 0x0D:
        raise MonitorError(f"unexpected {feature_name} response: {payload.hex(' ')}")
    if feature.decoder == "model":
        return payload[9] - 0x30
    if feature.decoder == "uart":
        if payload[7] != ord("V") or not payload[8:10].isdigit():
            raise MonitorError(f"unexpected UART response: {payload.hex(' ')}")
        return int(payload[8:10])
    if not payload[7:10].isdigit():
        raise MonitorError(f"non-numeric {feature_name} response: {payload.hex(' ')}")
    return int(payload[7:10])
