import pystray
from PIL import Image, ImageDraw

_MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

_KEY_OPTIONS = [
    "space", "enter", "tab", "esc",
    "v", "c", "a", "s",
    "f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11","f12",
    "copilot",
]

_MODIFIERS = ["ctrl", "shift", "alt", "win"]


def _make_image(hex_color):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    draw.ellipse([6, 6, size - 6, size - 6], fill=(*rgb, 255))
    return img


class TrayIcon:
    def __init__(self, config, on_exit, on_model_change, on_hotkey_change):
        self._config = config
        self._model = config["whisper"]["model_size"]
        self._on_exit = on_exit
        self._on_model_change = on_model_change
        self._on_hotkey_change = on_hotkey_change
        self._icon = self._build_icon()

    # --- helpers ---

    def _make_cb(self, callback, value):
        return lambda icon, item: callback(value)

    def _make_checked(self, expected):
        return lambda item: expected == self._model if isinstance(expected, str) else expected in self._config["hotkey"]["modifiers"]

    def _make_mod_cb(self, mod):
        return lambda icon, item: self._toggle_mod(mod)

    def _make_mod_checked(self, mod):
        return lambda item: mod in self._config["hotkey"]["modifiers"]

    def _make_key_cb(self, key):
        return lambda icon, item: self._set_key(key)

    def _make_key_checked(self, key):
        return lambda item: key == self._config["hotkey"]["key"]

    def _toggle_mod(self, mod):
        mods = self._config["hotkey"]["modifiers"]
        if mod in mods:
            mods.remove(mod)
        else:
            mods.append(mod)
        self._on_hotkey_change()
        self._icon.menu = self._build_menu()

    def _set_key(self, key):
        self._config["hotkey"]["key"] = key
        self._on_hotkey_change()
        self._icon.menu = self._build_menu()

    def _hotkey_display(self):
        parts = [m.capitalize() for m in self._config["hotkey"]["modifiers"]]
        key = self._config["hotkey"]["key"]
        parts.append(key.capitalize() if len(key) > 1 else key.upper())
        return "+".join(parts)

    # --- menu ---

    def _build_menu(self):
        model_items = [
            pystray.MenuItem(
                s,
                self._make_cb(self._on_model_change, s),
                checked=self._make_checked(s),
                radio=True,
            )
            for s in _MODEL_SIZES
        ]

        mod_items = [
            pystray.MenuItem(
                m.upper(),
                self._make_mod_cb(m),
                checked=self._make_mod_checked(m),
            )
            for m in _MODIFIERS
        ]

        key_items = [
            pystray.MenuItem(
                k,
                self._make_key_cb(k),
                checked=self._make_key_checked(k),
                radio=True,
            )
            for k in _KEY_OPTIONS
        ]

        return pystray.Menu(
            pystray.MenuItem("Dictate-Win", None, enabled=False),
            pystray.MenuItem(f"Hotkey: {self._hotkey_display()}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Modello", pystray.Menu(*model_items)),
            pystray.MenuItem("Modificatori", pystray.Menu(*mod_items)),
            pystray.MenuItem("Tasto", pystray.Menu(*key_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Esci", lambda icon: self._on_exit()),
        )

    def _build_icon(self):
        return pystray.Icon(
            "dictate-win",
            _make_image("#22c55e"),
            "Dictate-Win - In ascolto",
            self._build_menu(),
        )

    # --- public api ---

    def update_config(self, config):
        self._config = config
        self._model = config["whisper"]["model_size"]
        self._icon.menu = self._build_menu()

    def set_idle(self):
        self._icon.icon = _make_image("#22c55e")
        self._icon.title = "Dictate-Win - In ascolto"

    def set_recording(self):
        self._icon.icon = _make_image("#ef4444")
        self._icon.title = "Dictate-Win - Registrazione..."

    def set_processing(self):
        self._icon.icon = _make_image("#f59e0b")
        self._icon.title = "Dictate-Win - Trascrizione in corso..."

    def set_error(self, msg=""):
        self._icon.icon = _make_image("#ef4444")
        self._icon.title = f"Dictate-Win - Errore{': ' + msg if msg else ''}"

    def run(self):
        self._icon.run()

    def stop(self):
        self._icon.stop()
