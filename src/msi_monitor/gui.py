"""Qt desktop GUI for msi-monitor.

All monitor I/O runs on one worker thread that owns the Controller, so the UI
never blocks and HID access stays serialized.
"""

from __future__ import annotations

import sys
import time

from PySide6.QtCore import QLocale, QObject, QSettings, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import i18n
from .cli import _detect_profile
from .controller import Controller
from .errors import DeviceUnavailable, MonitorError
from .profile import Feature, MonitorProfile, format_feature_value

TABS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "tab.image",
        (
            "brightness", "contrast", "sharpness", "color-temperature", "red", "green",
            "blue", "eye-care", "contrast-enhancer", "night-vision", "ai-vision",
            "display-hdr", "black-equalizer", "response-time", "hdcr",
        ),
    ),
    ("tab.mode", ("pro-mode", "gaming-mode")),
    (
        "tab.gaming",
        (
            "smart-crosshair", "smart-crosshair-color", "optix-scope",
            "refresh-rate-display", "refresh-rate-position", "alarm-clock",
            "alarm-clock-position", "adaptive-sync", "dsc",
        ),
    ),
    ("tab.screen", ("screen-size", "pip-pbp", "pip-size", "pip-position")),
    (
        "tab.oled",
        (
            "pixel-shift", "protect-notice", "static-screen-detection",
            "multi-logo-detection", "taskbar-detection", "boundary-detection",
        ),
    ),
    (
        "tab.input",
        ("input", "kvm", "auto-scan", "hdmi-cec", "hdmi-mode", "type-c-pd", "deep-sleep"),
    ),
    (
        "tab.osd",
        (
            "transparency", "osd-timeout", "info-on-screen", "power-led", "rgb-led",
            "power-button", "navi-up", "navi-down", "navi-left", "navi-right",
        ),
    ),
    (
        "tab.info",
        (
            "model", "firmware-version", "uart-version", "hdr-active",
            "adaptive-sync-active", "refresh-rate",
        ),
    ),
)

LANGUAGE_CHOICES = (("system", None), ("de", "Deutsch"), ("en", "English"), ("es", "Español"))


def system_language() -> str:
    code = QLocale.system().name()[:2]
    return code if code in i18n.LANGUAGES else "en"


class Worker(QObject):
    loaded = Signal(str, object)  # feature, int value | MonitorError
    load_finished = Signal()
    fatal = Signal(str)
    # feature, value | None, kind ("ok" | "not_applied" | "unverified" | "error"), detail
    changed = Signal(str, object, str, str)

    def __init__(self, profile: MonitorProfile):
        super().__init__()
        self.profile = profile
        self.controller: Controller | None = None

    def _ctrl(self) -> Controller:
        if self.controller is None:
            self.controller = Controller(profile=self.profile)
        return self.controller

    @Slot()
    def load_all(self) -> None:
        try:
            for name in self.profile.features:
                try:
                    self.loaded.emit(name, self._ctrl().read_feature(name))
                except DeviceUnavailable:
                    raise
                except MonitorError as error:
                    self.loaded.emit(name, error)
                time.sleep(0.04)
        except DeviceUnavailable as error:
            self.close()
            self.fatal.emit(str(error))
        self.load_finished.emit()

    @Slot(str, str, bool)
    def change(self, name: str, raw: str, allow: bool) -> None:
        try:
            result = self._ctrl().change_feature(name, raw, allow, allow)
        except MonitorError as error:
            message = str(error)
            kind = "not_applied" if "verification failed" in message else "error"
            try:
                value = self._ctrl().read_feature(name)
            except MonitorError:
                value = None
            self.changed.emit(name, value, kind, message)
            return
        if result.outcome == "sent-unverified":
            self.close()
            self.changed.emit(name, result.target, "unverified", "")
        else:
            value = result.verified if result.verified is not None else result.target
            self.changed.emit(name, value, "ok", "")

    @Slot()
    def close(self) -> None:
        if self.controller is not None:
            self.controller.close()
            self.controller = None


