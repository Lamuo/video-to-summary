"""
config.py — configurazione centralizzata per video-to-summary
Modifica questo file prima di eseguire gli script.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ── Path base ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
INPUT_DIR   = BASE_DIR / "input"
OUTPUT_DIR  = BASE_DIR / "output"

# ── File video di input ───────────────────────────────────────────────────────
# Cambia questo con il nome del tuo file MP4
VIDEO_FILENAME = "sessione.mp4"
VIDEO_PATH     = INPUT_DIR / VIDEO_FILENAME
SESSION_NAME   = VIDEO_FILENAME.replace(".mp4", "")  # usato per nominare gli output

# ── Output paths ──────────────────────────────────────────────────────────────
AUDIO_PATH      = OUTPUT_DIR / "audio"      / f"{SESSION_NAME}.mp3"
KEYFRAMES_DIR   = OUTPUT_DIR / "keyframes"  / SESSION_NAME
TRANSCRIPT_PATH = OUTPUT_DIR / "transcript" / f"{SESSION_NAME}.json"
SUMMARY_PATH    = OUTPUT_DIR / "summary"    / f"{SESSION_NAME}.md"
VISUAL_NOTES_PATH = OUTPUT_DIR / "summary"  / f"{SESSION_NAME}_visuals.json"

# ── Audio extraction (ffmpeg) ─────────────────────────────────────────────────
AUDIO_BITRATE  = "64k"     # mono 64k è sufficiente per speech
AUDIO_CHANNELS = 1         # mono

# ── Keyframe extraction (PySceneDetect) ───────────────────────────────────────
# Soglia di rilevamento cambio scena (0-100, più basso = più sensibile)
SCENE_THRESHOLD = 27.0

# ── Trascrizione ──────────────────────────────────────────────────────────────
TRANSCRIPTION_MODE = "local"   # "local" = faster-whisper, "api" = OpenAI Whisper API

# faster-whisper locale
WHISPER_MODEL    = "medium"    # tiny | base | small | medium | large-v3
WHISPER_LANGUAGE = "it"        # lingua del video (it, en, auto)
WHISPER_DEVICE   = "cpu"       # "cpu" o "cuda" se hai GPU NVIDIA

# OpenAI API (usata solo se TRANSCRIPTION_MODE = "api")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Summarization ─────────────────────────────────────────────────────────────
SUMMARY_PROVIDER = "gemini"   # "anthropic" o "gemini"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")

# Keyframe analysis / vision
VISUAL_FRAME_LIMIT = 24   # limita i keyframe inviati al modello visivo

# Dimensione dei chunk per la summarization (in caratteri)
# ~30 min di parlato ≈ 15.000-20.000 caratteri
CHUNK_SIZE = 18_000

# Lingua del riassunto finale
SUMMARY_LANGUAGE = "italiano"

# Contesto aggiuntivo per il modello (facoltativo, migliora la qualità)
SESSION_CONTEXT = """
Questa è una sessione di SotDL (Shadow of the Demon Lord), un TTRPG come D&D (Dungeons & Dragons).
Il gruppo si chiama [NOME GRUPPO].
La campagna si chiama ClusterSomnia
I personaggi dei giocatori presenti sono: Alsa, Vishara, Quark, Black, Diane, Edgar e Zoe.
Altri personaggi secondari sono: [ELENCO PERSONAGGI SECONDARI]
"""
