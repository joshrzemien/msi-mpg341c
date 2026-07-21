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
        display: str | None = None,
        platform_name: str = sys.platform,
    ):
        self.profile = profile
        self.bus = bus
        self.display = display
        self.platform_name = platform_name
        self.executable = executable or (
            "betterdisplaycli" if platform_name == "darwin" else "ddcutil"
        )
        self._selected_display: str | None = None

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


    def _mac_selector(self) -> str:
        if self._selected_display is not None:
            return self._selected_display
        if self.bus is not None:
            raise MonitorError("--ddc-bus is only supported on Linux; use --ddc-display on macOS")

        selectors = (
            f"--vendor={self.profile.edid_vendor_id}",
            f"--model={self.profile.edid_product_id}",
            f"--productName={self.profile.ddc_model}",
        )
        if self.display is not None:
            selectors = (f"--UUID={self.display}", *selectors)
        output = self._run("get", *selectors, "--identifier=UUID")
        matches = [line.strip() for line in output.splitlines() if line.strip()]

        if self.display is not None and matches != [self.display]:
            raise MonitorError(
                f"{self.display!r} is not a verified {self.profile.product_name} DDC display"
            )

        if not matches:
            raise MonitorError(
                f"verified {self.profile.product_name} DDC display is not connected"
            )
        if len(matches) > 1:
            raise MonitorError(
                f"refusing ambiguous verified DDC displays: {', '.join(matches)}; "
                "use --ddc-display"
            )
        self._selected_display = matches[0]
        return self._selected_display

    def query_input(self) -> int:
        if self.platform_name == "darwin":
            output = self._run(
                "get",
                f"--UUID={self._mac_selector()}",
                "--ddc",
                "--vcp=0x60",
                "--value",
            )
            try:
                value = int(output, 10)
            except ValueError as error:
                raise MonitorError(f"unexpected DDC input response: {output!r}") from error
            accepted = self.profile.features["input"].choices
            if accepted is None or value not in accepted.values():
                raise MonitorError(f"unexpected DDC input value: 0x{value:02x}")
            return value
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
        if self.platform_name == "darwin":
            self._run(
                "set",
                f"--UUID={self._mac_selector()}",
                "--ddc",
                "--vcp=0x60",
                f"--value={target}",
            )
            return
        if self.platform_name != "linux":
            raise MonitorError(f"DDC input control is not supported on {self.platform_name}")
        self._run(*self._linux_selector(), "setvcp", "60", f"{target:02x}")