class FeatureRow(QWidget):
    """Editor for a single feature; emits `requested(choice_or_number)` on user change."""

    requested = Signal(str)

    def __init__(self, name: str, feature: Feature):
        super().__init__()
        self.name = name
        self.feature = feature
        self.value: int | None = None
        self.error: str | None = None
        self.lang = "en"
        self._updating = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo: QComboBox | None = None
        self.slider: QSlider | None = None
        self.spin: QSpinBox | None = None
        self.label: QLabel | None = None

        if not feature.writable:
            self.label = QLabel("…")
            self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(self.label)
        elif feature.choices is not None:
            self.combo = QComboBox()
            for choice, value in feature.choices.items():
                self.combo.addItem(choice, value)
            self.combo.activated.connect(self._combo_changed)
            layout.addWidget(self.combo)
        else:
            low = feature.minimum or 0
            high = feature.maximum if feature.maximum is not None else 999
            self.slider = QSlider(Qt.Horizontal)
            self.slider.setRange(low, high)
            self.spin = QSpinBox()
            self.spin.setRange(low, high)
            self.slider.valueChanged.connect(self.spin.setValue)
            self.spin.valueChanged.connect(self.slider.setValue)
            self._debounce = QTimer(self, singleShot=True, interval=350)
            self._debounce.timeout.connect(lambda: self.requested.emit(str(self.spin.value())))
            self.spin.valueChanged.connect(self._numeric_changed)
            layout.addWidget(self.slider, 1)
            layout.addWidget(self.spin)
        self.setEnabled(False)

    def _combo_changed(self, index: int) -> None:
        assert self.combo is not None
        if self.combo.itemData(index) != self.value:
            self.requested.emit(self.combo.itemText(index))

    def _numeric_changed(self, value: int) -> None:
        if not self._updating and value != self.value:
            self._debounce.start()

    def tooltip(self) -> str:
        text = i18n.tip(self.lang, self.name)
        if self.error:
            text = f"{text}\n\n{i18n.ui(self.lang, 'unavailable')}: {self.error}".strip()
        return text

    def retranslate(self, lang: str) -> None:
        self.lang = lang
        self.setToolTip(self.tooltip())
        if self.label is not None and self.error:
            self.label.setText(i18n.ui(lang, "unavailable"))

    def show_value(self, value: object) -> None:
        self._updating = True
        try:
            if isinstance(value, MonitorError):
                self.error = str(value)
                self.setEnabled(False)
                self.setToolTip(self.tooltip())
                if self.label is not None:
                    self.label.setText(i18n.ui(self.lang, "unavailable"))
                return
            if value is None:
                return
            self.error = None
            self.value = int(value)
            self.setToolTip(self.tooltip())
            self.setEnabled(True)
            if self.label is not None:
                self.label.setText(
                    format_feature_value(self.name, self.value, {self.name: self.feature})
                )
            elif self.combo is not None:
                index = self.combo.findData(self.value)
                if index < 0:
                    self.combo.addItem(i18n.ui(self.lang, "unknown", value=self.value), self.value)
                    index = self.combo.count() - 1
                self.combo.setCurrentIndex(index)
            elif self.spin is not None:
                self.spin.setValue(self.value)
        finally:
            self._updating = False


