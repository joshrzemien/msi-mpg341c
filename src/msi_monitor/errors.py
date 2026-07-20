class MonitorError(RuntimeError):
    """A monitor operation failed safely."""


class DeviceUnavailable(MonitorError):
    """The monitor HID controller is not available on this host."""
