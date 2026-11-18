from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Mapping, Sequence

from . import __version__
from .controller import ChangeResult, Controller
from .errors import DeviceUnavailable, MonitorError
from .hid import discover_candidates
from .profile import (
    MPG341CX,
    PROFILES,
    Feature,
    MonitorProfile,
    accepted_values,
    format_feature_value,
)

SCHEMA_VERSION = 1
ALL_FEATURES = {k: v for p in PROFILES for k, v in p.features.items()}


def _positive_int(raw_value: str) -> int:
    value = int(raw_value, 10)
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control verified MSI QD-OLED monitors (MPG 341C, MPG 322URX).",
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
    get_parser.add_argument("feature", choices=("all", *ALL_FEATURES))

    writable_features = tuple(
        name for name, feature in ALL_FEATURES.items() if feature.writable
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

    features = controller.profile.features
    for feature_name in feature_names:
        feature = features[feature_name]
        if feature.source == "hid" and hid_unavailable is not None:
            readings[feature_name] = {"available": False, "error": hid_unavailable}
            continue
        try:
            value = controller.read_feature(feature_name)
            if json_output:
                readings[feature_name] = {
                    "available": True,
                    "value": value,
                    "formatted": format_feature_value(feature_name, value, features),
                }
            else:
                print(f"{feature_name}: {format_feature_value(feature_name, value, features)}")
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


def _list_features(profile: MonitorProfile, json_output: bool) -> int:
    if json_output:
        features: dict[str, dict[str, object]] = {}
        for name, feature in profile.features.items():
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

    width = max(map(len, profile.features))
    for name, feature in profile.features.items():
        print(f"{name:<{width}}  {accepted_values(feature):<48}  {feature.description}")
    return 0


def _change_output(
    result: ChangeResult, json_output: bool, features: Mapping[str, Feature]
) -> int:
    def fmt(value: int) -> str:
        return format_feature_value(result.feature_name, value, features)

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
        print(f"unchanged {feature_name}: {fmt(result.current)}")
    elif result.outcome == "sent-unverified":
        print(
            f"command sent for {feature_name}: "
            f"{fmt(result.current)} -> "
            f"{fmt(result.target)}; monitor stopped answering before "
            f"verification ({result.verification_error})"
        )
    else:
        assert result.verified is not None
        print(
            f"switched {feature_name}: {fmt(result.current)} -> {fmt(result.verified)}"
        )
    return result.exit_code


def _detect_profile(device: str | None, serial: str | None) -> MonitorProfile:
    """Pick the profile whose USB identity and HID descriptor match a connected monitor."""
    for profile in PROFILES:
        try:
            if discover_candidates(profile, requested_device=device, requested_serial=serial):
                return profile
        except MonitorError:
            continue
    return MPG341CX


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        profile = _detect_profile(args.device, args.serial)
        requested = getattr(args, "feature", "all")
        if requested != "all" and requested not in profile.features:
            raise MonitorError(f"{requested} is not supported on the {profile.product_name}")
        if args.command == "list":
            return _list_features(profile, args.json)
        with Controller(
            profile=profile,
            device=args.device,
            serial=args.serial,
            ddc_bus=args.ddc_bus,
            ddc_executable=args.ddc_executable,
        ) as controller:
            if args.command == "status":
                return _show_features(controller, profile.status_features, args.json)
            if args.command == "get":
                names = list(profile.features) if args.feature == "all" else [args.feature]
                return _show_features(controller, names, args.json)
            if args.command == "set":
                result = controller.change_feature(
                    args.feature,
                    args.value,
                    args.allow_disconnect,
                    args.allow_panel_risk,
                )
                return _change_output(result, args.json, profile.features)
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