class MainWindow(QMainWindow):
    request_load = Signal()
    request_change = Signal(str, str, bool)
    request_close = Signal()

    def __init__(self, profile: MonitorProfile):
        super().__init__()
        self.profile = profile
        self._error = False
        self.settings = QSettings("msi-monitor", "msi-monitor-gui")
        self.language_setting = str(self.settings.value("language", "system"))
        if self.language_setting not in {code for code, _ in LANGUAGE_CHOICES}:
            self.language_setting = "system"
        self.lang = self._resolve(self.language_setting)

        self.setWindowTitle(profile.product_name)
        self.resize(600, 540)
        self.rows: dict[str, FeatureRow] = {}
        self.row_labels: dict[str, QLabel] = {}
        self.tab_keys: list[str] = []

        self.tabs = QTabWidget()
        for tab_key, names in TABS:
            present = [n for n in names if n in profile.features]
            if not present:
                continue
            page = QWidget()
            form = QFormLayout(page)
            form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            for name in present:
                row = FeatureRow(name, profile.features[name])
                row.requested.connect(lambda raw, n=name: self._on_request(n, raw))
                label = QLabel()
                label.setBuddy(row)
                self.rows[name] = row
                self.row_labels[name] = label
                form.addRow(label, row)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.tabs.addTab(scroll, "")
            self.tab_keys.append(tab_key)

        self.language_label = QLabel()
        self.language_combo = QComboBox()
        for code, name in LANGUAGE_CHOICES:
            self.language_combo.addItem(name or "", code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(self.language_setting))
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        self.refresh = QPushButton()
        self.refresh.clicked.connect(self._load)

        bottom = QHBoxLayout()
        bottom.addWidget(self.language_label)
        bottom.addWidget(self.language_combo)
        bottom.addStretch(1)
        bottom.addWidget(self.refresh)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.tabs)
        layout.addLayout(bottom)
        self.setCentralWidget(central)
        self._retranslate()

        self.thread = QThread(self)
        self.worker = Worker(profile)
        self.worker.moveToThread(self.thread)
        self.request_load.connect(self.worker.load_all)
        self.request_change.connect(self.worker.change)
        self.request_close.connect(self.worker.close)
        self.worker.loaded.connect(self._loaded)
        self.worker.load_finished.connect(self._load_finished)
        self.worker.fatal.connect(self._fatal)
        self.worker.changed.connect(self._changed)
        self.thread.start()
        self._load()

    @staticmethod
    def _resolve(setting: str) -> str:
        return system_language() if setting == "system" else setting

    def t(self, key: str, **kwargs: object) -> str:
        return i18n.ui(self.lang, key, **kwargs)

    def _retranslate(self) -> None:
        for index, key in enumerate(self.tab_keys):
            self.tabs.setTabText(index, self.t(key))
        for name, label in self.row_labels.items():
            label.setText(i18n.label(self.lang, name))
            label.setToolTip(i18n.tip(self.lang, name))
            self.rows[name].retranslate(self.lang)
        self.language_label.setText(self.t("language"))
        self.language_combo.setItemText(0, self.t("lang.system"))
        self.refresh.setText(self.t("reload"))

    def _language_changed(self, index: int) -> None:
        self.language_setting = self.language_combo.itemData(index)
        self.settings.setValue("language", self.language_setting)
        self.lang = self._resolve(self.language_setting)
        self._retranslate()

    def _load(self) -> None:
        self.refresh.setEnabled(False)
        self._error = False
        self.statusBar().showMessage(self.t("loading"))
        self.request_load.emit()

    def _loaded(self, name: str, value: object) -> None:
        if name in self.rows:
            self.rows[name].show_value(value)

    def _load_finished(self) -> None:
        self.refresh.setEnabled(True)
        if not self._error:
            self.statusBar().showMessage(self.t("ready"), 3000)

    def _fatal(self, message: str) -> None:
        self._error = True
        self.statusBar().showMessage(self.t("error", msg=message))

    def _on_request(self, name: str, raw: str) -> None:
        row = self.rows[name]
        safety = row.feature.safety
        if safety is not None:
            answer = QMessageBox.question(
                self,
                self.t("confirm.title"),
                self.t(
                    "confirm.text",
                    label=i18n.label(self.lang, name),
                    value=raw,
                    warning=self.t(f"safety.{safety}"),
                ),
            )
            if answer != QMessageBox.Yes:
                row.show_value(row.value)
                return
        row.setEnabled(False)
        self.statusBar().showMessage(self.t("setting", label=i18n.label(self.lang, name)))
        self.request_change.emit(name, raw, safety is not None)

    def _changed(self, name: str, value: object, kind: str, detail: str) -> None:
        row = self.rows[name]
        row.setEnabled(True)
        row.show_value(value)
        label = i18n.label(self.lang, name)
        if kind == "ok":
            message = f"{label}: {format_feature_value(name, value, self.profile.features)}"
        elif kind == "not_applied":
            message = self.t("not_applied", label=label)
        elif kind == "unverified":
            message = self.t("sent_unverified")
        else:
            message = self.t("error", msg=detail)
        self.statusBar().showMessage(message, 6000)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.request_close.emit()
        self.thread.quit()
        self.thread.wait(3000)
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MSI Monitor")
    app.setDesktopFileName("msi-monitor-gui")
    window = MainWindow(_detect_profile(None, None))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
