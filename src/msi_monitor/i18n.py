"""GUI translations (German / English / Spanish): labels, tooltips and UI strings."""

from __future__ import annotations

UI: dict[str, dict[str, str]] = {
    "de": {
        "tab.image": "Bild",
        "tab.mode": "Modus",
        "tab.gaming": "Gaming",
        "tab.screen": "Bildschirm",
        "tab.oled": "OLED-Schutz",
        "tab.input": "Eingang && USB",
        "tab.osd": "OSD && Tasten",
        "tab.info": "Info",
        "reload": "Neu laden",
        "language": "Sprache:",
        "lang.system": "Systemsprache",
        "loading": "Lese Monitor-Einstellungen …",
        "ready": "Bereit",
        "error": "Fehler: {msg}",
        "setting": "Setze {label} …",
        "confirm.title": "Bestätigen",
        "confirm.text": "{label} auf „{value}“ setzen?\n\n{warning}",
        "safety.disconnect": "Diese Einstellung kann Bild oder USB-Verbindung kurz unterbrechen.",
        "safety.panel": "Diese Einstellung ändert den OLED-Einbrennschutz.",
        "not_applied": "{label}: Monitor hat den Wert nicht übernommen "
        "(evtl. durch HDR oder einen Modus gesperrt)",
        "sent_unverified": "Gesendet – Verbindung danach unterbrochen",
        "unavailable": "nicht verfügbar",
        "unknown": "unbekannt ({value})",
    },
    "en": {
        "tab.image": "Image",
        "tab.mode": "Mode",
        "tab.gaming": "Gaming",
        "tab.screen": "Screen",
        "tab.oled": "OLED Care",
        "tab.input": "Input && USB",
        "tab.osd": "OSD && Keys",
        "tab.info": "Info",
        "reload": "Reload",
        "language": "Language:",
        "lang.system": "System language",
        "loading": "Reading monitor settings …",
        "ready": "Ready",
        "error": "Error: {msg}",
        "setting": "Setting {label} …",
        "confirm.title": "Confirm",
        "confirm.text": "Set {label} to “{value}”?\n\n{warning}",
        "safety.disconnect": "This setting can briefly interrupt video or the USB connection.",
        "safety.panel": "This setting changes the OLED burn-in protection.",
        "not_applied": "{label}: the monitor did not apply the value "
        "(possibly locked by HDR or the current mode)",
        "sent_unverified": "Sent – connection dropped afterwards",
        "unavailable": "not available",
        "unknown": "unknown ({value})",
    },
}

