# Protocol notes

These notes describe the behavior verified on an MSI MPG 341C QD-OLED reporting HID model `117`, UART protocol `21`, and firmware `20`, and on an MSI MPG 322URX QD-OLED reporting HID model `126`, UART protocol `21`, and firmware `24`. The 322URX differences are listed in [MPG 322URX](#mpg-322urx).

## USB identity

- Vendor/product: `1462:3fa4`
- HID name: `MSI Gaming Controller` (341C), `MSI Monitor MPG 322URX QD-OLED` (322URX)
- HID report descriptor length: 95 bytes (341C), 150 bytes (322URX)
- Command report ID: `0x01`
- Linux `hidraw` report size: 64 bytes, including the report ID

The VID/PID is not unique to this monitor model. A compatible report descriptor is necessary but still insufficient: the read-only model and UART queries must also match before feature commands are used.

## HID framing

The first byte written through Linux `hidraw` is report ID `0x01`. The remaining 63 bytes contain an ASCII-oriented command padded with NUL bytes.

A feature key is five ASCII bytes. Verified exchanges have these forms:

```text
query:     58 <feature-key> CR
response:  5b <feature-key> <3-byte-value> CR
write:     5b <feature-key> <3-decimal-digit-value> CR
```

Numeric responses use three decimal ASCII digits. Two identity responses differ:

- Model: the final value byte is `0x30 + model_id` and can be non-ASCII.
- UART: the three-byte value is `VNN`, where `NN` is decimal.

A six-byte payload beginning with `56` and ending in carriage return is treated as an explicit monitor rejection. Reports with another report ID or size are ignored. A correctly framed but unexpected response is an error rather than a guessed value.

The authoritative feature keys, value domains, and risk classes are defined in `src/msi_monitor/profile.py`.

## KVM

The verified KVM feature key is `008>0`:

| Value | Meaning |
| ---: | --- |
| `0` | Auto |
| `1` | USB Type-B upstream |
| `2` | USB Type-C upstream |

A successful KVM write can immediately disconnect the HID controller. The CLI therefore reports exit code `2` when the command was sent but read-back became impossible.

## Input source

macOS uses the MSI HID key `00500`, verified against MSI Gaming Intelligence 0.1.4.7 and the connected model-117 monitor:

| Value | Input |
| ---: | --- |
| `0` | HDMI 1 |
| `1` | HDMI 2 |
| `2` | DisplayPort |
| `3` | USB Type-C |

Linux uses standard DDC/CI VCP feature `0x60`:

| Value | Input |
| ---: | --- |
| `0x0f` | DisplayPort |
| `0x10` | USB Type-C |
| `0x11` | HDMI 1 |
| `0x12` | HDMI 2 |

The asymmetric transport is intentional. macOS can safely switch away while it owns the Type-C USB controller; Linux retains DDC/CI so it can restore Type-C after USB KVM routing moves away.

## Transaction policy

The implementation:

1. Opens the selected Linux `hidraw` or macOS HIDAPI device and takes a non-blocking exclusive lock.
2. Drains stale input reports.
3. Sends one padded report.
4. For queries, waits up to two seconds for a matching response.
5. Reads the current value before writes and suppresses no-op writes.
6. Reads back changed values when the transport remains reachable.

There is no public raw-command interface. Unverified values, firmware operations, resets, and panel-maintenance activation are outside the supported protocol surface.

## MPG 322URX

The 322URX shares the VID/PID, report ID `0x01`, 64-byte framing, and UART protocol `21` with the 341C. Its report descriptor declares reports `0x01`, `0x02`, `0x04`, `0x05`, `0x11`, `0x30`, and `0x72` (the 341C declares `0x01`–`0x04`); only report `0x01` is used.

Keys that do not answer on firmware 24 and are therefore not exposed: `00210` (black equalizer), `00220` (response time), `00240` (HDCR), `008@0` (HDMI mode).

Additional keys, each verified by a write, read-back, and restore on the connected monitor. Current values were matched against the on-screen menu; the meaning of the remaining enum values follows the menu order and the [msigd](https://github.com/couriersud/msigd) catalog for related MSI models.

| Key | Feature | Values |
| --- | --- | --- |
| `00200` | Game mode | `0` user, `1` FPS, `2` racing, `3` RTS, `4` RPG, `5` premium color |
| `00300` | Pro mode | `0` user, `1` anti-blue, `2` movie, `3` office, `4` sRGB, `5` Adobe RGB, `6` DCI-P3, `7` eco |
| `004:0` | DisplayHDR | `0` True Black 400, `1` Peak 1000, `2` EOTF Boost |
| `00250` / `00251` | Refresh-rate overlay / corner | off/on; `0`–`3` left-top, right-top, left-bottom, right-bottom |
| `00260` / `00263` | Alarm clock timer / corner | `0` off, `1`–`4`; corner as above |
| `00270` / `00271` | Smart Crosshair icon / color | `0` off, `1`–`6`; `0` white, `1` red, `2` auto |
| `00630` / `00640` | PiP size / corner | small, medium, large; corner as above |
| `00830` | Info On Screen | off/on |
| `00860` | RGB LED | off/on |
| `00880` | Power button | `0` off, `1` standby (the 341C profile labels this key DP deep sleep) |
| `00900`–`00930` | Navi key up/down/left/right | `0` off, `1` brightness, `2` game mode, `3` Smart Crosshair, `4` alarm clock, `5` input, `6` PiP/PbP, `7` refresh rate, `8` info, `9` Night Vision, `10` Optix Scope, `11` KVM |

Changing `004:0` re-initializes the HID controller; the read-back after the write may time out once. The profile marks it as a disconnecting change.

The alarm clock duration (`00262`) is not exposed because values above `999` do not fit the three-digit write format.
