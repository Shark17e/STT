import os
import sys

from huggingface_hub import snapshot_download

MODELS = {
    "tiny": "guillaumekln/faster-whisper-tiny",
    "base": "guillaumekln/faster-whisper-base",
    "small": "guillaumekln/faster-whisper-small",
    "medium": "guillaumekln/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}

SIZES = {
    "tiny": "~150 MB",
    "base": "~300 MB",
    "small": "~500 MB",
    "medium": "~1.5 GB",
    "large-v3": "~3 GB",
}


def main():
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whisper-models")

    selected = sys.argv[1:] if len(sys.argv) > 1 else list(MODELS.keys())

    def _parse_mb(s):
        num = float(s.split()[0].lstrip("~"))
        if "GB" in s:
            return int(num * 1024)
        return int(num)

    total_mb = sum(_parse_mb(v) for k, v in SIZES.items() if k in selected)
    print(f"Modelli da scaricare: {', '.join(selected)}")
    print(f"Spazio stimato: ~{total_mb} MB (~{total_mb/1024:.1f} GB)")
    print()

    for name in selected:
        if name not in MODELS:
            print(f"Modello sconosciuto: {name}. Opzioni: {', '.join(MODELS.keys())}")
            continue

        repo_id = MODELS[name]
        local_dir = os.path.join(base_dir, name)
        os.makedirs(local_dir, exist_ok=True)

        print(f"Download {name} ({SIZES[name]}) da {repo_id} ...")
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
        )
        print(f"Completato: {local_dir}\n")

    print("Tutti i download completati.")
    print(f"I modelli si trovano in: {base_dir}")
    print("Modifica 'model_size' in config.json per cambiare modello.")


if __name__ == "__main__":
    main()
