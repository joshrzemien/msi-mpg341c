from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Sequence

from . import __version__
from .controller import ChangeResult, Controller
from .errors import DeviceUnavailable, MonitorError
from .profile import MPG341CX, accepted_values, format_feature_value

SCHEMA_VERSION = 1


def _positive_int(raw_value: str) -> int:
    value = int(raw_value, 10)
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control the verified MSI MPG 341C QD-OLED monitor.",
        epilog=(
            "Examples: msi-monitor get brightness; msi-monitor set brightness 50; "
            "msi-monitor set input type-c --allow-disconnect"
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="emit stable machine-readable JSON")
    parser.add_argument("--device", help="select a specific platform HID device")
    parser.add_argument("--serial", help="select a specific monitor-controller serial")
    parser.add_argument(
        "--ddc-bus",
        type=_positive_int,
        help="select a specific ddcutil I2C bus on Linux",
    )
    parser.add_argument(
        "--ddcutil",
        dest="ddc_executable",
        metavar="PATH",
        help=argparse.SUPPRESS,
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status", help="show important current settings")
    subparsers.add_parser("list", help="list supported feature names and values")

    get_parser = subparsers.add_parser("get", help="read one feature or all features")
    get_parser.add_argument("feature", choices=("all", *MPG341CX.features))

    writable_features = tuple(
        name for name, feature in MPG341CX.features.items() if feature.writable
    )
    set_parser = subparsers.add_parser("set", help="change one validated feature")
    set_parser.add_argument("feature", choices=writable_features)
    set_parser.add_argument("value")
    set_parser.add_argument(
        "--allow-disconnect",
        action="store_true",
        help="acknowledge that this setting can interrupt video or USB routing",
    )
    set_parser.add_argument(
        "--allow-panel-risk",
        action="store_true",
        help="acknowledge changes to OLED protection behavior",
    )
    args = parser.parse_args(argv)
    if args.command is None:
        args.command = "status"
    return args


def _show_features(
    controller: Controller,
    feature_names: Sequence[str],
    json_output: bool,
) -> int:
    failed = False
    hid_unavailable: str | None = None
    readings: dict[str, dict[str, object]] = {}

    for feature_name in feature_names:
        feature = MPG341CX.features[feature_name]
        if feature.source == "hid" and hid_unavailable is not None:
            readings[feature_name] = {"available": False, "error": hid_unavailable}
            continue
        try:
            value = controller.read_feature(feature_name)
            if json_output:
                readings[feature_name] = {
                    "available": True,
                    "value": value,
                    "formatted": format_feature_value(feature_name, value),
                }
            else:
                print(f"{feature_name}: {format_feature_value(feature_name, value)}")
        except DeviceUnavailable as error:
            hid_unavailable = str(error)
            failed = True
            readings[feature_name] = {"available": False, "error": str(error)}
            if not json_output:
                print(f"HID: unavailable ({error})")
        except MonitorError as error:
            failed = True
            readings[feature_name] = {"available": False, "error": str(error)}
            if not json_output:
                print(f"{feature_name}: unavailable ({error})")
        time.sleep(0.04)

    if json_output:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "features": readings}, indent=2))
    return 2 if failed else 0


def _list_features(json_output: bool) -> int:
    if json_output:
        features: dict[str, dict[str, object]] = {}
        for name, feature in MPG341CX.features.items():
            item: dict[str, object] = {
                "description": feature.description,
                "writable": feature.writable,
                "source": feature.source,
                "safety": feature.safety,
                "accepted": accepted_values(feature),
            }
            if feature.choices is not None:
                item["choices"] = dict(feature.choices)
            elif feature.minimum is not None or feature.maximum is not None:
                item["minimum"] = feature.minimum
                item["maximum"] = feature.maximum
            features[name] = item
        print(json.dumps({"schema_version": SCHEMA_VERSION, "features": features}, indent=2))
        return 0

    width = max(map(len, MPG341CX.features))
    for name, feature in MPG341CX.features.items():
        print(f"{name:<{width}}  {accepted_values(feature):<48}  {feature.description}")
    return 0


def _change_output(result: ChangeResult, json_output: bool) -> int:
    feature_name = result.feature_name
    if json_output:
        output: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "feature": feature_name,
            "outcome": result.outcome,
            "current": result.current,
            "target": result.target,
        }
        if result.verified is not None:
            output["verified"] = result.verified
        if result.verification_error is not None:
            output["verification_error"] = result.verification_error
        print(json.dumps(output, indent=2))
        return result.exit_code

    if result.outcome == "unchanged":
        print(f"unchanged {feature_name}: {format_feature_value(feature_name, result.current)}")
    elif result.outcome == "sent-unverified":
        print(
            f"command sent for {feature_name}: "
            f"{format_feature_value(feature_name, result.current)} -> "
            f"{format_feature_value(feature_name, result.target)}; monitor stopped answering before "
            f"verification ({result.verification_error})"
        )
    else:
        assert result.verified is not None
        print(
            f"switched {feature_name}: {format_feature_value(feature_name, result.current)} -> "
            f"{format_feature_value(feature_name, result.verified)}"
        )
    return result.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "list":
            return _list_features(args.json)
        with Controller(
            device=args.device,
            serial=args.serial,
            ddc_bus=args.ddc_bus,
            ddc_executable=args.ddc_executable,
        ) as controller:
            if args.command == "status":
                return _show_features(controller, MPG341CX.status_features, args.json)
            if args.command == "get":
                names = list(MPG341CX.features) if args.feature == "all" else [args.feature]
                return _show_features(controller, names, args.json)
            if args.command == "set":
                result = controller.change_feature(
                    args.feature,
                    args.value,
                    args.allow_disconnect,
                    args.allow_panel_risk,
                )
                return _change_output(result, args.json)
            raise MonitorError(f"unknown command: {args.command}")
    except MonitorError as error:
        if args.json:
            print(
                json.dumps({"schema_version": SCHEMA_VERSION, "error": str(error)}),
                file=sys.stderr,
            )
        else:
            print(f"msi-monitor: {error}", file=sys.stderr)
        return 1
