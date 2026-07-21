from __future__ import annotations

import fcntl
import hashlib
import os
import plistlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import hid

from .errors import DeviceUnavailable, MonitorError
from .profile import Feature, MonitorProfile
from .protocol import (
    REPORT_SIZE,
    decode_query_response,
    make_query,
    make_write,
    report_payload,
)


@dataclass(frozen=True)
class HidCandidate:
    device: str
    serial: str | None
    path: bytes


def _ioreg_devices(executable: str = "ioreg") -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            (executable, "-a", "-r", "-c", "IOHIDDevice"),
            check=False,
            capture_output=True,
            timeout=5,
        )
    except FileNotFoundError as error:
        raise MonitorError(f"{executable} is not installed") from error
    except subprocess.TimeoutExpired as error:
        raise MonitorError("macOS HID discovery timed out") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise MonitorError(f"macOS HID discovery failed: {detail or 'unknown error'}")
    try:
        devices = plistlib.loads(result.stdout)
    except plistlib.InvalidFileException as error:
        raise MonitorError("macOS HID discovery returned an invalid property list") from error
    if not isinstance(devices, list):
        raise MonitorError("macOS HID discovery returned an unexpected property list")
    return [device for device in devices if isinstance(device, dict)]


def _display_path(path: bytes) -> str:
    return path.decode("utf-8", "backslashreplace")


def discover_candidates(
    profile: MonitorProfile,
    requested_device: str | Path | None = None,
    requested_serial: str | None = None,
    ioreg_executable: str = "ioreg",
) -> list[HidCandidate]:
    verified_identities = {
        (device.get("SerialNumber"), device.get("Product"))
        for device in _ioreg_devices(ioreg_executable)
        if device.get("VendorID") == profile.usb_vendor_id
        and device.get("ProductID") == profile.usb_product_id
        and device.get("ReportDescriptor") == profile.report_descriptor
    }
    requested_path = str(requested_device) if requested_device is not None else None
    matches: list[HidCandidate] = []

    try:
        devices = hid.enumerate(profile.usb_vendor_id, profile.usb_product_id)
    except OSError as error:
        raise DeviceUnavailable(f"cannot enumerate macOS HID devices: {error}") from error

    for device in devices:
        path = device.get("path")
        serial = device.get("serial_number")
        product = device.get("product_string")
        if not isinstance(path, bytes) or (serial, product) not in verified_identities:
            continue
        display_path = _display_path(path)
        if requested_path is not None and display_path != requested_path:
            continue
        if requested_serial is not None and serial != requested_serial:
            continue
        matches.append(HidCandidate(display_path, serial, path))

    if matches:
        return matches
    if requested_device is not None:
        raise DeviceUnavailable(
            f"{requested_device} is not a verified {profile.product_name} controller"
        )
    if requested_serial is not None:
        raise DeviceUnavailable(
            f"verified {profile.product_name} controller with serial {requested_serial!r} is not connected"
        )
    raise DeviceUnavailable(f"verified {profile.product_name} controller is not connected to this host")


class HidDevice:
    def __init__(self, candidate: HidCandidate):
        self.candidate = candidate
        self._device: hid.device | None = None
        self._lock_fd: int | None = None

    def open(self) -> HidDevice:
        if self._device is not None:
            return self
        lock_name = hashlib.sha256(self.candidate.path).hexdigest()
        lock_dir = Path.home() / "Library" / "Caches" / "msi-mpg341c" / "locks"
        lock_fd: int | None = None
        try:
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock_fd = os.open(
                lock_dir / f"{lock_name}.lock",
                os.O_RDWR | os.O_CREAT | os.O_CLOEXEC,
                0o600,
            )
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            if lock_fd is not None:
                os.close(lock_fd)
            raise MonitorError(
                f"{self.candidate.device} is busy; another monitor controller is using it"
            ) from error
        except OSError as error:
            if lock_fd is not None:
                os.close(lock_fd)
            raise MonitorError(f"cannot lock {self.candidate.device}: {error}") from error
        assert lock_fd is not None

        try:
            device = hid.device()
            device.open_path(self.candidate.path)
        except OSError as error:
            os.close(lock_fd)
            raise DeviceUnavailable(f"cannot open {self.candidate.device}: {error}") from error
        self._lock_fd = lock_fd
        self._device = device
        return self

    def close(self) -> None:
        if self._device is not None:
            self._device.close()
            self._device = None
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None

    def __enter__(self) -> HidDevice:
        return self.open()

    def __exit__(self, *_: object) -> None:
        self.close()

    def _handle(self) -> hid.device:
        if self._device is None:
            raise MonitorError("internal error: HID device is not open")
        return self._device

    def _drain(self) -> None:
        device = self._handle()
        while device.read(REPORT_SIZE, 1):
            pass

    def query(self, feature_name: str, feature: Feature, timeout: float = 2.0) -> int:
        report, expected_prefix = make_query(feature_name, feature)
        device = self._handle()
        try:
            self._drain()
            written = device.write(report)
            if written != REPORT_SIZE:
                raise MonitorError(f"short HID write: {written}/{REPORT_SIZE} bytes")

            deadline = time.monotonic() + timeout
            while True:
                remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
                if remaining_ms == 0:
                    raise MonitorError(f"monitor did not answer the {feature_name} query")
                raw_report = bytes(device.read(REPORT_SIZE, remaining_ms))
                if not raw_report:
                    raise MonitorError(f"monitor did not answer the {feature_name} query")
                payload = report_payload(raw_report)
                if payload is None:
                    continue
                return decode_query_response(feature_name, feature, expected_prefix, payload)
        except OSError as error:
            raise DeviceUnavailable(f"monitor {feature_name} query failed: {error}") from error

    def send(self, feature_name: str, feature: Feature, target: int) -> None:
        report = make_write(feature_name, feature, target)
        device = self._handle()
        try:
            self._drain()
            written = device.write(report)
            if written != REPORT_SIZE:
                raise MonitorError(f"short HID write: {written}/{REPORT_SIZE} bytes")
        except OSError as error:
            raise DeviceUnavailable(f"monitor {feature_name} write failed: {error}") from error
