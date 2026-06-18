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

# VK codes — Win+Shift sono parte dell'hardware Copilot, non vanno tracciati
_USER_MOD_VK = {
    0xA2: "ctrl", 0xA3: "ctrl",  # Ctrl
    0xA4: "alt", 0xA5: "alt",    # Alt
}

_F23_VK = 0x86


def _build_hotkey_str(config):
    parts = [f"<{m}>" for m in config["hotkey"]["modifiers"]]
    key = _KEY_ALIASES.get(config["hotkey"]["key"], config["hotkey"]["key"])
    parts.append(f"<{key}>" if key in _SPECIAL_KEYS else key)
    return "+".join(parts)


class HotkeyListener:
    def __init__(self, config, on_trigger):
        self._config = config
        self._on_trigger = on_trigger
        self._hotkey_str = _build_hotkey_str(config)
        self._listeners = []

    @property
    def hotkey_str(self):
        return self._hotkey_str

    def start(self):
        raw_key = _KEY_ALIASES.get(self._config["hotkey"]["key"], self._config["hotkey"]["key"])

        if raw_key == "f23":
            self._start_copilot_mode()
        else:
            ghk = keyboard.GlobalHotKeys({self._hotkey_str: self._on_trigger})
            ghk.start()
            self._listeners.append(ghk)

    def _start_copilot_mode(self):
        expected_mods = set(self._config["hotkey"]["modifiers"]) - {"win", "shift"}
        pressed = set()

        def event_filter(msg, data):
            nonlocal pressed
            vk = data.vkCode

            if vk in _USER_MOD_VK:
                mod = _USER_MOD_VK[vk]
                is_down = msg in (0x0100, 0x0104)
                if is_down:
                    pressed.add(mod)
                else:
                    pressed.discard(mod)

            if vk == _F23_VK and pressed == expected_mods:
                self._on_trigger()
                return False
            return True

        listener = keyboard.Listener(
            on_press=None,
            win32_event_filter=event_filter,
        )
        listener.start()
        self._listeners.append(listener)

    def stop(self):
        for listener in self._listeners:
            listener.stop()
