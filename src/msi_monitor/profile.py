from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from .errors import MonitorError

FeatureSource = Literal["hid", "ddc"]
SafetyClass = Literal["disconnect", "panel"]


@dataclass(frozen=True)
class Feature:
    key: str | None
    description: str
    writable: bool = True
    choices: Mapping[str, int] | None = None
    minimum: int | None = None
    maximum: int | None = None
    decoder: str = "ascii"
    source: FeatureSource = "hid"
    safety: SafetyClass | None = None
    unit: str = ""
    hexadecimal: bool = False


@dataclass(frozen=True)
class MonitorProfile:
    slug: str
    product_name: str
    usb_vendor_id: int
    usb_product_id: int
    report_descriptor: bytes
    model_id: int
    uart_version: int
    tested_firmware: tuple[int, ...]
    ddc_manufacturer: str
    ddc_model: str
    hid_input_feature: Feature | None
    features: Mapping[str, Feature]
    status_features: tuple[str, ...]

    @property
    def hid_id(self) -> str:
        return f"HID_ID=0003:{self.usb_vendor_id:08X}:{self.usb_product_id:08X}"


BOOLEAN = {"off": 0, "on": 1}
INPUT_SOURCES = {
    "hdmi-1": 0x11,
    "hdmi-2": 0x12,
    "displayport": 0x0F,
    "type-c": 0x10,
}
HID_INPUT_SOURCES = {
    "hdmi-1": 0,
    "hdmi-2": 1,
    "displayport": 2,
    "type-c": 3,
}
HID_INPUT_FEATURE = Feature(
    "00500",
    "Active video input over MSI HID",
    choices=HID_INPUT_SOURCES,
    safety="disconnect",
)


FEATURES: dict[str, Feature] = {
    "input": Feature(
        None,
        "Active video input",
        choices=INPUT_SOURCES,
        source="ddc",
        safety="disconnect",
        hexadecimal=True,
    ),
    "model": Feature(
        "00140",
        "MSI internal model identifier",
        writable=False,
        choices={"mpg341cx-oled": 117},
        decoder="model",
    ),
    "uart-version": Feature("00150", "Monitor protocol version", writable=False, decoder="uart"),
    "firmware-version": Feature("001<0", "Monitor firmware version", writable=False),
    "hdr-active": Feature("00190", "Current HDR signal state", writable=False, choices=BOOLEAN),
    "adaptive-sync-active": Feature(
        "00160", "Current adaptive-sync signal state", writable=False, choices=BOOLEAN
    ),
    "refresh-rate": Feature("00170", "Current refresh rate", writable=False, unit=" Hz"),
    "gaming-mode": Feature("00200", "Current gaming preset index", writable=False),
    "pro-mode": Feature("00300", "Current professional preset index", writable=False),
    "black-equalizer": Feature("00210", "Black equalizer", minimum=0, maximum=20),
    "response-time": Feature(
        "00220",
        "Panel response-time mode",
        choices={"normal": 0, "fast": 1, "fastest": 2},
    ),
    "hdcr": Feature("00240", "Dynamic contrast", choices=BOOLEAN),
    "adaptive-sync": Feature(
        "00280", "Adaptive-Sync setting", choices=BOOLEAN, safety="disconnect"
    ),
    "screen-size": Feature(
        "002:0",
        "Aspect-ratio emulation",
        choices={"auto": 0, "4:3": 1, "16:9": 2, "21:9": 3, "1:1": 4},
    ),
    "eye-care": Feature("00310", "Low-blue-light eye care", choices=BOOLEAN),
    "contrast-enhancer": Feature(
        "00340",
        "Contrast enhancement",
        choices={"off": 0, "weak": 1, "medium": 2, "strong": 3, "strongest": 4},
    ),
    "brightness": Feature("00400", "SDR brightness", minimum=0, maximum=100),
    "contrast": Feature("00410", "Image contrast", minimum=0, maximum=100),
    "sharpness": Feature("00420", "Image sharpness", minimum=0, maximum=5),
    "color-temperature": Feature(
        "00430",
        "Color temperature",
        choices={"normal": 0, "cool": 1, "warm": 2, "custom": 3},
    ),
    "red": Feature("00431", "Custom red channel", minimum=0, maximum=100),
    "green": Feature("00432", "Custom green channel", minimum=0, maximum=100),
    "blue": Feature("00433", "Custom blue channel", minimum=0, maximum=100),
    "night-vision": Feature(
        "002;0",
        "Dark-detail enhancement",
        choices={"off": 0, "normal": 1, "strong": 2, "strongest": 3, "ai": 4},
    ),
    "deep-sleep": Feature("00880", "DisplayPort deep sleep", choices=BOOLEAN),
    "auto-scan": Feature(
        "00510", "Automatic input scanning", choices=BOOLEAN, safety="disconnect"
    ),
    "hdmi-cec": Feature("008:0", "HDMI CEC", choices=BOOLEAN),
    "optix-scope": Feature("002A0", "Optix Scope magnifier", choices=BOOLEAN),
    "kvm": Feature(
        "008>0",
        "USB KVM routing",
        choices={"auto": 0, "upstream": 1, "type-c": 2},
        safety="disconnect",
    ),
    "type-c-pd": Feature("008A0", "Type-C power delivery while asleep", choices=BOOLEAN),
    "hdmi-mode": Feature(
        "008@0",
        "HDMI 2.1 mode",
        choices={"console": 0, "pc": 1},
        safety="disconnect",
    ),
    "display-hdr": Feature(
        "004:0",
        "OLED HDR peak mode",
        choices={"true-black-400": 0, "peak-1000": 1},
    ),
    "dsc": Feature(
        "002D0", "Display Stream Compression", choices=BOOLEAN, safety="disconnect"
    ),
    "power-led": Feature("008B0", "Monitor power LED", choices=BOOLEAN),
    "ai-vision": Feature(
        "002B0",
        "AI Vision image enhancement",
        choices={"off": 0, "level-1": 1, "level-2": 2, "level-3": 3},
    ),
    "pip-pbp": Feature(
        "00600",
        "Picture-in-picture / picture-by-picture mode",
        choices={"off": 0, "pip": 1, "pbp": 2},
        safety="disconnect",
    ),
    "pixel-shift": Feature(
        "00;00",
        "OLED pixel-shift speed",
        choices={"slow": 0, "normal": 1, "fast": 2},
        safety="panel",
    ),
    "protect-notice": Feature(
        "00;90",
        "OLED panel-protect notice interval",
        choices={"auto": 0, "24-hours": 1},
        safety="panel",
    ),
    "static-screen-detection": Feature(
        "00;20", "OLED static-screen detection", choices=BOOLEAN, safety="panel"
    ),
    "multi-logo-detection": Feature(
        "00;50", "OLED multi-logo detection", choices=BOOLEAN, safety="panel"
    ),
    "taskbar-detection": Feature(
        "00;60", "OLED taskbar detection", choices=BOOLEAN, safety="panel"
    ),
    "boundary-detection": Feature(
        "00;70", "OLED boundary detection", choices=BOOLEAN, safety="panel"
    ),
    "transparency": Feature("00810", "OSD transparency", minimum=0, maximum=5),
    "osd-timeout": Feature(
        "00820",
        "OSD timeout in seconds",
        choices={str(value): value for value in (5, 10, 15, 20, 25, 30)},
        unit=" seconds",
    ),
}

