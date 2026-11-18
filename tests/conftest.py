import pytest

from msi_monitor.errors import DeviceUnavailable


@pytest.fixture(autouse=True)
def _no_real_monitor_detection(monkeypatch):
    """Keep CLI tests independent of whatever monitor is attached to the host."""

    def _none_connected(profile, **_kwargs):
        raise DeviceUnavailable(f"{profile.product_name} is not connected")

    monkeypatch.setattr("msi_monitor.cli.discover_candidates", _none_connected)
