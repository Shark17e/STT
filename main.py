import sys
import threading

from config import load_config, save_config, get_config_path
from hotkey import HotkeyListener
from paster import paste_text
from recorder import Recorder
from settings import open_settings
from transcriber import Transcriber
from tray import TrayIcon


def main():
    config_path = get_config_path()

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Errore caricamento config.json: {e}", file=sys.stderr)
        sys.exit(1)

    _lock = threading.Lock()

    try:
        recorder = Recorder(config)
    except Exception as e:
        print(f"Errore inizializzazione microfono: {e}", file=sys.stderr)
        recorder = None

    try:
        transcriber = Transcriber(config)
    except Exception as e:
        print(f"Errore caricamento modello: {e}", file=sys.stderr)
        transcriber = None

    # --- callbacks ---

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
        tray.update_model(new_model)
        if transcriber is not None:
            transcriber.reload(new_model)

    def _on_open_settings():
        def after_save(new_config):
            nonlocal config, hotkey
            old_model = config["whisper"]["model_size"]
            old_hotkey_key = config["hotkey"]["key"]
            old_hotkey_mods = list(config["hotkey"]["modifiers"])
            config = new_config

            if (
                config["hotkey"]["key"] != old_hotkey_key
                or config["hotkey"]["modifiers"] != old_hotkey_mods
            ):
                new_hotkey = HotkeyListener(config, _on_hotkey)
                try:
                    new_hotkey.start()
                except Exception as e:
                    print(f"Errore registrazione nuovo hotkey: {e}", file=sys.stderr)
                else:
                    old_hotkey = hotkey
                    hotkey = new_hotkey
                    old_hotkey.stop()

            tray.update_config(config)

            if config["whisper"]["model_size"] != old_model:
                if transcriber is not None:
                    transcriber.reload(config["whisper"]["model_size"])

            print(f"Hotkey aggiornato: {hotkey.hotkey_str}")

        open_settings(after_save)

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

    # --- init ---

    hotkey = HotkeyListener(config, _on_hotkey)
    try:
        hotkey.start()
    except Exception as e:
        print(f"Errore registrazione hotkey: {e}", file=sys.stderr)
        hotkey = None

    tray = TrayIcon(
        config=config,
        on_exit=lambda: tray.stop(),
        on_model_change=_on_model_change,
        on_open_settings=_on_open_settings,
    )
    tray.set_idle()
    print(f"Dictate-Win avviato. Hotkey: {hotkey.hotkey_str}")
    tray.run()

    if hotkey is not None:
        hotkey.stop()


if __name__ == "__main__":
    main()
