import pytest

from msi_monitor.controller import Controller
from msi_monitor.errors import DeviceUnavailable, MonitorError


class FakeHid:
    def __init__(self, values):
        self.values = values
        self.sent = []

    def query(self, feature_name, _feature):
        return self.values[feature_name]

    def send(self, feature_name, _feature, target):
        self.sent.append((feature_name, target))
        self.values[feature_name] = target


class FakeDdc:
    def __init__(self, value):
        self.value = value
        self.sent = []

    def query_input(self):
        return self.value

    def set_input(self, target):
        self.sent.append(target)
        self.value = target


def _hid_controller(monkeypatch, feature_name, current):
    controller = Controller(platform_name="linux")
    values = {feature_name: current}
    hid = FakeHid(values)
    monkeypatch.setattr(controller, "read_feature", lambda name: values[name])
    monkeypatch.setattr(controller, "_select_hid", lambda: hid)
    monkeypatch.setattr("msi_monitor.controller.time.sleep", lambda _seconds: None)
    return controller, hid, values


def test_no_op_write_does_not_require_risk_acknowledgement(monkeypatch):
    controller, hid, _ = _hid_controller(monkeypatch, "kvm", 0)

    result = controller.change_feature("kvm", "auto")

    assert result.outcome == "unchanged"
    assert result.exit_code == 0
    assert hid.sent == []


def test_disconnect_risk_is_rejected_before_write(monkeypatch):
    controller, hid, _ = _hid_controller(monkeypatch, "kvm", 0)

    with pytest.raises(MonitorError, match="without --allow-disconnect"):
        controller.change_feature("kvm", "type-c")

    assert hid.sent == []


def test_panel_risk_is_rejected_before_write(monkeypatch):
    controller, hid, _ = _hid_controller(monkeypatch, "pixel-shift", 0)

    with pytest.raises(MonitorError, match="without --allow-panel-risk"):
        controller.change_feature("pixel-shift", "normal")

    assert hid.sent == []


def test_hid_write_is_read_back(monkeypatch):
    controller, hid, _ = _hid_controller(monkeypatch, "brightness", 43)

    result = controller.change_feature("brightness", "44")

    assert hid.sent == [("brightness", 44)]
    assert result.outcome == "switched"
    assert result.current == 43
    assert result.verified == 44


def test_ddc_input_write_is_read_back(monkeypatch):
    controller = Controller(platform_name="linux")
    ddc = FakeDdc(0x11)
    controller.ddc = ddc
    monkeypatch.setattr("msi_monitor.controller.time.sleep", lambda _seconds: None)

    result = controller.change_feature("input", "type-c", allow_disconnect=True)

    assert ddc.sent == [0x10]
    assert result.outcome == "switched"
    assert result.verified == 0x10


def test_macos_input_uses_hid_values(monkeypatch):
    controller = Controller(platform_name="darwin")
    hid = FakeHid({"input": 3})
    monkeypatch.setattr(controller, "_select_hid", lambda: hid)
    monkeypatch.setattr("msi_monitor.controller.time.sleep", lambda _seconds: None)

    assert controller.read_feature("input") == 0x10

    result = controller.change_feature("input", "hdmi-1", allow_disconnect=True)

    assert hid.sent == [("input", 0)]
    assert result.outcome == "switched"
    assert result.current == 0x10
    assert result.verified == 0x11


def test_ddc_input_verification_polls_until_source_changes(monkeypatch):
    controller = Controller(platform_name="linux")
    values = iter((0x10, 0x10, 0x11))
    sent = []
    sleeps = []

    class DelayedDdc:
        def query_input(self):
            return next(values)

        def set_input(self, target):
            sent.append(target)

    controller.ddc = DelayedDdc()
    monkeypatch.setattr("msi_monitor.controller.time.sleep", sleeps.append)

    result = controller.change_feature("input", "hdmi-1", allow_disconnect=True)

    assert sent == [0x11]
    assert sleeps == [0.25, 0.25]
    assert result.outcome == "switched"
    assert result.verified == 0x11


def test_disconnect_after_write_is_reported_as_unverified(monkeypatch):
    controller = Controller(platform_name="linux")
    hid = FakeHid({"kvm": 0})
    read_count = 0

    def read_feature(_name):
        nonlocal read_count
        read_count += 1
        if read_count == 1:
            return 0
        raise DeviceUnavailable("USB moved to the other host")

    monkeypatch.setattr(controller, "read_feature", read_feature)
    monkeypatch.setattr(controller, "_select_hid", lambda: hid)
    monkeypatch.setattr("msi_monitor.controller.time.sleep", lambda _seconds: None)

    result = controller.change_feature("kvm", "type-c", allow_disconnect=True)

    assert result.outcome == "sent-unverified"
    assert result.exit_code == 2
    assert result.verification_error == "USB moved to the other host"
