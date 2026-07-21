from __future__ import annotations

import sys
from pathlib import Path

from .errors import DeviceUnavailable
from .profile import MonitorProfile

if sys.platform == "darwin":
    from .hidmac import HidCandidate, HidDevice, discover_candidates
elif sys.platform == "linux":
    from .hidraw import (
        HidrawCandidate as HidCandidate,
        HidrawDevice as HidDevice,
        discover_candidates,
    )
else:

    class HidCandidate:
        device: str | Path
        serial: str | None

    class HidDevice:
        pass

    def discover_candidates(
        profile: MonitorProfile,
        requested_device: str | Path | None = None,
        requested_serial: str | None = None,
    ) -> list[HidCandidate]:
        del requested_device, requested_serial
        raise DeviceUnavailable(
            f"{profile.product_name} control is not supported on {sys.platform}"
        )


__all__ = ["HidCandidate", "HidDevice", "discover_candidates"]
