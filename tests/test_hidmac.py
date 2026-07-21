import pytest

pytest.importorskip("hid")

from msi_monitor.errors import DeviceUnavailable
from msi_monitor.hidmac import HidCandidate, HidDevice, discover_candidates
from msi_monitor.profile import FEATURES, MPG341CX
from msi_monitor.protocol import make_report, make_query


def _ioreg_device(descriptor):
    return {
        "VendorID": MPG341CX.usb_vendor_id,
        "ProductID": MPG341CX.usb_product_id,
        "Product": "MSI Gaming Controller",
        "SerialNumber": "SERIAL-7",
        "ReportDescriptor": descriptor,
    }


def _hidapi_device():
    return {
        "path": b"DevSrvsID:1234",
        "product_string": "MSI Gaming Controller",
        "serial_number": "SERIAL-7",
    }


def test_discovery_requires_matching_ioreg_report_descriptor(monkeypatch):
    monkeypatch.setattr(
        "msi_monitor.hidmac._ioreg_devices",
        lambda _executable: [_ioreg_device(MPG341CX.report_descriptor)],
    )
    monkeypatch.setattr(
        "msi_monitor.hidmac.hid.enumerate",
        lambda _vendor, _product: [_hidapi_device()],
    )

    candidates = discover_candidates(MPG341CX, requested_serial="SERIAL-7")

    assert candidates == [
        HidCandidate(
            device="DevSrvsID:1234",
            serial="SERIAL-7",
            path=b"DevSrvsID:1234",
        )
    ]


def test_discovery_rejects_wrong_report_descriptor(monkeypatch):
    monkeypatch.setattr(
        "msi_monitor.hidmac._ioreg_devices",
        lambda _executable: [_ioreg_device(b"not-this-monitor")],
    )
    monkeypatch.setattr(
        "msi_monitor.hidmac.hid.enumerate",
        lambda _vendor, _product: [_hidapi_device()],
    )

    with pytest.raises(DeviceUnavailable, match="not connected"):
        discover_candidates(MPG341CX)


def test_hid_query_uses_numbered_reports():
    response = make_report(b"5b0014000" + bytes((0x30 + 117,)) + b"\r")

    class FakeDevice:
        def __init__(self):
            self.writes = []

        def write(self, report):
            self.writes.append(report)
            return len(report)

        def read(self, _size, timeout_ms):
            return [] if timeout_ms == 1 else list(response)

    candidate = HidCandidate("DevSrvsID:1234", "SERIAL-7", b"DevSrvsID:1234")
    device = HidDevice(candidate)
    handle = FakeDevice()
    device._device = handle

    assert device.query("model", FEATURES["model"]) == 117
    assert handle.writes == [make_query("model", FEATURES["model"])[0]]
