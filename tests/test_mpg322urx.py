from pathlib import Path

import pytest

from msi_monitor.cli import _detect_profile, main
from msi_monitor.controller import Controller
from msi_monitor.errors import MonitorError
from msi_monitor.hidraw import discover_candidates
from msi_monitor.profile import (
    FEATURES,
    MPG322URX,
    MPG322URX_UNSUPPORTED,
    MPG341CX,
    PROFILES,
    format_feature_value,
    parse_feature_value,
)


def test_profile_identity():
    assert MPG322URX.model_id == 126
    assert MPG322URX.uart_version == 21
    assert MPG322URX.tested_firmware == (24,)
    assert MPG322URX.hid_id == MPG341CX.hid_id
    assert MPG322URX.report_descriptor != MPG341CX.report_descriptor
    assert PROFILES == (MPG341CX, MPG322URX)


def test_unanswered_features_are_not_exposed():
    assert MPG322URX_UNSUPPORTED.isdisjoint(MPG322URX.features)
    assert MPG322URX_UNSUPPORTED.isdisjoint(MPG322URX.status_features)
    assert "deep-sleep" not in MPG322URX.features
    assert set(MPG322URX.status_features) <= MPG322URX.features.keys()


def test_mpg341cx_catalog_is_unchanged():
    assert MPG341CX.features is FEATURES
    for name in ("navi-up", "power-button", "smart-crosshair", "rgb-led"):
        assert name not in FEATURES


def test_every_322urx_feature_fits_the_wire_protocol():
    for name, feature in MPG322URX.features.items():
        if feature.source == "hid":
            assert feature.key is not None and len(feature.key) == 5, name
        if feature.writable and feature.choices is not None:
            assert all(0 <= value <= 999 for value in feature.choices.values()), name


def test_values_are_parsed_against_the_selected_profile():
    features = MPG322URX.features
    assert parse_feature_value("display-hdr", "eotf-boost", features) == 2
    assert format_feature_value("display-hdr", 2, features) == "eotf-boost (2)"
    assert format_feature_value("navi-left", 11, features) == "kvm (11)"
    assert parse_feature_value("pro-mode", "eco", features) == 7
    with pytest.raises(MonitorError):
        parse_feature_value("display-hdr", "eotf-boost")  # not an MPG 341C mode


def test_hdr_mode_change_requires_disconnect_acknowledgement():
    assert MPG322URX.features["display-hdr"].safety == "disconnect"


def _sysfs_node(tmp_path: Path, descriptor: bytes):
    sysfs_root = tmp_path / "sys"
    device_dir = tmp_path / "devices" / "controller"
    dev_root = tmp_path / "dev"
    device_dir.mkdir(parents=True)
    dev_root.mkdir()
    (sysfs_root / "hidraw3").mkdir(parents=True)
    (sysfs_root / "hidraw3" / "device").symlink_to(device_dir)
    (dev_root / "hidraw3").touch()
    (device_dir / "uevent").write_text(f"{MPG322URX.hid_id}\nHID_UNIQ=SERIAL-3\n")
    (device_dir / "report_descriptor").write_bytes(descriptor)
    return sysfs_root, dev_root


def test_hidraw_discovery_tells_the_models_apart(tmp_path):
    sysfs_root, dev_root = _sysfs_node(tmp_path, MPG322URX.report_descriptor)

    assert len(discover_candidates(MPG322URX, sysfs_root=sysfs_root, dev_root=dev_root)) == 1
    with pytest.raises(MonitorError):
        discover_candidates(MPG341CX, sysfs_root=sysfs_root, dev_root=dev_root)


def test_cli_detects_the_connected_profile(monkeypatch):
    def only_322urx(profile, **_kwargs):
        if profile is MPG322URX:
            return ["candidate"]
        raise MonitorError("not connected")

    monkeypatch.setattr("msi_monitor.cli.discover_candidates", only_322urx)
    assert _detect_profile(None, None) is MPG322URX


def test_cli_falls_back_to_mpg341cx_when_nothing_matches():
    assert _detect_profile(None, None) is MPG341CX


def test_cli_rejects_features_missing_on_the_detected_model(monkeypatch, capsys):
    monkeypatch.setattr("msi_monitor.cli._detect_profile", lambda *_: MPG322URX)

    assert main(["get", "black-equalizer"]) == 1
    assert "not supported on the MSI MPG 322URX" in capsys.readouterr().err


def test_controller_accepts_the_322urx_identity(monkeypatch):
    class FakeHid:
        def __init__(self, _candidate):
            pass

        def open(self):
            return self

        def close(self):
            pass

        def query(self, name, _feature):
            return {"model": 126, "uart-version": 21}[name]

    monkeypatch.setattr(
        "msi_monitor.controller.discover_candidates",
        lambda *_args, **_kwargs: [type("C", (), {"device": "/dev/hidraw3"})()],
    )
    monkeypatch.setattr("msi_monitor.controller.HidDevice", FakeHid)

    controller = Controller(profile=MPG322URX, platform_name="linux")
    assert controller.read_feature("model") == 126
