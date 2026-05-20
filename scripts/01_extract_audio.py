"""
01_extract_audio.py
Estrae la traccia audio dal video MP4 come MP3 mono.
Dipendenza: ffmpeg nel PATH di sistema.
"""

import subprocess
import sys
from pathlib import Path

# Aggiunge la root del progetto al path per importare config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import VIDEO_PATH, AUDIO_PATH, AUDIO_BITRATE, AUDIO_CHANNELS


def extract_audio():
    if not VIDEO_PATH.exists():
        print(f"[ERRORE] Video non trovato: {VIDEO_PATH}")
        print(f"  → Metti il file MP4 nella cartella: {VIDEO_PATH.parent}")
        sys.exit(1)

    if AUDIO_PATH.exists():
        print(f"[SKIP] Audio già estratto: {AUDIO_PATH}")
        return

    AUDIO_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"[1/1] Estrazione audio da: {VIDEO_PATH.name} ...")
    cmd = [
        "ffmpeg",
        "-i", str(VIDEO_PATH),
        "-vn",                          # no video
        "-ac", str(AUDIO_CHANNELS),     # mono
        "-ab", AUDIO_BITRATE,           # bitrate
        "-ar", "16000",                 # 16kHz — ottimale per Whisper
        "-y",                           # overwrite silenzioso
        str(AUDIO_PATH),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("[ERRORE] ffmpeg ha fallito:")
        print(result.stderr)
        sys.exit(1)

    size_mb = AUDIO_PATH.stat().st_size / (1024 * 1024)
    print(f"[OK] Audio salvato: {AUDIO_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    extract_audio()
