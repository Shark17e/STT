# Dettatura Vocale Offline (Dictate-Win)

Programma in system tray che ascolta dal microfono, trascrive in testo con Whisper (offline) e incolla il risultato nella finestra attiva.

## Funzionamento

- Premi l'hotkey (default: tasto **Copilot** o `Win+Shift+F23`, configurabile dal menu tray)
- Parla al microfono
- Rilascia o attendi il silenzio (1.5s)
- Il testo trascritto viene incollato automaticamente

## Requisiti

- Windows 11 (testato su 23H2+)
- Microfono funzionante
- ~2-6 GB di RAM in base al modello Whisper scelto
- CPU con supporto AVX (presente in qualsiasi Intel/AMD dal 2010+)

## Installazione rapida

Se usi l'exe precompilato (nella release):

1. Scarica `TTS.zip` ed estrai in una cartella
2. Posiziona la cartella `whisper-models/` con i modelli scaricati accanto a `TTS.exe`
3. Avvia `TTS.exe` (appare l'icona nella system tray)
4. Premi **Copilot** o l'hotkey che hai configurato

## Build da sorgente

```powershell
git clone <url-repo>
cd TTS
pip install -r requirements.txt

# Per build exe (serve PyInstaller)
pyinstaller --noconsole --onedir --name TTS --icon ThaSkull.ico ^
    --hidden-import faster_whisper --hidden-import ctranslate2 ^
    --hidden-import tokenizers --hidden-import sounddevice ^
    --hidden-import soundfile --hidden-import PIL._tkinter_finder ^
    --hidden-import pyautogui._pyautogui_win --hidden-import pyperclip ^
    --hidden-import pystray --hidden-import _cffi_backend ^
    --collect-all faster_whisper --collect-all ctranslate2 ^
    --collect-all tokenizers --collect-all sounddevice main.py
```

## Modelli

Scaricare i modelli Whisper nella cartella `whisper-models/`:

```powershell
python download_models.py
```

Oppure manualmente da [huggingface/Systran/faster-whisper](https://huggingface.co/Systran).

## Tasto Copilot

Se la tastiera ha il tasto Copilot, impostalo come hotkey nel menu tray:
- Right-click sull'icona → **Tasto** → `copilot`

Il programma intercetta `Win+Shift+F23` a livello di hook di sistema, impedendo a Windows di riceverli. Non serve software aggiuntivo.

## Licenza

MIT
