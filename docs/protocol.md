# Protocol notes

These notes describe the behavior verified on an MSI MPG 341C QD-OLED reporting HID model `117`, UART protocol `21`, and firmware `20`.

## USB identity

- Vendor/product: `1462:3fa4`
- HID name: `MSI Gaming Controller`
- HID report descriptor length: 95 bytes
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
