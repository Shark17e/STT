import json
import os
import tkinter as tk
from tkinter import ttk

_MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

_KEY_PRESETS = [
    "space", "enter", "tab", "esc",
    "v", "c", "a", "s", "d",
    "f1","f2","f3","f4","f5","f6","f7","f8","f9","f10",
    "f11","f12","f13","f14","f15","f16","f17","f18","f19","f20",
    "f21","f22","f23","f24",
    "copilot",
]


def _get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def open_settings(on_save):
    config_path = _get_config_path()

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    root = tk.Tk()
    root.title("Dictate-Win - Impostazioni")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.focus_force()
    root.lift()

    frame = ttk.Frame(root, padding=15)
    frame.pack()

    row = 0

    ttk.Label(frame, text="Modello", font=("", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 3)
    )
    row += 1

    model_var = tk.StringVar(value=config["whisper"]["model_size"])
    model_frame = ttk.Frame(frame)
    model_frame.grid(row=row, column=0, columnspan=2, sticky="we", pady=(0, 10))
    for i, size in enumerate(_MODEL_SIZES):
        ttk.Radiobutton(model_frame, text=size, variable=model_var, value=size).pack(
            side="left", padx=4
        )
    row += 1

    ttk.Separator(frame, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="we", pady=5
    )
    row += 1

    ttk.Label(frame, text="Tasto di scelta rapida", font=("", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 3)
    )
    row += 1

    mods = config["hotkey"]["modifiers"]
    mod_vars = {}
    mods_frame = ttk.Frame(frame)
    mods_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 3))
    for mod in ("ctrl", "shift", "alt", "win"):
        var = tk.BooleanVar(value=mod in mods)
        mod_vars[mod] = var
        ttk.Checkbutton(mods_frame, text=mod.upper(), variable=var).pack(
            side="left", padx=4
        )
    row += 1

    key_var = tk.StringVar(value=config["hotkey"]["key"])
    key_combo = ttk.Combobox(
        frame,
        textvariable=key_var,
        values=_KEY_PRESETS,
        state="readonly",
        width=14,
    )
    key_combo.grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1

    ttk.Label(
        frame,
        text=(
            "Nota: il tasto Copilot hardware invia Win+Shift+F23. "
            "Se usi 'copilot', win/shift sono impliciti."
        ),
        foreground="gray",
        font=("", 8),
        wraplength=320,
    ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(2, 10))
    row += 1

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))

    def save():
        config["whisper"]["model_size"] = model_var.get()
        config["hotkey"]["modifiers"] = sorted(
            m for m, v in mod_vars.items() if v.get()
        )
        config["hotkey"]["key"] = key_var.get()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        root.destroy()
        on_save(config)

    ttk.Button(btn_frame, text="Salva", command=save).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Annulla", command=root.destroy).pack(
        side="left", padx=5
    )

    root.mainloop()