STATUS_FEATURES = (
    "input",
    "model",
    "firmware-version",
    "uart-version",
    "kvm",
    "brightness",
    "contrast",
    "response-time",
    "color-temperature",
    "adaptive-sync",
    "hdr-active",
    "refresh-rate",
    "display-hdr",
    "pixel-shift",
    "multi-logo-detection",
    "taskbar-detection",
    "boundary-detection",
)

MPG341CX = MonitorProfile(
    slug="mpg341cx-oled",
    product_name="MSI MPG 341C QD-OLED",
    usb_vendor_id=0x1462,
    usb_product_id=0x3FA4,
    report_descriptor=bytes.fromhex(
        "05 01 09 00 a1 01 85 01 15 00 25 ff 19 01 29 08 95 3f 75 08 81 02 "
        "19 01 29 08 91 02 85 02 15 00 25 ff 19 01 29 08 95 3f 75 08 81 02 "
        "19 01 29 08 91 02 85 03 15 00 25 ff 19 01 29 08 95 3f 75 08 81 02 "
        "19 01 29 08 91 02 85 04 15 00 25 ff 19 01 29 08 95 3f 75 08 81 02 "
        "19 01 29 08 91 02 c0"
    ),
    model_id=117,
    uart_version=21,
    tested_firmware=(20,),
    ddc_manufacturer="MSI",
    ddc_model="MPG341CX OLED",
    hid_input_feature=HID_INPUT_FEATURE,
    features=FEATURES,
    status_features=STATUS_FEATURES,
)


def parse_feature_value(feature_name: str, raw_value: str) -> int:
    feature = FEATURES[feature_name]
    if feature.choices is not None:
        normalized = raw_value.lower()
        if normalized not in feature.choices:
            accepted = ", ".join(feature.choices)
            raise MonitorError(f"invalid {feature_name} value {raw_value!r}; choose: {accepted}")
        return feature.choices[normalized]
    try:
        value = int(raw_value, 10)
    except ValueError as error:
        raise MonitorError(f"invalid {feature_name} integer: {raw_value!r}") from error
    if feature.minimum is not None and value < feature.minimum:
        raise MonitorError(f"{feature_name} must be at least {feature.minimum}")
    if feature.maximum is not None and value > feature.maximum:
        raise MonitorError(f"{feature_name} must be at most {feature.maximum}")
    return value


def format_feature_value(feature_name: str, value: int) -> str:
    feature = FEATURES[feature_name]
    if feature.choices is not None:
        labels = {choice_value: label for label, choice_value in feature.choices.items()}
        label = labels.get(value)
        if label is None:
            return f"unknown ({value})"
        if feature.hexadecimal:
            return f"{label} (0x{value:02x})"
        return f"{label}{feature.unit} ({value})"
    return f"{value}{feature.unit}"


def accepted_values(feature: Feature) -> str:
    if not feature.writable:
        return "read-only"
    if feature.choices is not None:
        return "|".join(feature.choices)
    if feature.minimum is not None and feature.maximum is not None:
        return f"{feature.minimum}..{feature.maximum}"
    return "integer"
