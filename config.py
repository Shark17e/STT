import json
import os

_DEFAULT_CONFIG = {
    "hotkey": {
        "modifiers": ["ctrl", "shift"],
        "key": "space",
    },
    "whisper": {
        "model_size": "small",
        "model_dir": "whisper-models",
        "device": "cpu",
        "compute_type": "int8",
    },
    "audio": {
        "sample_rate": 16000,
        "silence_threshold": 0.03,
        "silence_duration_sec": 1.5,
        "min_duration_sec": 0.5,
        "max_duration_sec": 30,
    },
}


def get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config(path=None):
    if path is None:
        path = get_config_path()

    config = _DEFAULT_CONFIG.copy()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        for section, values in user_config.items():
            if section in config and isinstance(config[section], dict) and isinstance(values, dict):
                config[section].update(values)
            else:
                config[section] = values

    return config


def save_config(config, path=None):
    if path is None:
        path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
