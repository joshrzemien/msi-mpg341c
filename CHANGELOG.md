# Changelog

## 0.2.1 — 2026-07-21

- Poll DDC input read-back for up to five seconds so delayed source changes verify reliably.

## 0.2.0 — 2026-07-21

- Add native macOS HID discovery and I/O through IOKit identity data and HIDAPI.
- Add guarded macOS DDC input control through BetterDisplay CLI integration.
- Add macOS device selectors, packaging metadata, tests, and CI coverage.
- Preserve exact report-descriptor, model, UART, ambiguity, and read-back safety checks on both platforms.

## 0.1.0 — 2026-07-20

- Add guarded control for 36 writable monitor settings.
- Add read-only status and telemetry for 44 total features.
- Add DDC/CI input selection that remains available when USB KVM routing moves away.
- Verify the HID report descriptor, MSI model ID, and UART version before HID operations.
- Add explicit disconnect and OLED-panel safety acknowledgements.
- Add serial, `hidraw`, and DDC-bus device selectors.
- Add versioned JSON output, udev active-seat access, and hardware-free protocol tests.