# feature -> (German label, English label)
LABELS: dict[str, tuple[str, str]] = {
    "brightness": ("Helligkeit", "Brightness"),
    "contrast": ("Kontrast", "Contrast"),
    "sharpness": ("Schärfe", "Sharpness"),
    "color-temperature": ("Farbtemperatur", "Color temperature"),
    "red": ("Rot", "Red"),
    "green": ("Grün", "Green"),
    "blue": ("Blau", "Blue"),
    "eye-care": ("Low Blue Light", "Low Blue Light"),
    "contrast-enhancer": ("Image Enhancement", "Image Enhancement"),
    "night-vision": ("Night Vision", "Night Vision"),
    "ai-vision": ("AI Vision", "AI Vision"),
    "display-hdr": ("DisplayHDR", "DisplayHDR"),
    "black-equalizer": ("Black Equalizer", "Black Equalizer"),
    "response-time": ("Reaktionszeit", "Response time"),
    "hdcr": ("HDCR", "HDCR"),
    "pro-mode": ("Pro Mode", "Pro Mode"),
    "gaming-mode": ("Game Mode", "Game Mode"),
    "smart-crosshair": ("Smart Crosshair", "Smart Crosshair"),
    "smart-crosshair-color": ("Crosshair-Farbe", "Crosshair color"),
    "optix-scope": ("Optix Scope", "Optix Scope"),
    "refresh-rate-display": ("Hz-Anzeige", "Refresh rate overlay"),
    "refresh-rate-position": ("Hz-Anzeige Position", "Refresh rate position"),
    "alarm-clock": ("Alarm Clock", "Alarm Clock"),
    "alarm-clock-position": ("Alarm Clock Position", "Alarm Clock position"),
    "adaptive-sync": ("Adaptive Sync", "Adaptive Sync"),
    "dsc": ("DSC", "DSC"),
    "screen-size": ("Seitenverhältnis", "Screen size"),
    "pip-pbp": ("PiP / PbP", "PiP / PbP"),
    "pip-size": ("PiP-Größe", "PiP size"),
    "pip-position": ("PiP-Position", "PiP position"),
    "pixel-shift": ("Pixel Shift", "Pixel Shift"),
    "protect-notice": ("Protect Notice", "Protect Notice"),
    "static-screen-detection": ("Standbild-Erkennung", "Static screen detection"),
    "multi-logo-detection": ("Logo-Erkennung", "Multi logo detection"),
    "taskbar-detection": ("Taskleisten-Erkennung", "Taskbar detection"),
    "boundary-detection": ("Rand-Erkennung", "Boundary detection"),
    "input": ("Eingang", "Input"),
    "kvm": ("KVM / USB", "KVM / USB"),
    "auto-scan": ("Eingangs-Autoscan", "Input auto scan"),
    "hdmi-cec": ("HDMI CEC", "HDMI CEC"),
    "hdmi-mode": ("HDMI-Modus", "HDMI mode"),
    "type-c-pd": ("Type-C PD Charge", "Type-C PD Charge"),
    "deep-sleep": ("DP Deep Sleep", "DP Deep Sleep"),
    "transparency": ("OSD-Transparenz", "OSD transparency"),
    "osd-timeout": ("OSD-Timeout", "OSD timeout"),
    "info-on-screen": ("Info On Screen", "Info On Screen"),
    "power-led": ("Power-LED", "Power LED"),
    "rgb-led": ("RGB LED", "RGB LED"),
    "power-button": ("Power Button", "Power Button"),
    "navi-up": ("Navi Key ↑", "Navi Key ↑"),
    "navi-down": ("Navi Key ↓", "Navi Key ↓"),
    "navi-left": ("Navi Key ←", "Navi Key ←"),
    "navi-right": ("Navi Key →", "Navi Key →"),
    "model": ("Modell", "Model"),
    "firmware-version": ("Firmware", "Firmware"),
    "uart-version": ("Protokoll", "Protocol"),
    "hdr-active": ("HDR aktiv", "HDR active"),
    "adaptive-sync-active": ("Adaptive Sync aktiv", "Adaptive Sync active"),
    "refresh-rate": ("Bildwiederholrate", "Refresh rate"),
}

