import subprocess

import pytest

from msi_monitor.ddc import DdcTransport
from msi_monitor.errors import MonitorError
from msi_monitor.profile import MPG341CX


def test_query_input_uses_model_selector_and_parses_hex(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "VCP 60 SNC x11\n", "")

    monkeypatch.setattr("msi_monitor.ddc.subprocess.run", fake_run)

    assert DdcTransport(MPG341CX, platform_name="linux").query_input() == 0x11
    assert calls[0][0] == (
        "ddcutil",
        "--mfg",
        "MSI",
        "--model",
        "MPG341CX OLED",
        "--terse",
        "getvcp",
        "60",
    )
    assert calls[0][1]["timeout"] == 10


def test_explicit_bus_replaces_model_selector(monkeypatch):
    calls = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr("msi_monitor.ddc.subprocess.run", fake_run)

    DdcTransport(MPG341CX, bus=3, platform_name="linux").set_input(0x10)

    assert calls == [("ddcutil", "--bus", "3", "setvcp", "60", "10")]


def test_query_input_rejects_unexpected_output(monkeypatch):
    def fake_run(args, **_kwargs):
        return subprocess.CompletedProcess(args, 0, "not a VCP response", "")

    monkeypatch.setattr("msi_monitor.ddc.subprocess.run", fake_run)

    with pytest.raises(MonitorError, match="unexpected DDC input response"):
        DdcTransport(MPG341CX, platform_name="linux").query_input()


def test_nonzero_ddcutil_exit_surfaces_error(monkeypatch):
    def fake_run(args, **_kwargs):
        return subprocess.CompletedProcess(args, 1, "", "display is ambiguous")

    monkeypatch.setattr("msi_monitor.ddc.subprocess.run", fake_run)

    with pytest.raises(MonitorError, match="display is ambiguous"):
        DdcTransport(MPG341CX, platform_name="linux").query_input()


def test_macos_query_verifies_display_and_reads_input(monkeypatch):
    calls = []
    responses = iter(
        (
            subprocess.CompletedProcess((), 0, "DISPLAY-UUID\n", ""),
            subprocess.CompletedProcess((), 0, "16\n", ""),
        )
    )

    def fake_run(args, **_kwargs):
        calls.append(args)
        return next(responses)

    monkeypatch.setattr("msi_monitor.ddc.subprocess.run", fake_run)

    assert DdcTransport(MPG341CX, platform_name="darwin").query_input() == 0x10
    assert calls == [
        (
            "betterdisplaycli",
            "get",
            "--vendor=13929",
            "--model=19920",
            "--productName=MPG341CX OLED",
            "--identifier=UUID",
        ),
        (
            "betterdisplaycli",
            "get",
            "--UUID=DISPLAY-UUID",
            "--ddc",
            "--vcp=0x60",
            "--value",
        ),
    ]


def test_macos_set_targets_verified_explicit_display(monkeypatch):
    calls = []
    responses = iter(
        (
            subprocess.CompletedProcess((), 0, "DISPLAY-UUID\n", ""),
            subprocess.CompletedProcess((), 0, "", ""),
        )
    )

    def fake_run(args, **_kwargs):
        calls.append(args)
        return next(responses)

    monkeypatch.setattr("msi_monitor.ddc.subprocess.run", fake_run)

    DdcTransport(
        MPG341CX,
        display="DISPLAY-UUID",
        platform_name="darwin",
    ).set_input(0x10)

    assert calls == [
        (
            "betterdisplaycli",
            "get",
            "--UUID=DISPLAY-UUID",
            "--vendor=13929",
            "--model=19920",
            "--productName=MPG341CX OLED",
            "--identifier=UUID",
        ),
        (
            "betterdisplaycli",
            "set",
            "--UUID=DISPLAY-UUID",
            "--ddc",
            "--vcp=0x60",
            "--value=16",
        ),
    ]


def test_macos_query_rejects_invalid_input_value(monkeypatch):
    responses = iter(
        (
            subprocess.CompletedProcess((), 0, "DISPLAY-UUID\n", ""),
            subprocess.CompletedProcess((), 0, "0\n", ""),
        )
    )
    monkeypatch.setattr(
        "msi_monitor.ddc.subprocess.run",
        lambda *_args, **_kwargs: next(responses),
    )

    with pytest.raises(MonitorError, match="unexpected DDC input value: 0x00"):
        DdcTransport(MPG341CX, platform_name="darwin").query_input()
