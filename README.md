# msi-mpg341c

Linux and macOS control for the **MSI MPG 341C QD-OLED** monitor. It exposes monitor settings, input selection, and USB KVM routing through a guarded command-line interface.

This is an independent interoperability project and is not affiliated with or endorsed by MSI.

## Supported hardware

| Product | USB controller | HID model | UART | Tested firmware |
| --- | --- | ---: | ---: | ---: |
| MSI MPG 341C QD-OLED (`MPG341CX OLED` in EDID) | `1462:3fa4` | `117` | `21` | `20` |

Only this exact profile has been hardware-tested. The USB VID/PID is shared by other MSI monitors, so the program also verifies the HID report descriptor, model identifier, and UART protocol version before using HID feature commands.

## Safety model

- Values are restricted to verified ranges and enum choices.
- Read-only telemetry cannot be written.
- Video- or USB-routing changes require `--allow-disconnect`.
- OLED-protection changes require `--allow-panel-risk`.
- Writes are read back when the monitor remains reachable.
- Unchanged values do not generate a write.
- Arbitrary raw HID commands, firmware updates, resets, and panel-maintenance activation are not exposed.

The tool directly controls physical hardware. Keep the monitor's OSD controls available when testing input or KVM changes.

## Requirements

- Python 3.11 or newer
- The monitor's USB upstream connection for HID settings and KVM control
- Linux: [`ddcutil`](https://www.ddcutil.com/) for video-input reads and writes
- macOS: [BetterDisplay](https://betterdisplay.pro/) running with CLI integration enabled for video-input reads and writes

The DDC input path remains available when a KVM switch moves the monitor's USB controller to the other computer.

## Installation

### macOS

```bash
brew install --cask betterdisplay
git clone https://github.com/joshrzemien/msi-mpg341c.git
cd msi-mpg341c
uv tool install .
open -a BetterDisplay
```

BetterDisplay's CLI integration is enabled by default. The Python package installs the native `hidapi` dependency on macOS; no kernel extension or elevated USB permissions are required.

### Arch Linux / AUR

```bash
paru -S msi-mpg341c
```

The package installs the Python application, `ddcutil`, and the udev access rule.

### Linux from source

```bash
git clone https://github.com/joshrzemien/msi-mpg341c.git
cd msi-mpg341c
uv tool install .
sudo install -Dm644 contrib/udev/71-msi-monitor.rules \
  /etc/udev/rules.d/71-msi-monitor.rules
sudo udevadm control --reload
sudo udevadm trigger --subsystem-match=hidraw
```

Reconnect the monitor's USB upstream cable after installing the rule. Do not run `msi-monitor` with `sudo`.

A Python package installer cannot install system udev rules; install the rule separately as shown above.

## Usage

With no arguments, `msi-monitor` displays the status summary:

```bash
msi-monitor
msi-monitor status
msi-monitor list
msi-monitor get brightness
msi-monitor get all
msi-monitor set brightness 50
```

Potentially disconnecting operations require acknowledgement:

```bash
msi-monitor set input type-c --allow-disconnect
msi-monitor set input hdmi-1 --allow-disconnect
msi-monitor set kvm type-c --allow-disconnect
msi-monitor set kvm auto --allow-disconnect
```

OLED-care changes use a separate acknowledgement:

```bash
msi-monitor set pixel-shift normal --allow-panel-risk
```

If an input change removes the picture, restore HDMI 1 over DDC/CI:

```bash
msi-monitor set input hdmi-1 --allow-disconnect
```

### Multiple monitors

Automatic selection refuses ambiguous supported HID controllers or DDC displays. Select one explicitly with a global option placed before the command:

```bash
# Linux
msi-monitor --device /dev/hidraw4 get brightness
msi-monitor --ddc-bus 3 get input

# Linux or macOS
msi-monitor --serial A02019010700 get brightness

# macOS; obtain the UUID with: betterdisplaycli get --identifiers
msi-monitor --ddc-display 29E93D45-E1B5-44D1-A989-67F184915919 get input
```

`--device` and `--serial` never bypass descriptor or profile verification. `--ddc-bus` selects a Linux I2C bus; `--ddc-display` selects a BetterDisplay UUID on macOS.

### JSON output

Use `--json` before the command for a versioned machine-readable contract:

```bash
msi-monitor --json status
msi-monitor --json get all
msi-monitor --json list
```

Errors are written to stderr. Exit code `2` means a command was sent but could not be verified, or a multi-feature read was incomplete; this commonly occurs when a KVM write intentionally routes USB away.

## Architecture

- `cli.py`: argument parsing and human/JSON output
- `controller.py`: feature operations, safety policy, and read-back verification
- `profile.py`: verified device identity and feature catalog
- `protocol.py`: pure HID frame construction and response decoding
- `hid.py`: platform transport dispatch
- `hidraw.py`: Linux discovery, locking, and HID I/O
- `hidmac.py`: macOS IOKit identity verification and HIDAPI I/O
- `ddc.py`: constrained `ddcutil` or BetterDisplay CLI invocation for input control

The Linux implementation uses a short-lived process and active-seat udev access. The macOS HID path is also short-lived; input control uses the running BetterDisplay app's CLI integration.

## Development

```bash
uv sync --extra test
uv run pytest
uv build
```

Tests use captured protocol shapes and test doubles; they do not write to monitor hardware. New device profiles must include read-only identity evidence and hardware validation for every exposed write. Shared VID/PID values are not sufficient evidence of compatibility.

Protocol notes are in [`docs/protocol.md`](docs/protocol.md).

## License

Licensed under the GNU General Public License, version 3 or later. See [`LICENSE`](LICENSE).
