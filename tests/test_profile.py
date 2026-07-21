import pytest

from msi_monitor.errors import MonitorError
from msi_monitor.profile import (
    FEATURES,
    MPG341CX,
    accepted_values,
    format_feature_value,
    parse_feature_value,
)


def test_verified_profile_identity():
    assert MPG341CX.model_id == 117
    assert MPG341CX.uart_version == 21
    assert MPG341CX.tested_firmware == (20,)
    assert MPG341CX.hid_id == "HID_ID=0003:00001462:00003FA4"
    assert MPG341CX.edid_vendor_id == 0x3669
    assert MPG341CX.edid_product_id == 0x4DD0
    assert len(MPG341CX.report_descriptor) == 95


def test_public_feature_catalog_is_complete():
    assert len(FEATURES) == 44
    assert set(MPG341CX.status_features) <= FEATURES.keys()


def test_every_hid_feature_has_a_valid_wire_key():
    for name, feature in FEATURES.items():
        if feature.source == "hid":
            assert feature.key is not None, name
            assert len(feature.key) == 5, name
            feature.key.encode("ascii")


def test_every_writable_feature_has_a_bounded_domain():
    for name, feature in FEATURES.items():
        if not feature.writable:
            continue
        if feature.choices is not None:
            assert feature.choices, name
            assert all(0 <= value <= 999 for value in feature.choices.values()), name
        else:
            assert feature.minimum is not None, name
            assert feature.maximum is not None, name
            assert 0 <= feature.minimum <= feature.maximum <= 999, name


def test_parse_enum_is_case_insensitive():
    assert parse_feature_value("response-time", "FAST") == 1


def test_parse_rejects_unknown_enum():
    with pytest.raises(MonitorError, match="choose: normal, fast, fastest"):
        parse_feature_value("response-time", "turbo")


def test_parse_accepts_numeric_boundary_values():
    assert parse_feature_value("brightness", "0") == 0
    assert parse_feature_value("brightness", "100") == 100


@pytest.mark.parametrize("raw", ["-1", "101"])
def test_parse_rejects_numeric_values_outside_bounds(raw):
    with pytest.raises(MonitorError):
        parse_feature_value("brightness", raw)


def test_format_enum_numeric_and_input_values():
    assert format_feature_value("response-time", 1) == "fast (1)"
    assert format_feature_value("brightness", 43) == "43"
    assert format_feature_value("input", 0x11) == "hdmi-1 (0x11)"
    assert format_feature_value("osd-timeout", 20) == "20 seconds (20)"


def test_accepted_values_describe_cli_domain():
    assert accepted_values(FEATURES["model"]) == "read-only"
    assert accepted_values(FEATURES["brightness"]) == "0..100"
    assert accepted_values(FEATURES["kvm"]) == "auto|upstream|type-c"
