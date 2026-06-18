# STT - Dettatura Vocale Offline

Trascrivi la voce in testo con Whisper (offline, 100% locale) e incolla il risultato nella finestra attiva. Funziona interamente in system tray, senza finestre visibili.

## Funzionamento

1. Premi l'hotkey (default: **Win+Shift+F23** = tasto Copilot)
2. Parla al microfono
3. Smetti di parlare (o ripremi l'hotkey) — dopo 1.5s di silenzio si ferma
4. Il testo viene trascritto e incollato automaticamente

## Download rapido

Scarica l'ultima release da [GitHub Releases](https://github.com/Shark17e/TTS/releases):

1. **TTS-vX.X.X.zip** — contiene l'exe già compilato. Estrai in una cartella e avvia `TTS.exe`.
2. Scarica i modelli Whisper (vedi sotto) nella cartella `whisper-models/` accanto all'exe.

## Modelli

Il programma richiede un modello Whisper nella cartella `whisper-models/`.  
Se il modello non è presente all'avvio, appare una finestra che chiede se scaricarlo automaticamente (richiede internet).

| Modello | Spazio | RAM | Precisione |
|---------|--------|-----|------------|
| tiny    | ~150 MB  | ~1 GB  | Base |
| base    | ~300 MB  | ~1.5 GB | Discreta |
| small   | ~500 MB  | ~2 GB  | Buona |
| medium  | ~1.5 GB  | ~3 GB  | Molto buona |
| large-v3| ~3 GB   | ~5 GB  | Massima |

**Consigliato:** `small` per uso generico, `medium` se hai RAM sufficiente.

Per scaricare i modelli manualmente:

```powershell
# Tutti i modelli
python download_models.py

# Un modello specifico
python download_models.py medium
python download_models.py small
```

Cambia il modello attivo dal menu tray (click destro sull'icona → _Modello_) o modificando `config.json`.

## Installazione

### Da release (consigliato)

1. Scarica `TTS-vX.X.X.zip` dalla sezione [Releases](https://github.com/Shark17e/TTS/releases)
2. Estrai in una cartella (es. `C:\Programmi\TTS\`)
3. Avvia `TTS.exe` — appare l'icona nella system tray
4. Se il modello non è presente, il programma ti chiederà se scaricarlo
5. Premi il tasto **Copilot** (o l'hotkey configurato) per dettare

### Build da sorgente

```powershell
# Clona la repo
git clone https://github.com/Shark17e/TTS.git
cd TTS

# Installa dipendenze
pip install -r requirements.txt

# Avvia direttamente (mostra console per debug)
python main.py

# Build con PyInstaller (exe singolo)
pip install pyinstaller
pyinstaller --noconsole --onefile --name TTS --icon ThaSkull.ico ^
    --hidden-import faster_whisper --hidden-import ctranslate2 ^
    --hidden-import tokenizers --hidden-import sounddevice ^
    --hidden-import soundfile --hidden-import PIL._tkinter_finder ^
    --hidden-import pyautogui._pyautogui_win --hidden-import pyperclip ^
    --hidden-import pystray --hidden-import _cffi_backend ^
    --hidden-import tkinter ^
    --collect-all faster_whisper --collect-all ctranslate2 ^
    --collect-all tokenizers --collect-all sounddevice main.py

# L'exe singolo si trova in dist/TTS.exe
```

> La prima build richiede 3-5 minuti. L'exe generato (~200 MB) contiene tutte le librerie incluse.

## Requisiti

- **Windows 11** (testato su 23H2+; Windows 10 non testato ma dovrebbe funzionare)
- **Microfono** funzionante
- **CPU** con supporto AVX (qualsiasi Intel/AMD dal 2010+)
- **RAM:** 2-6 GB in base al modello
- **Python 3.9+** (solo per build da sorgente)

## Configurazione

Tutte le impostazioni si cambiano dal **menu contestuale** della system tray:

| Voce menu | Cosa fa |
|-----------|---------|
| _Modello_ | Cambia dimensione modello Whisper (richiede ricarica) |
| _Modificatori_ | CTRL / SHIFT / ALT / WIN per l'hotkey |
| _Tasto_ | Tasto dell'hotkey (es. Space, F1-F12, Copilot) |
| _Esci_ | Termina il programma |

Oppure modifica manualmente `config.json`:

```json
{
    "hotkey": {
        "modifiers": ["win", "shift"],
        "key": "f23"
    },
    "whisper": {
        "model_size": "small",
        "model_dir": "whisper-models",
        "device": "cpu",
        "compute_type": "int8"
    },
    "audio": {
        "sample_rate": 16000,
        "silence_threshold": 0.03,
        "silence_duration_sec": 1.5,
        "min_duration_sec": 0.5,
        "max_duration_sec": 30
    }
}
```

### Tasto Copilot

Se la tastiera ha il tasto Copilot (Windows 11):

1. Click destro sull'icona → _Tasto_ → `copilot`
2. Il programma intercetta `Win+Shift+F23` a livello kernel tramite hook di sistema
3. Non serve software aggiuntivo (PowerToys/AutoHotkey)

## Struttura cartelle

```
TTS/
├── main.py                # Entry point
├── config.py              # Caricamento/salvataggio config.json
├── config.json            # Impostazioni utente
├── hotkey.py              # Hook globale tastiera (Copilot)
├── recorder.py            # Registrazione audio con silence detection
├── transcriber.py         # Trascrizione con faster-whisper
├── paster.py              # Clipboard + Ctrl+V
├── tray.py                # Icona system tray + menu
├── download_models.py     # Download modelli da Hugging Face
├── ThaSkull.ico           # Icona del programma
├── whisper-models/        # Modelli Whisper (IGNORATI da git)
│   ├── tiny/
│   ├── base/
│   ├── small/
│   ├── medium/
│   └── large-v3/
└── dist/TTS/              # Build PyInstaller
    └── TTS.exe
```

## Risoluzione problemi

| Problema | Soluzione |
|----------|-----------|
| **Nessun audio registrato** | Controlla che il microfono sia abilitato in Windows → Impostazioni → Sistema → Suono |
| **Trascrizione vuota (".")** | Abbassa `silence_threshold` in config.json (es. 0.01). Parla più vicino al microfono |
| **Il tasto Copilot non funziona** | Verifica che la tastiera abbia un tasto Copilot fisico. Prova `Win+Shift+F23` o configura un altro hotkey |
| **Modello non caricato** | Verifica che `whisper-models/<modello>/model.bin` esista. Riavvia il programma |
| **Errore "No module named ..."** | Se buildi da sorgente: `pip install -r requirements.txt`. Se usi l'exe: ri-scarica la release |
| **Antivirus blocca l'exe** | PyInstaller produce falsi positivi. Aggiungi un'eccezione o builda da sorgente |
| **L'exe non si avvia** | Installa [Microsoft Visual C++ Redistributable](https://aka.ms/vcredist) |

## Licenza

MIT
