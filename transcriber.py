import os
import threading

from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, config):
        self._config = config
        self._model = None
        self._ready = False
        self._error = None
        self._load_thread = threading.Thread(target=self._load, daemon=True)
        self._load_thread.start()

    def _get_model_path(self):
        model_size = self._config["whisper"]["model_size"]
        model_dir = self._config["whisper"]["model_dir"]
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_dir)
        local = os.path.join(base, model_size)
        if os.path.isdir(local):
            return local
        return None

    def _load(self):
        try:
            model_path = self._get_model_path()
            if model_path is None:
                self._error = (
                    f"Modello non trovato. Scarica il modello e mettilo in "
                    f"'{os.path.join(self._config['whisper']['model_dir'], self._config['whisper']['model_size'])}'"
                )
                return

            self._model = WhisperModel(
                model_path,
                device=self._config["whisper"]["device"],
                compute_type=self._config["whisper"]["compute_type"],
            )
            self._ready = True
        except Exception as e:
            self._error = str(e)

    def wait_ready(self, timeout=60):
        self._load_thread.join(timeout=timeout)
        if not self._ready:
            raise RuntimeError(self._error or "Modello non caricato")

    @property
    def is_ready(self):
        return self._ready

    @property
    def error(self):
        return self._error

    def transcribe(self, audio):
        if not self._ready:
            self.wait_ready()

        segments, _ = self._model.transcribe(audio, language="it", beam_size=5)
        text = " ".join(segment.text for segment in segments)
        return text.strip()

    def reload(self, model_size):
        self._config["whisper"]["model_size"] = model_size
        self._model = None
        self._ready = False
        self._error = None
        self._load_thread = threading.Thread(target=self._load, daemon=True)
        self._load_thread.start()
