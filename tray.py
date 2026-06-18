import pystray
from PIL import Image, ImageDraw

_MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]


def _make_image(hex_color):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    draw.ellipse([6, 6, size - 6, size - 6], fill=(*rgb, 255))
    return img


class TrayIcon:
    def __init__(self, config, on_exit, on_model_change, on_open_settings):
        self._config = config
        self._model = config["whisper"]["model_size"]
        self._on_exit = on_exit
        self._on_model_change = on_model_change
        self._on_open_settings = on_open_settings
        self._icon = self._build_icon()

    @staticmethod
    def _make_model_cb(callback, size):
        return lambda icon, item: callback(size)

    def _build_menu(self):
        model_items = []
        for size in _MODEL_SIZES:
            model_items.append(
                pystray.MenuItem(
                    size,
                    self._make_model_cb(self._on_model_change, size),
                    checked=lambda item, sz=size: self._model == sz,
                    radio=True,
                )
            )

        return pystray.Menu(
            pystray.MenuItem("Dictate-Win", lambda icon, item: None, enabled=False),
            pystray.MenuItem(f"Hotkey: {self._hotkey_display()}", lambda icon, item: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Modello", pystray.Menu(*model_items)),
            pystray.MenuItem("Apri impostazioni", lambda icon, item: self._on_open_settings()),
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

    def _hotkey_display(self):
        parts = [m.capitalize() for m in self._config["hotkey"]["modifiers"]]
        key = self._config["hotkey"]["key"]
        parts.append(key.capitalize() if len(key) > 1 else key.upper())
        return "+".join(parts)

    def update_model(self, model_size):
        self._model = model_size
        self._icon.menu = self._build_menu()

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