# feature -> (German tooltip, English tooltip)
TIPS: dict[str, tuple[str, str]] = {
    "brightness": (
        "Helligkeit des Panels im SDR-Betrieb. Bei aktivem HDR gesperrt – "
        "dann regelt KDE die Helligkeit.",
        "Panel brightness in SDR. Locked while HDR is active – the desktop "
        "controls brightness then.",
    ),
    "contrast": ("Bildkontrast.", "Image contrast."),
    "sharpness": (
        "Nachschärfung durch den Monitor. 0 = keine (empfohlen für PC-Inhalte).",
        "Sharpening applied by the monitor. 0 = none (recommended for PC content).",
    ),
    "color-temperature": (
        "Farbstimmung: cool = bläulich, warm = gelblich, custom = eigene RGB-Werte. "
        "Bei HDR gesperrt.",
        "Color tone: cool = bluish, warm = yellowish, custom = your own RGB values. "
        "Locked in HDR.",
    ),
    "red": ("Rot-Anteil für Farbtemperatur „custom“.", "Red gain for the “custom” color temperature."),
    "green": ("Grün-Anteil für Farbtemperatur „custom“.", "Green gain for the “custom” color temperature."),
    "blue": ("Blau-Anteil für Farbtemperatur „custom“.", "Blue gain for the “custom” color temperature."),
    "eye-care": (
        "Reduziert Blaulicht, Bild wird wärmer/gelblicher. Schonender am Abend.",
        "Reduces blue light; the picture gets warmer. Easier on the eyes at night.",
    ),
    "contrast-enhancer": (
        "Verstärkt Kanten und Details per Bildverarbeitung. Kann Artefakte erzeugen.",
        "Boosts edges and detail through image processing. Can introduce artifacts.",
    ),
    "night-vision": (
        "Hellt dunkle Bildbereiche auf, um Gegner im Schatten besser zu sehen. "
        "„ai“ passt das automatisch an.",
        "Brightens dark areas so you can spot enemies in shadows. "
        "“ai” adjusts automatically.",
    ),
    "ai-vision": (
        "Automatische Bildoptimierung für Spiele (Helligkeit/Sättigung je nach Szene).",
        "Automatic picture optimization for games (brightness/saturation per scene).",
    ),
    "display-hdr": (
        "HDR-Modus des Monitors. True Black 400: tiefes Schwarz, max. ~450 nits, "
        "genau. Peak 1000: hellere kleine Highlights. EOTF Boost: hebt dunkle bis "
        "mittlere Töne an, wirkt heller, aber weniger genau.",
        "Monitor HDR mode. True Black 400: deep blacks, ~450 nits peak, accurate. "
        "Peak 1000: brighter small highlights. EOTF Boost: lifts dark and mid tones, "
        "looks brighter but less accurate.",
    ),
    "black-equalizer": (
        "Hellt nur sehr dunkle Bereiche auf.",
        "Brightens only very dark areas.",
    ),
    "response-time": ("Pixel-Overdrive.", "Pixel overdrive."),
    "hdcr": ("Dynamischer Kontrast.", "Dynamic contrast."),
    "pro-mode": (
        "Bild-Preset für Arbeit/Medien: User (eigene Werte), Anti-Blue, Movie, Office, "
        "sRGB/Adobe RGB/DCI-P3 (farbgenaue Farbräume), Eco (stromsparend).",
        "Picture preset for work/media: User (your values), Anti-Blue, Movie, Office, "
        "sRGB/Adobe RGB/DCI-P3 (accurate color spaces), Eco (power saving).",
    ),
    "gaming-mode": (
        "Bild-Preset für Spiele: FPS, Racing, RTS, RPG, Premium Color oder User.",
        "Picture preset for games: FPS, Racing, RTS, RPG, Premium Color or User.",
    ),
    "smart-crosshair": (
        "Blendet ein Fadenkreuz in der Bildschirmmitte ein (Icon 1–6). off = aus.",
        "Shows a crosshair in the center of the screen (icon 1–6). off = hidden.",
    ),
    "smart-crosshair-color": (
        "Farbe des Fadenkreuzes. auto wechselt je nach Hintergrund zwischen Weiß und Rot.",
        "Crosshair color. auto switches between white and red depending on the background.",
    ),
    "optix-scope": (
        "Lupe: vergrößert die Bildmitte, z. B. zum Zielen in Shootern.",
        "Magnifier: zooms into the center of the screen, e.g. for aiming in shooters.",
    ),
    "refresh-rate-display": (
        "Zeigt die aktuelle Bildwiederholrate (Hz) dauerhaft in einer Bildschirmecke.",
        "Permanently shows the current refresh rate (Hz) in a screen corner.",
    ),
    "refresh-rate-position": ("Ecke für die Hz-Anzeige.", "Corner for the refresh rate overlay."),
    "alarm-clock": (
        "Startet einen der 4 Timer und blendet ihn ein. Die Zeiten selbst werden "
        "im Monitormenü eingestellt.",
        "Starts one of the 4 timers and shows it on screen. The durations are set "
        "in the monitor menu.",
    ),
    "alarm-clock-position": ("Ecke für den Timer.", "Corner for the timer."),
    "adaptive-sync": (
        "Variable Bildwiederholrate (FreeSync/G-Sync compatible) gegen Tearing und Ruckeln.",
        "Variable refresh rate (FreeSync/G-Sync compatible) against tearing and stutter.",
    ),
    "dsc": (
        "Display Stream Compression: nötig für 4K bei 240 Hz über DisplayPort. "
        "Ausschalten kann die maximale Hz-Zahl senken.",
        "Display Stream Compression: required for 4K at 240 Hz over DisplayPort. "
        "Turning it off may lower the maximum refresh rate.",
    ),
    "screen-size": (
        "Seitenverhältnis-Emulation, z. B. 4:3 mit schwarzen Rändern. auto = native.",
        "Aspect ratio emulation, e.g. 4:3 with black bars. auto = native.",
    ),
    "pip-pbp": (
        "Zweites Bild: pip = kleines Fenster im Bild, pbp = zwei Bilder nebeneinander.",
        "Second picture: pip = small window inside, pbp = two pictures side by side.",
    ),
    "pip-size": ("Größe des PiP-Fensters.", "Size of the PiP window."),
    "pip-position": ("Ecke des PiP-Fensters.", "Corner of the PiP window."),
    "pixel-shift": (
        "Verschiebt das Bild minimal in Abständen, um Einbrennen zu verhindern. "
        "Schneller = mehr Schutz, eher sichtbar.",
        "Shifts the picture slightly at intervals to prevent burn-in. "
        "Faster = more protection, more noticeable.",
    ),
    "protect-notice": (
        "Wann der Monitor an den Panel-Protect-Wartungslauf erinnert.",
        "When the monitor reminds you to run the Panel Protect maintenance cycle.",
    ),
    "static-screen-detection": (
        "Dimmt das Bild, wenn sich lange nichts bewegt (Einbrennschutz).",
        "Dims the screen when nothing moves for a long time (burn-in protection).",
    ),
    "multi-logo-detection": (
        "Erkennt statische Logos (z. B. TV-Sender) und dimmt sie gezielt.",
        "Detects static logos (e.g. TV channels) and dims them locally.",
    ),
    "taskbar-detection": (
        "Erkennt eine statische Taskleiste und dimmt sie leicht.",
        "Detects a static taskbar and dims it slightly.",
    ),
    "boundary-detection": (
        "Erkennt schwarze Balken / Ränder und schützt die Kanten davor einzubrennen.",
        "Detects black bars / borders and protects the edges from burn-in.",
    ),
    "input": (
        "Aktiver Videoeingang. Beim Wechsel ist das Bild dieses PCs weg!",
        "Active video input. Switching away blanks this PC's picture!",
    ),
    "kvm": (
        "Welcher Eingang die USB-Geräte am Monitor (Tastatur/Maus) bekommt. "
        "auto folgt dem aktiven Videoeingang.",
        "Which input gets the USB devices on the monitor (keyboard/mouse). "
        "auto follows the active video input.",
    ),
    "auto-scan": (
        "Sucht automatisch einen Eingang mit Signal, wenn der aktive keins hat.",
        "Automatically looks for an input with a signal when the active one has none.",
    ),
    "hdmi-cec": (
        "Erlaubt Konsolen/Geräten per HDMI, den Monitor ein- und auszuschalten.",
        "Lets consoles/devices on HDMI turn the monitor on and off.",
    ),
    "hdmi-mode": ("HDMI 2.1-Modus für Konsole oder PC.", "HDMI 2.1 mode for console or PC."),
    "type-c-pd": (
        "Lädt Geräte am USB-C-Port auch, wenn der Monitor im Standby ist.",
        "Keeps charging devices on USB-C while the monitor is in standby.",
    ),
    "deep-sleep": ("Tiefer Standby über DisplayPort.", "DisplayPort deep sleep."),
    "transparency": ("Durchsichtigkeit des Monitormenüs (0 = deckend).", "Transparency of the monitor menu (0 = opaque)."),
    "osd-timeout": (
        "Nach wie vielen Sekunden sich das Monitormenü von selbst schließt.",
        "After how many seconds the monitor menu closes by itself.",
    ),
    "info-on-screen": (
        "Zeigt beim Wechsel von Eingang/Modus kurz Infos im Bild an.",
        "Briefly shows info on screen when the input or mode changes.",
    ),
    "power-led": ("Betriebs-LED an der Front.", "Power LED on the front."),
    "rgb-led": ("RGB-Beleuchtung (Mystic Light) am Monitor.", "RGB lighting (Mystic Light) on the monitor."),
    "power-button": (
        "Was die Ein/Aus-Taste macht: off = ganz ausschalten, standby = nur Standby.",
        "What the power button does: off = power off, standby = standby only.",
    ),
    "navi-up": (
        "Schnellfunktion, wenn der Joystick bei geschlossenem Menü nach oben gedrückt wird.",
        "Shortcut when the joystick is pushed up while the menu is closed.",
    ),
    "navi-down": (
        "Schnellfunktion für Joystick nach unten.",
        "Shortcut for joystick down.",
    ),
    "navi-left": (
        "Schnellfunktion für Joystick nach links.",
        "Shortcut for joystick left.",
    ),
    "navi-right": (
        "Schnellfunktion für Joystick nach rechts.",
        "Shortcut for joystick right.",
    ),
    "model": ("Interne MSI-Modellnummer.", "Internal MSI model number."),
    "firmware-version": ("Firmware-Version des Monitors.", "Monitor firmware version."),
    "uart-version": ("Version des Steuerprotokolls.", "Control protocol version."),
    "hdr-active": ("Ob gerade ein HDR-Signal anliegt.", "Whether an HDR signal is currently received."),
    "adaptive-sync-active": (
        "Ob variable Bildwiederholrate gerade aktiv ist.",
        "Whether variable refresh rate is currently active.",
    ),
    "refresh-rate": ("Aktuelle Bildwiederholrate.", "Current refresh rate."),
}


