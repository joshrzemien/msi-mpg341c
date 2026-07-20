import pytest

from msi_monitor.errors import MonitorError
from msi_monitor.profile import FEATURES
from msi_monitor.protocol import (
    REPORT_ID,
    REPORT_SIZE,
    decode_query_response,
    make_query,
    make_report,
    make_write,
    report_payload,
)


def test_make_report_adds_report_id_and_padding():
    report = make_report(b"58abc\r")

    assert len(report) == REPORT_SIZE
    assert report[0] == REPORT_ID
    assert report[1:7] == b"58abc\r"
    assert report[7:] == bytes(REPORT_SIZE - 7)


def test_make_report_rejects_oversized_payload():
    with pytest.raises(MonitorError, match="payload is too long"):
        make_report(bytes(REPORT_SIZE))


def test_make_query_uses_feature_key_and_expected_response_prefix():
    report, prefix = make_query("brightness", FEATURES["brightness"])

    assert report[:9] == b"\x015800400\r"
    assert prefix == b"5b00400"


def test_make_write_formats_three_digit_value():
    report = make_write("brightness", FEATURES["brightness"], 43)

    assert report[:12] == b"\x015b00400043\r"


def test_make_write_rejects_value_outside_wire_format():
    with pytest.raises(MonitorError, match="does not fit"):
        make_write("brightness", FEATURES["brightness"], 1000)


def test_report_payload_strips_padding():
    assert report_payload(make_report(b"payload\r")) == b"payload\r"


def test_report_payload_ignores_wrong_report_id_or_length():
    assert report_payload(bytes(REPORT_SIZE)) is None
    assert report_payload(b"\x01short") is None


def test_decode_numeric_response():
    value = decode_query_response(
        "brightness",
        FEATURES["brightness"],
        b"5b00400",
        b"5b00400043\r",
    )

    assert value == 43


def test_decode_binary_model_identifier():
    value = decode_query_response(
        "model",
        FEATURES["model"],
        b"5b00140",
        b"5b0014000" + bytes((0x30 + 117,)) + b"\r",
    )

    assert value == 117


def test_decode_uart_version():
    value = decode_query_response(
        "uart-version",
        FEATURES["uart-version"],
        b"5b00150",
        b"5b00150V21\r",
    )

    assert value == 21


def test_decode_rejected_query():
    with pytest.raises(MonitorError, match="rejected.*code E"):
        decode_query_response(
            "brightness",
            FEATURES["brightness"],
            b"5b00400",
            b"5600E\r",
        )


def test_decode_rejects_unexpected_key():
    with pytest.raises(MonitorError, match="unexpected brightness response"):
        decode_query_response(
            "brightness",
            FEATURES["brightness"],
            b"5b00400",
            b"5b00410043\r",
        )


def test_decode_rejects_non_numeric_value():
    with pytest.raises(MonitorError, match="non-numeric brightness response"):
        decode_query_response(
            "brightness",
            FEATURES["brightness"],
            b"5b00400",
            b"5b00400abc\r",
        )
