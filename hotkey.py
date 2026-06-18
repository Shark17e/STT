import ctypes
import threading
from ctypes import wintypes

from pynput import keyboard
from pynput._util.win32 import SystemHook

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

_USER_MOD_VK = {
    0xA2: "ctrl", 0xA3: "ctrl",
    0xA4: "alt", 0xA5: "alt",
}

_F23_VK = 0x86
_WIN_VK = {0x5B, 0x5C}
_SHIFT_VK = {0xA0, 0xA1}

# --- SendInput structures ---
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_void_p),
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [('ki', KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', INPUT_UNION),
    ]

def _send_keydown(vk, scan=0, extended=False):
    dwFlags = 0x0001 if extended else 0
    ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=dwFlags, time=0, dwExtraInfo=0)
    inp = INPUT(type=1, u=INPUT_UNION(ki=ki))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


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

        lock = threading.RLock()
        state = 0  # 0=IDLE, 1=WIN_BLOCKED, 2=WIN_SHIFT_BLOCKED
        replay_timer = None
        timer_canceled = False

        def _cancel_timer():
            nonlocal replay_timer, timer_canceled
            timer_canceled = True
            if replay_timer is not None:
                replay_timer.cancel()
                replay_timer = None

        def _replay():
            nonlocal state
            if state == 1:
                _send_keydown(0x5B)
            elif state == 2:
                _send_keydown(0x5B)
                _send_keydown(0xA0)
            state = 0

        def _on_timer():
            with lock:
                if timer_canceled:
                    return
                _replay()

        def event_filter(msg, data):
            nonlocal pressed, state, replay_timer, timer_canceled

            vk = data.vkCode
            is_down = msg in (0x0100, 0x0104)
            is_up = msg in (0x0101, 0x0105)

            # Skip injected events (from our own SendInput replay)
            if data.flags & 0x10:
                return True

            with lock:
                if vk in _USER_MOD_VK:
                    mod = _USER_MOD_VK[vk]
                    if is_down:
                        pressed.add(mod)
                    else:
                        pressed.discard(mod)

                # --- Win key ---
                if vk in _WIN_VK:
                    if is_down:
                        timer_canceled = False
                        state = 1
                        replay_timer = threading.Timer(0.1, _on_timer)
                        replay_timer.start()
                        raise SystemHook.SuppressException()
                    else:
                        if state in (1, 2):
                            _cancel_timer()
                            _replay()
                        return True

                # --- Shift key ---
                if vk in _SHIFT_VK:
                    if is_down:
                        if state == 1:
                            state = 2
                            timer_canceled = False
                            replay_timer = threading.Timer(0.1, _on_timer)
                            replay_timer.start()
                            raise SystemHook.SuppressException()
                        return True
                    else:
                        if state == 2:
                            _cancel_timer()
                            _replay()
                        return True

                # --- F23 key ---
                if vk == _F23_VK:
                    if is_down:
                        if state == 2:
                            _cancel_timer()
                            state = 0
                            self._on_trigger()
                            raise SystemHook.SuppressException()
                        if pressed == expected_mods:
                            self._on_trigger()
                            raise SystemHook.SuppressException()
                    return True

                # --- Any other key ---
                if is_down and state in (1, 2):
                    _cancel_timer()
                    if state == 1:
                        _send_keydown(0x5B)
                    elif state == 2:
                        _send_keydown(0x5B)
                        _send_keydown(0xA0)
                    _send_keydown(vk, data.scanCode, bool(data.flags & 0x01))
                    state = 0
                    raise SystemHook.SuppressException()

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
