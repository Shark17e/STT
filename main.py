import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

if sys.platform == "win32":
    import ctypes
    ctypes.windll.user32.ShowWindow(
        ctypes.windll.kernel32.GetConsoleWindow(), 0
    )

from config import load_config, save_config, get_config_path
from hotkey import HotkeyListener
from paster import paste_text
from paths import get_base_dir, models_dir
from recorder import Recorder
from transcriber import Transcriber
from tray import TrayIcon


MODEL_NAMES = ["tiny", "base", "small", "medium", "large-v3"]
SIZES_LABEL = {
    "tiny": "~150 MB",
    "base": "~300 MB",
    "small": "~500 MB",
    "medium": "~1.5 GB",
    "large-v3": "~3 GB",
}


def _model_path(config, model_size=None):
    size = model_size or config["whisper"]["model_size"]
    d = config["whisper"]["model_dir"]
    base = os.path.join(get_base_dir(), d) if not os.path.isabs(d) else d
    return os.path.join(base, size)


def _model_is_available(config, model_size=None):
    return os.path.isfile(os.path.join(_model_path(config, model_size), "model.bin"))


def _find_models_in_folder(folder):
    found = []
    for name in MODEL_NAMES:
        if os.path.isfile(os.path.join(folder, name, "model.bin")):
            found.append(name)
    return found


def _ensure_model(config):
    if _model_is_available(config):
        return True

    ret = ctypes.windll.user32.MessageBoxW(
        0,
        "Nessun modello Whisper trovato.\n\n"
        "Hai già una cartella con i modelli?\n"
        "Seleziona Sì per scegliere la cartella,\n"
        "No per scaricarli ora.",
        "TTS - Modelli mancanti",
        4 | 32,
    )

    if ret == 6:
        folder = filedialog.askdirectory(title="Seleziona cartella whisper-models")
        if folder:
            found = _find_models_in_folder(folder)
            if found:
                config["whisper"]["model_dir"] = folder
                save_config(config, get_config_path())
                if config["whisper"]["model_size"] not in found:
                    config["whisper"]["model_size"] = found[0]
                    save_config(config, get_config_path())
                return True
            else:
                ctypes.windll.user32.MessageBoxW(
                    0, "Nella cartella selezionata non ci sono modelli validi.",
                    "TTS", 16
                )

    return _download_dialog(config)


def _download_dialog(config):
    root = tk.Tk()
    root.title("TTS - Scarica modelli")
    root.geometry("480x460")
    root.resizable(False, False)
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    cancel_event = threading.Event()
    result = {"success": False, "downloaded": []}

    tk.Label(root, text="Seleziona i modelli da scaricare:", font=("", 10, "bold")).pack(pady=(10, 0))

    vars = {}
    frame = tk.Frame(root)
    frame.pack(pady=5)
    for name in MODEL_NAMES:
        v = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(frame, text=f"{name:8s}  {SIZES_LABEL[name]:>8s}", variable=v, anchor="w")
        cb.pack(fill=tk.X, padx=20, pady=1)
        vars[name] = v

    tk.Label(root, text="I modelli verranno salvati nella cartella 'whisper-models/'", fg="gray", font=("", 8)).pack()

    bar = ttk.Progressbar(root, mode="determinate", value=0)
    status_label = tk.Label(root, text="", fg="gray")
    file_label = tk.Label(root, text="", fg="gray")

    def _cleanup():
        bar["value"] = 0
        file_label.config(text="")
        status_label.config(text="")

    _last_prog = [0.0]
    def _show_progress(current, total):
        now = time.time()
        if now - _last_prog[0] < 0.15:
            return
        _last_prog[0] = now
        root.after(0, lambda c=current, t=total: _update_progress(c, t))

    def _update_progress(current, total):
        if total > 0:
            pct = min(int(current / total * 100), 100)
            file_label.config(text=f"{current//1024**2}/{total//1024**2} MB")
            bar["value"] = pct

    def _show_completed():
        bar["value"] = 100
        file_label.config(text="")
        status_label.config(text="Download completato!")
        start_btn.destroy()
        cancel_btn.destroy()
        tk.Button(root, text="Continua", command=root.destroy, width=20).pack(pady=10)

    def _download_task():
        from download_models import download_model, DownloadCancelled

        selected = [name for name, v in vars.items() if v.get()]
        if not selected:
            return

        d = config["whisper"]["model_dir"]
        base_dir = os.path.join(get_base_dir(), d) if not os.path.isabs(d) else d
        total_selected = len(selected)

        for i, name in enumerate(selected):
            if cancel_event.is_set():
                return

            root.after(0, lambda n=name, idx=i, t=total_selected: (
                status_label.config(text=f"Download {n} ({idx+1}/{t})..."),
                bar.configure(value=0),
                file_label.config(text=""),
            ))

            try:
                download_model(name, base_dir, on_progress=_show_progress, cancel=cancel_event)
                result["downloaded"].append(name)
            except DownloadCancelled:
                return
            except Exception as e:
                root.after(0, lambda: _err(e))
                return

        result["success"] = True
        root.after(0, _show_completed)

    def _err(e):
        bar["value"] = 0
        status_label.config(text=f"❌ Errore: {e}", fg="red")
        file_label.config(text="")

    def _start():
        selected = [name for name, v in vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Nessun modello", "Seleziona almeno un modello da scaricare.", parent=root)
            return
        start_btn.config(state=tk.DISABLED)
        for cb_w in frame.winfo_children():
            cb_w.config(state=tk.DISABLED)
        _cleanup()
        threading.Thread(target=_download_task, daemon=True).start()

    def _on_close():
        if start_btn.cget("state") == tk.DISABLED:
            cancel_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)

    start_btn = tk.Button(root, text="Scarica selezionati", command=_start, width=20)
    start_btn.pack(pady=5)

    file_label.pack()
    bar.pack(fill=tk.X, padx=20, pady=5)
    status_label.pack()

    cancel_btn = tk.Button(root, text="Annulla", command=_on_close)
    cancel_btn.pack(pady=5)

    root.mainloop()

    if not result["success"] or not result["downloaded"]:
        return False

    _pick_active_model(config, result["downloaded"])
    return _model_is_available(config)


