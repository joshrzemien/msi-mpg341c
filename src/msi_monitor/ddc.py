from __future__ import annotations

import subprocess
import sys

from .errors import MonitorError
from .profile import MonitorProfile



class DdcTransport:
    def __init__(
        self,
        profile: MonitorProfile,
        bus: int | None = None,
        executable: str | None = None,
        platform_name: str = sys.platform,
    ):
        self.profile = profile
        self.bus = bus
        self.platform_name = platform_name
        self.executable = executable or "ddcutil"

    def _run(self, *args: str) -> str:
        try:
            result = subprocess.run(
                (self.executable, *args),
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError as error:
            raise MonitorError(f"{self.executable} is not installed") from error
        except subprocess.TimeoutExpired as error:
            raise MonitorError("monitor DDC command timed out") from error
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise MonitorError(f"monitor DDC command failed: {detail or 'unknown error'}")
        return result.stdout.strip()

    def _linux_selector(self) -> tuple[str, ...]:
        if self.bus is not None:
            return ("--bus", str(self.bus))
        return (
            "--mfg",
            self.profile.ddc_manufacturer,
            "--model",
            self.profile.ddc_model,
        )


    def query_input(self) -> int:
        if self.platform_name != "linux":
            raise MonitorError(f"DDC input control is not supported on {self.platform_name}")

        output = self._run(*self._linux_selector(), "--terse", "getvcp", "60")
        fields = output.split()
        if (
            len(fields) != 4
            or fields[:3] != ["VCP", "60", "SNC"]
            or len(fields[3]) < 2
            or fields[3][0] != "x"
        ):
            raise MonitorError(f"unexpected DDC input response: {output!r}")
        try:
            return int(fields[3][1:], 16)
        except ValueError as error:
            raise MonitorError(f"invalid DDC input value: {fields[3]!r}") from error

    def set_input(self, target: int) -> None:
        if self.platform_name != "linux":
            raise MonitorError(f"DDC input control is not supported on {self.platform_name}")
        self._run(*self._linux_selector(), "setvcp", "60", f"{target:02x}")