# --- Spanish -----------------------------------------------------------------

UI["es"] = {
    "tab.image": "Imagen",
    "tab.mode": "Modo",
    "tab.gaming": "Gaming",
    "tab.screen": "Pantalla",
    "tab.oled": "Cuidado OLED",
    "tab.input": "Entrada && USB",
    "tab.osd": "OSD && Botones",
    "tab.info": "Info",
    "reload": "Recargar",
    "language": "Idioma:",
    "lang.system": "Idioma del sistema",
    "loading": "Leyendo la configuración del monitor …",
    "ready": "Listo",
    "error": "Error: {msg}",
    "setting": "Ajustando {label} …",
    "confirm.title": "Confirmar",
    "confirm.text": "¿Cambiar {label} a «{value}»?\n\n{warning}",
    "safety.disconnect": "Este ajuste puede interrumpir brevemente la imagen o la conexión USB.",
    "safety.panel": "Este ajuste cambia la protección contra quemado del OLED.",
    "not_applied": "{label}: el monitor no aplicó el valor "
    "(posiblemente bloqueado por HDR o por el modo actual)",
    "sent_unverified": "Enviado – la conexión se interrumpió después",
    "unavailable": "no disponible",
    "unknown": "desconocido ({value})",
}

LABELS_ES: dict[str, str] = {
    "brightness": "Brillo", "contrast": "Contraste", "sharpness": "Nitidez",
    "color-temperature": "Temperatura de color", "red": "Rojo", "green": "Verde",
    "blue": "Azul", "eye-care": "Low Blue Light", "contrast-enhancer": "Image Enhancement",
    "night-vision": "Night Vision", "ai-vision": "AI Vision", "display-hdr": "DisplayHDR",
    "black-equalizer": "Black Equalizer", "response-time": "Tiempo de respuesta",
    "hdcr": "HDCR", "pro-mode": "Pro Mode", "gaming-mode": "Game Mode",
    "smart-crosshair": "Smart Crosshair", "smart-crosshair-color": "Color de la mira",
    "optix-scope": "Optix Scope", "refresh-rate-display": "Mostrar Hz",
    "refresh-rate-position": "Posición de Hz", "alarm-clock": "Alarm Clock",
    "alarm-clock-position": "Posición de Alarm Clock", "adaptive-sync": "Adaptive Sync",
    "dsc": "DSC", "screen-size": "Relación de aspecto", "pip-pbp": "PiP / PbP",
    "pip-size": "Tamaño PiP", "pip-position": "Posición PiP", "pixel-shift": "Pixel Shift",
    "protect-notice": "Protect Notice", "static-screen-detection": "Detección de imagen estática",
    "multi-logo-detection": "Detección de logotipos", "taskbar-detection": "Detección de barra de tareas",
    "boundary-detection": "Detección de bordes", "input": "Entrada", "kvm": "KVM / USB",
    "auto-scan": "Escaneo automático de entrada", "hdmi-cec": "HDMI CEC",
    "hdmi-mode": "Modo HDMI", "type-c-pd": "Type-C PD Charge", "deep-sleep": "DP Deep Sleep",
    "transparency": "Transparencia OSD", "osd-timeout": "Tiempo de espera OSD",
    "info-on-screen": "Info On Screen", "power-led": "LED de encendido", "rgb-led": "RGB LED",
    "power-button": "Power Button", "navi-up": "Navi Key ↑", "navi-down": "Navi Key ↓",
    "navi-left": "Navi Key ←", "navi-right": "Navi Key →", "model": "Modelo",
    "firmware-version": "Firmware", "uart-version": "Protocolo", "hdr-active": "HDR activo",
    "adaptive-sync-active": "Adaptive Sync activo", "refresh-rate": "Frecuencia de actualización",
}

