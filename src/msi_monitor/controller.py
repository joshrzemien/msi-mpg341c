from __future__ import annotations

import time
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .ddc import DdcTransport
from .errors import DeviceUnavailable, MonitorError
from .hid import HidCandidate, HidDevice, discover_candidates
from .profile import (
    MPG341CX,
    Feature,
    MonitorProfile,
    format_feature_value,
    parse_feature_value,
)

ChangeOutcome = Literal["unchanged", "switched", "sent-unverified"]


@dataclass(frozen=True)
class ChangeResult:
    feature_name: str
    current: int
    target: int
    outcome: ChangeOutcome
    verified: int | None = None
    verification_error: str | None = None

    @property
    def exit_code(self) -> int:
        return 2 if self.outcome == "sent-unverified" else 0


class Controller:
    def __init__(
        self,
        profile: MonitorProfile = MPG341CX,
        device: str | Path | None = None,
        serial: str | None = None,
        ddc_bus: int | None = None,
        ddc_executable: str | None = None,
        platform_name: str = sys.platform,
    ):
        self.profile = profile
        self.platform_name = platform_name
        self.requested_device = device
        self.requested_serial = serial
        self.ddc = DdcTransport(
            profile,
            bus=ddc_bus,
            executable=ddc_executable,
            platform_name=platform_name,
        )
        self._hid: HidDevice | None = None
        self._candidate: HidCandidate | None = None
        self._identity_values: dict[str, int] = {}

    def close(self) -> None:
        if self._hid is not None:
            self._hid.close()
            self._hid = None
            self._candidate = None
            self._identity_values.clear()

    def __enter__(self) -> Controller:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def selected_device(self) -> str | Path | None:
        return self._candidate.device if self._candidate is not None else None

    def _feature(self, feature_name: str) -> Feature:
        try:
            return self.profile.features[feature_name]
        except KeyError as error:
            raise MonitorError(f"unknown feature: {feature_name}") from error

    def _select_hid(self) -> HidDevice:
        if self._hid is not None:
            return self._hid

        candidates = discover_candidates(
            self.profile,
            requested_device=self.requested_device,
            requested_serial=self.requested_serial,
        )
        matches: list[tuple[HidCandidate, HidDevice, int, int]] = []
        failures: list[str] = []
        model_feature = self._feature("model")
        uart_feature = self._feature("uart-version")

        for candidate in candidates:
            device = HidDevice(candidate)
            try:
                device.open()
                model = device.query("model", model_feature)
                uart = device.query("uart-version", uart_feature)
            except MonitorError as error:
                device.close()
                failures.append(f"{candidate.device}: {error}")
                continue
            if model == self.profile.model_id and uart == self.profile.uart_version:
                matches.append((candidate, device, model, uart))
                continue
            device.close()
            failures.append(
                f"{candidate.device}: unsupported profile model={model}, UART={uart}"
            )

        if not matches:
            detail = f" ({'; '.join(failures)})" if failures else ""
            raise DeviceUnavailable(
                f"verified {self.profile.product_name} controller is unavailable{detail}"
            )
        if len(matches) > 1:
            for _, device, _, _ in matches:
                device.close()
            paths = ", ".join(str(candidate.device) for candidate, _, _, _ in matches)
            raise MonitorError(
                f"refusing ambiguous verified monitor controllers: {paths}; use --device or --serial"
            )

        candidate, device, model, uart = matches[0]
        self._candidate = candidate
        self._hid = device
        self._identity_values = {"model": model, "uart-version": uart}
        return device

    def _uses_hid_input(self, feature_name: str) -> bool:
        return (
            feature_name == "input"
            and self.platform_name == "darwin"
            and self.profile.hid_input_feature is not None
        )

    def _input_features(self) -> tuple[Feature, Feature]:
        public_feature = self.profile.features["input"]
        hid_feature = self.profile.hid_input_feature
        if (
            hid_feature is None
            or hid_feature.choices is None
            or public_feature.choices is None
        ):
            raise MonitorError(f"{self.profile.product_name} has no verified HID input profile")
        return public_feature, hid_feature

    def _query_hid_input(self) -> int:
        public_feature, hid_feature = self._input_features()
        hid_value = self._select_hid().query("input", hid_feature)
        for name, value in hid_feature.choices.items():
            if value == hid_value:
                return public_feature.choices[name]
        raise MonitorError(f"unexpected HID input value: {hid_value}")

    def _send_hid_input(self, target: int) -> None:
        public_feature, hid_feature = self._input_features()
        for name, value in public_feature.choices.items():
            if value == target:
                self._select_hid().send("input", hid_feature, hid_feature.choices[name])
                return
        raise MonitorError(f"unsupported HID input target: {target}")

    def read_feature(self, feature_name: str) -> int:
        feature = self._feature(feature_name)
        if self._uses_hid_input(feature_name):
            return self._query_hid_input()
        if feature.source == "ddc":
            return self.ddc.query_input()
        device = self._select_hid()
        if feature_name in self._identity_values:
            return self._identity_values[feature_name]
        return device.query(feature_name, feature)

    def change_feature(
        self,
        feature_name: str,
        raw_value: str,
        allow_disconnect: bool = False,
        allow_panel_risk: bool = False,
    ) -> ChangeResult:
        feature = self._feature(feature_name)
        if not feature.writable:
            raise MonitorError(f"{feature_name} is read-only")
        target = parse_feature_value(feature_name, raw_value)
        current = self.read_feature(feature_name)
        if current == target:
            return ChangeResult(feature_name, current, target, "unchanged", verified=current)
        if feature.safety == "disconnect" and not allow_disconnect:
            raise MonitorError(
                f"refusing {feature_name} {format_feature_value(feature_name, current)} -> "
                f"{format_feature_value(feature_name, target)} without --allow-disconnect"
            )
        if feature.safety == "panel" and not allow_panel_risk:
            raise MonitorError(
                f"refusing OLED-care change {feature_name} without --allow-panel-risk"
            )

        uses_hid_input = self._uses_hid_input(feature_name)
        if uses_hid_input:
            self._send_hid_input(target)
        elif feature.source == "ddc":
            self.ddc.set_input(target)
        else:
            self._select_hid().send(feature_name, feature, target)

        uses_ddc = feature.source == "ddc" and not uses_hid_input
        verification_deadline = time.monotonic() + (5.0 if uses_ddc else 0.25)
        verified = current
        verification_error: MonitorError | None = None
        while True:
            time.sleep(0.25)
            try:
                verified = self.read_feature(feature_name)
                verification_error = None
            except MonitorError as error:
                verification_error = error
            if verification_error is None and verified == target:
                return ChangeResult(
                    feature_name,
                    current,
                    target,
                    "switched",
                    verified=verified,
                )
            if not uses_ddc or time.monotonic() >= verification_deadline:
                break

        if verification_error is not None:
            return ChangeResult(
                feature_name,
                current,
                target,
                "sent-unverified",
                verification_error=str(verification_error),
            )
        raise MonitorError(
            f"{feature_name} verification failed: requested "
            f"{format_feature_value(feature_name, target)}, read back "
            f"{format_feature_value(feature_name, verified)}"
        )
