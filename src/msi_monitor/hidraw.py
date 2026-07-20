from __future__ import annotations

import fcntl
import os
import select
import time
from dataclasses import dataclass
from pathlib import Path

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
class HidrawCandidate:
    device: Path
    serial: str | None


def _sysfs_device_dir(node: Path) -> Path:
    return Path(os.path.realpath(node / "device"))


def _property(lines: set[str], name: str) -> str | None:
    prefix = f"{name}="
    return next((line[len(prefix) :] for line in lines if line.startswith(prefix)), None)


def discover_candidates(
    profile: MonitorProfile,
    requested_device: Path | None = None,
    requested_serial: str | None = None,
    sysfs_root: Path = Path("/sys/class/hidraw"),
    dev_root: Path = Path("/dev"),
) -> list[HidrawCandidate]:
    matches: list[HidrawCandidate] = []
    requested_path = requested_device.resolve() if requested_device is not None else None

    for sysfs_node in sorted(sysfs_root.glob("hidraw*")):
        device_dir = _sysfs_device_dir(sysfs_node)
        try:
            identity = set((device_dir / "uevent").read_text().splitlines())
            descriptor = (device_dir / "report_descriptor").read_bytes()
        except OSError:
            continue
        device = (dev_root / sysfs_node.name).resolve()
        if profile.hid_id not in identity or descriptor != profile.report_descriptor:
            continue
        serial = _property(identity, "HID_UNIQ")
        if requested_path is not None and device != requested_path:
            continue
        if requested_serial is not None and serial != requested_serial:
            continue
        matches.append(HidrawCandidate(device=device, serial=serial))

    if matches:
        return matches
    if requested_device is not None:
        raise DeviceUnavailable(f"{requested_device} is not a verified {profile.product_name} controller")
    if requested_serial is not None:
        raise DeviceUnavailable(
            f"verified {profile.product_name} controller with serial {requested_serial!r} is not connected"
        )
    raise DeviceUnavailable(f"verified {profile.product_name} controller is not connected to this host")


class HidrawDevice:
    def __init__(self, candidate: HidrawCandidate):
        self.candidate = candidate
        self._fd: int | None = None

    def open(self) -> HidrawDevice:
        if self._fd is not None:
            return self
        try:
            fd = os.open(
                self.candidate.device,
                os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC,
            )
        except PermissionError as error:
            raise MonitorError(
                f"permission denied for {self.candidate.device}; reconnect the monitor or check its udev rule"
            ) from error
        except OSError as error:
            raise DeviceUnavailable(f"cannot open {self.candidate.device}: {error}") from error
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            os.close(fd)
            raise MonitorError(
                f"{self.candidate.device} is busy; another monitor controller is using it"
            ) from error
        except OSError:
            os.close(fd)
            raise
        self._fd = fd
        return self

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> HidrawDevice:
        return self.open()

    def __exit__(self, *_: object) -> None:
        self.close()

    def _fileno(self) -> int:
        if self._fd is None:
            raise MonitorError("internal error: HID device is not open")
        return self._fd

    def _drain(self) -> None:
        fd = self._fileno()
        while True:
            try:
                if not os.read(fd, REPORT_SIZE):
                    return
            except BlockingIOError:
                return

    def query(self, feature_name: str, feature: Feature, timeout: float = 2.0) -> int:
        report, expected_prefix = make_query(feature_name, feature)
        fd = self._fileno()
        try:
            self._drain()
            written = os.write(fd, report)
            if written != REPORT_SIZE:
                raise MonitorError(f"short HID write: {written}/{REPORT_SIZE} bytes")

            poller = select.poll()
            poller.register(fd, select.POLLIN)
            deadline = time.monotonic() + timeout
            while True:
                remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
                if remaining_ms == 0 or not poller.poll(remaining_ms):
                    raise MonitorError(f"monitor did not answer the {feature_name} query")
                try:
                    raw_report = os.read(fd, REPORT_SIZE)
                except BlockingIOError:
                    continue
                payload = report_payload(raw_report)
                if payload is None:
                    continue
                return decode_query_response(feature_name, feature, expected_prefix, payload)
        except OSError as error:
            raise DeviceUnavailable(f"monitor {feature_name} query failed: {error}") from error

    def send(self, feature_name: str, feature: Feature, target: int) -> None:
        report = make_write(feature_name, feature, target)
        fd = self._fileno()
        try:
            self._drain()
            written = os.write(fd, report)
            if written != REPORT_SIZE:
                raise MonitorError(f"short HID write: {written}/{REPORT_SIZE} bytes")
        except OSError as error:
            raise DeviceUnavailable(f"monitor {feature_name} write failed: {error}") from error
