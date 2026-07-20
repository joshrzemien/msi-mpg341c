from pathlib import Path

import pytest

from msi_monitor.errors import DeviceUnavailable
from msi_monitor.hidraw import discover_candidates
from msi_monitor.profile import MPG341CX


def _create_candidate(tmp_path: Path, descriptor: bytes | None = None):
    sysfs_root = tmp_path / "sys" / "class" / "hidraw"
    device_dir = tmp_path / "devices" / "controller"
    dev_root = tmp_path / "dev"
    sysfs_node = sysfs_root / "hidraw7"
    device_dir.mkdir(parents=True)
    dev_root.mkdir()
    sysfs_node.mkdir(parents=True)
    (sysfs_node / "device").symlink_to(device_dir)
    (dev_root / "hidraw7").touch()
    (device_dir / "uevent").write_text(
        f"{MPG341CX.hid_id}\nHID_NAME=MSI Gaming Controller\nHID_UNIQ=SERIAL-7\n"
    )
    (device_dir / "report_descriptor").write_bytes(
        MPG341CX.report_descriptor if descriptor is None else descriptor
    )
    return sysfs_root, dev_root, (dev_root / "hidraw7").resolve()


def test_discovery_matches_identity_descriptor_and_serial(tmp_path):
    sysfs_root, dev_root, expected_device = _create_candidate(tmp_path)

    candidates = discover_candidates(
        MPG341CX,
        requested_serial="SERIAL-7",
        sysfs_root=sysfs_root,
        dev_root=dev_root,
    )

    assert [(candidate.device, candidate.serial) for candidate in candidates] == [
        (expected_device, "SERIAL-7")
    ]


def test_discovery_rejects_wrong_serial(tmp_path):
    sysfs_root, dev_root, _ = _create_candidate(tmp_path)

    with pytest.raises(DeviceUnavailable, match="serial 'OTHER'"):
        discover_candidates(
            MPG341CX,
            requested_serial="OTHER",
            sysfs_root=sysfs_root,
            dev_root=dev_root,
        )


def test_discovery_rejects_wrong_report_descriptor(tmp_path):
    sysfs_root, dev_root, _ = _create_candidate(tmp_path, descriptor=b"not-this-monitor")

    with pytest.raises(DeviceUnavailable, match="not connected"):
        discover_candidates(MPG341CX, sysfs_root=sysfs_root, dev_root=dev_root)


def test_discovery_accepts_verified_explicit_device(tmp_path):
    sysfs_root, dev_root, expected_device = _create_candidate(tmp_path)

    candidates = discover_candidates(
        MPG341CX,
        requested_device=expected_device,
        sysfs_root=sysfs_root,
        dev_root=dev_root,
    )

    assert candidates[0].device == expected_device