def _pick_active_model(config, downloaded):
    if len(downloaded) == 1:
        config["whisper"]["model_size"] = downloaded[0]
        save_config(config, get_config_path())
        return

    win = tk.Tk()
    win.title("TTS - Modello attivo")
    win.geometry("300x220")
    win.resizable(False, False)
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
    y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    tk.Label(win, text="Quale modello vuoi usare?", font=("", 10, "bold")).pack(pady=10)
    v = tk.StringVar(value=downloaded[0])
    for name in downloaded:
        tk.Radiobutton(win, text=f"{name}  ({SIZES_LABEL[name]})", variable=v, value=name).pack(anchor="w", padx=20)

    def _ok():
        config["whisper"]["model_size"] = v.get()
        save_config(config, get_config_path())
        win.destroy()

    tk.Button(win, text="OK", command=_ok).pack(pady=10)
    win.wait_window()


def main():
    config_path = get_config_path()

    try:
        config = load_config(config_path)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(
            0, f"Errore caricamento config.json:\n{e}", "TTS - Errore", 16
        )
        sys.exit(1)

    if not _ensure_model(config):
        sys.exit(0)

    _lock = threading.Lock()

    try:
        recorder = Recorder(config)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(
            0, f"Microfono non disponibile:\n{e}", "TTS - Errore", 16
        )
        recorder = None

    try:
        transcriber = Transcriber(config)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(
            0, f"Errore caricamento modello:\n{e}", "TTS - Errore", 16
        )
        transcriber = None

    _exit_requested = threading.Event()

    def _on_hotkey():
        if recorder is None:
            tray.set_error("Microfono non disponibile")
            return
        if transcriber is None:
            tray.set_error("Modello non caricato")
            return
        if recorder.is_recording:
            recorder.stop()
            return
        if not _lock.acquire(blocking=False):
            return
        threading.Thread(target=_work_wrapper, daemon=True).start()

    def _on_model_change(new_model):
        nonlocal config
        config["whisper"]["model_size"] = new_model
        save_config(config, config_path)
        tray.update_config(config)
        if transcriber is not None:
            transcriber.reload(new_model)

    def _on_hotkey_change():
        nonlocal config, hotkey
        save_config(config, config_path)
        new = HotkeyListener(config, _on_hotkey)
        try:
            new.start()
        except Exception as e:
            print(f"Errore nuovo hotkey: {e}", file=sys.stderr)
            new.stop()
        else:
            old = hotkey
            hotkey = new
            old.stop()
            tray.update_config(config)

    def _work():
        try:
            tray.set_recording()
            audio = recorder.record()
            if audio is not None:
                tray.set_processing()
                text = transcriber.transcribe(audio)
                if text:
                    paste_text(text)
            tray.set_idle()
        except Exception as e:
            print(f"Errore: {e}", file=sys.stderr)
            tray.set_error(str(e)[:60])

    def _work_wrapper():
        try:
            _work()
        finally:
            _lock.release()

    def _on_exit():
        _exit_requested.set()
        tray.stop()

    hotkey = HotkeyListener(config, _on_hotkey)
    try:
        hotkey.start()
    except Exception as e:
        print(f"Errore registrazione hotkey: {e}", file=sys.stderr)
        hotkey = None

    tray = TrayIcon(
        config=config,
        on_exit=_on_exit,
        on_model_change=_on_model_change,
        on_hotkey_change=_on_hotkey_change,
    )
    tray.set_idle()
    tray.run()

    if hotkey is not None:
        hotkey.stop()


if __name__ == "__main__":
    main()