TIPS_ES: dict[str, str] = {
    "brightness": "Brillo del panel en SDR. Bloqueado con HDR activo; entonces el "
    "escritorio controla el brillo.",
    "contrast": "Contraste de la imagen.",
    "sharpness": "Realce de nitidez del monitor. 0 = ninguno (recomendado para PC).",
    "color-temperature": "Tono de color: cool = azulado, warm = amarillento, custom = "
    "valores RGB propios. Bloqueado en HDR.",
    "red": "Ganancia de rojo para la temperatura «custom».",
    "green": "Ganancia de verde para la temperatura «custom».",
    "blue": "Ganancia de azul para la temperatura «custom».",
    "eye-care": "Reduce la luz azul; la imagen se vuelve más cálida. Más cómodo de noche.",
    "contrast-enhancer": "Realza bordes y detalles mediante procesamiento. Puede crear artefactos.",
    "night-vision": "Aclara las zonas oscuras para ver mejor a los enemigos en la sombra. "
    "«ai» lo ajusta automáticamente.",
    "ai-vision": "Optimización automática de imagen para juegos (brillo/saturación según la escena).",
    "display-hdr": "Modo HDR del monitor. True Black 400: negros profundos, ~450 nits, "
    "preciso. Peak 1000: picos pequeños más brillantes. EOTF Boost: eleva tonos oscuros "
    "y medios; más brillante pero menos preciso.",
    "black-equalizer": "Aclara solo las zonas muy oscuras.",
    "response-time": "Overdrive de píxeles.",
    "hdcr": "Contraste dinámico.",
    "pro-mode": "Preajuste para trabajo/multimedia: User (tus valores), Anti-Blue, Movie, "
    "Office, sRGB/Adobe RGB/DCI-P3 (espacios de color precisos), Eco (ahorro de energía).",
    "gaming-mode": "Preajuste para juegos: FPS, Racing, RTS, RPG, Premium Color o User.",
    "smart-crosshair": "Muestra una mira en el centro de la pantalla (icono 1–6). off = oculta.",
    "smart-crosshair-color": "Color de la mira. auto alterna entre blanco y rojo según el fondo.",
    "optix-scope": "Lupa: amplía el centro de la pantalla, p. ej. para apuntar en shooters.",
    "refresh-rate-display": "Muestra siempre la frecuencia actual (Hz) en una esquina.",
    "refresh-rate-position": "Esquina para el indicador de Hz.",
    "alarm-clock": "Inicia uno de los 4 temporizadores y lo muestra. Las duraciones se "
    "ajustan en el menú del monitor.",
    "alarm-clock-position": "Esquina para el temporizador.",
    "adaptive-sync": "Frecuencia variable (FreeSync/G-Sync compatible) contra tearing y tirones.",
    "dsc": "Display Stream Compression: necesario para 4K a 240 Hz por DisplayPort. "
    "Desactivarlo puede reducir la frecuencia máxima.",
    "screen-size": "Emulación de relación de aspecto, p. ej. 4:3 con barras negras. auto = nativa.",
    "pip-pbp": "Segunda imagen: pip = ventana pequeña dentro, pbp = dos imágenes lado a lado.",
    "pip-size": "Tamaño de la ventana PiP.",
    "pip-position": "Esquina de la ventana PiP.",
    "pixel-shift": "Desplaza la imagen ligeramente a intervalos para evitar el quemado. "
    "Más rápido = más protección, más visible.",
    "protect-notice": "Cuándo el monitor recuerda ejecutar el ciclo de mantenimiento Panel Protect.",
    "static-screen-detection": "Atenúa la pantalla si nada se mueve durante mucho tiempo "
    "(protección contra quemado).",
    "multi-logo-detection": "Detecta logotipos estáticos (p. ej. de canales de TV) y los atenúa.",
    "taskbar-detection": "Detecta una barra de tareas estática y la atenúa ligeramente.",
    "boundary-detection": "Detecta barras/bordes negros y protege los bordes del quemado.",
    "input": "Entrada de vídeo activa. ¡Al cambiar, este PC se queda sin imagen!",
    "kvm": "Qué entrada recibe los dispositivos USB del monitor (teclado/ratón). "
    "auto sigue la entrada de vídeo activa.",
    "auto-scan": "Busca automáticamente una entrada con señal si la activa no tiene.",
    "hdmi-cec": "Permite que consolas/dispositivos HDMI enciendan y apaguen el monitor.",
    "hdmi-mode": "Modo HDMI 2.1 para consola o PC.",
    "type-c-pd": "Sigue cargando dispositivos por USB-C con el monitor en reposo.",
    "deep-sleep": "Reposo profundo por DisplayPort.",
    "transparency": "Transparencia del menú del monitor (0 = opaco).",
    "osd-timeout": "Tras cuántos segundos se cierra solo el menú del monitor.",
    "info-on-screen": "Muestra brevemente información al cambiar de entrada o modo.",
    "power-led": "LED de encendido frontal.",
    "rgb-led": "Iluminación RGB (Mystic Light) del monitor.",
    "power-button": "Qué hace el botón de encendido: off = apagar, standby = solo reposo.",
    "navi-up": "Acceso directo al mover el joystick hacia arriba con el menú cerrado.",
    "navi-down": "Acceso directo para joystick hacia abajo.",
    "navi-left": "Acceso directo para joystick a la izquierda.",
    "navi-right": "Acceso directo para joystick a la derecha.",
    "model": "Número de modelo interno de MSI.",
    "firmware-version": "Versión del firmware del monitor.",
    "uart-version": "Versión del protocolo de control.",
    "hdr-active": "Si se está recibiendo una señal HDR.",
    "adaptive-sync-active": "Si la frecuencia variable está activa ahora.",
    "refresh-rate": "Frecuencia de actualización actual.",
}


LANGUAGES = ("de", "en", "es")
_PAIR_INDEX = {"de": 0, "en": 1}


def ui(lang: str, key: str, **kwargs: object) -> str:
    return UI.get(lang, UI["en"]).get(key, UI["en"][key]).format(**kwargs)


def label(lang: str, feature: str) -> str:
    if lang == "es" and feature in LABELS_ES:
        return LABELS_ES[feature]
    pair = LABELS.get(feature)
    return pair[_PAIR_INDEX.get(lang, 1)] if pair else feature


def tip(lang: str, feature: str) -> str:
    if lang == "es" and feature in TIPS_ES:
        return TIPS_ES[feature]
    pair = TIPS.get(feature)
    return pair[_PAIR_INDEX.get(lang, 1)] if pair else ""
