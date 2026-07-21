import json

from msi_monitor.cli import main, parse_args
from msi_monitor.controller import ChangeResult


def test_no_command_defaults_to_status():
    assert parse_args([]).command == "status"


def test_global_device_selectors_are_parsed():
    args = parse_args(
        ["--serial", "ABC", "--ddc-bus", "3", "--ddc-display", "UUID", "get", "input"]
    )

    assert args.serial == "ABC"
    assert args.ddc_bus == 3
    assert args.ddc_display == "UUID"
    assert args.command == "get"


def test_json_feature_list_is_machine_readable(capsys):
    assert main(["--json", "list"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["schema_version"] == 1
    assert output["features"]["brightness"]["accepted"] == "0..100"
    assert output["features"]["kvm"]["safety"] == "disconnect"


def test_set_output_preserves_human_contract(monkeypatch, capsys):
    class FakeController:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def change_feature(self, *_args):
            return ChangeResult("brightness", 43, 44, "switched", verified=44)

    monkeypatch.setattr("msi_monitor.cli.Controller", FakeController)

    assert main(["set", "brightness", "44"]) == 0
    assert capsys.readouterr().out == "switched brightness: 43 -> 44\n"


def test_unverified_json_write_uses_exit_two(monkeypatch, capsys):
    class FakeController:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def change_feature(self, *_args):
            return ChangeResult(
                "kvm",
                0,
                2,
                "sent-unverified",
                verification_error="USB moved",
            )

    monkeypatch.setattr("msi_monitor.cli.Controller", FakeController)

    assert main(["--json", "set", "kvm", "type-c", "--allow-disconnect"]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "sent-unverified"
    assert output["verification_error"] == "USB moved"
