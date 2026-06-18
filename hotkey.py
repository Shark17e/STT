from pynput import keyboard

_SPECIAL_KEYS = {
    "space", "tab", "enter", "backspace", "delete", "home", "end",
    "page_up", "page_down", "left", "up", "right", "down",
    "insert", "menu", "esc", "pause", "print_screen",
    "caps_lock", "num_lock", "scroll_lock",
}
for i in range(1, 25):
    _SPECIAL_KEYS.add(f"f{i}")

_KEY_ALIASES = {
    "copilot": "f23",
}


def _build_hotkey_str(config):
    parts = [f"<{m}>" for m in config["hotkey"]["modifiers"]]
    key = _KEY_ALIASES.get(config["hotkey"]["key"], config["hotkey"]["key"])
    parts.append(f"<{key}>" if key in _SPECIAL_KEYS else key)
    return "+".join(parts)


class HotkeyListener:
    def __init__(self, config, on_trigger):
        self._config = config
        self._on_trigger = on_trigger
        self._listener = None
        self._hotkey_str = _build_hotkey_str(config)

    @property
    def hotkey_str(self):
        return self._hotkey_str

    def start(self):
        self._listener = keyboard.GlobalHotKeys({self._hotkey_str: self._on_trigger})
        self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()
