"""
03_transcribe.py
Trascrive l'audio usando faster-whisper (locale) o OpenAI Whisper API.
Output: JSON con segmenti e timestamp + TXT plain per leggibilità.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    AUDIO_PATH, TRANSCRIPT_PATH,
    TRANSCRIPTION_MODE, WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE,
    OPENAI_API_KEY,
)


def transcribe_local():
    """Usa faster-whisper in locale (CPU o CUDA)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[ERRORE] faster-whisper non installato. Esegui: pip install faster-whisper")
        sys.exit(1)

    print(f"[INFO] Caricamento modello Whisper '{WHISPER_MODEL}' su {WHISPER_DEVICE} ...")
    print(f"       (Il download del modello avviene solo la prima volta)")
    model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8")

    print(f"[1/1] Trascrizione in corso: {AUDIO_PATH.name} ...")
    print(f"      Lingua: {WHISPER_LANGUAGE} | Modello: {WHISPER_MODEL}")
    print(f"      (Per 3h di audio con CPU medium: ~30-60 min. Lascia girare.)")

    segments, info = model.transcribe(
        str(AUDIO_PATH),
        language=WHISPER_LANGUAGE if WHISPER_LANGUAGE != "auto" else None,
        beam_size=5,
        vad_filter=True,          # Voice Activity Detection: salta i silenzi
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    print(f"      Lingua rilevata: {info.language} (probabilità: {info.language_probability:.2f})")

    results = []
    for seg in segments:
        results.append({
            "start": round(seg.start, 2),
            "end":   round(seg.end, 2),
            "text":  seg.text.strip(),
        })
        # Stampa progresso ogni 5 minuti di audio
        if results and len(results) % 50 == 0:
            print(f"      ... {seg.end/60:.1f} min trascritti")

    return results


def transcribe_api():
    """Usa l'API OpenAI Whisper (richiede OPENAI_API_KEY)."""
    if not OPENAI_API_KEY:
        print("[ERRORE] OPENAI_API_KEY non impostata nel file .env")
        sys.exit(1)
    try:
        from openai import OpenAI
    except ImportError:
        print("[ERRORE] openai non installato. Esegui: pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"[1/1] Invio a OpenAI Whisper API: {AUDIO_PATH.name} ...")

    with open(AUDIO_PATH, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=WHISPER_LANGUAGE if WHISPER_LANGUAGE != "auto" else None,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    results = [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in response.segments
    ]
    return results


def save_transcript(segments: list):
    TRANSCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Salva JSON con timestamp (usato da 04_summarize.py)
    with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    # Salva anche TXT leggibile con timestamp
    txt_path = TRANSCRIPT_PATH.with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            ts = f"[{int(seg['start']//60):02d}:{int(seg['start']%60):02d}]"
            f.write(f"{ts} {seg['text']}\n")

    total_chars = sum(len(s["text"]) for s in segments)
    print(f"[OK] Trascrizione salvata:")
    print(f"     JSON: {TRANSCRIPT_PATH}")
    print(f"     TXT:  {txt_path}")
    print(f"     Segmenti: {len(segments)} | Caratteri totali: {total_chars:,}")


def transcribe():
    if TRANSCRIPT_PATH.exists():
        print(f"[SKIP] Trascrizione già presente: {TRANSCRIPT_PATH}")
        return

    if not AUDIO_PATH.exists():
        print(f"[ERRORE] Audio non trovato: {AUDIO_PATH}")
        print("  → Esegui prima 01_extract_audio.py")
        sys.exit(1)

    if TRANSCRIPTION_MODE == "local":
        segments = transcribe_local()
    elif TRANSCRIPTION_MODE == "api":
        segments = transcribe_api()
    else:
        print(f"[ERRORE] TRANSCRIPTION_MODE non valido: '{TRANSCRIPTION_MODE}'. Usa 'local' o 'api'.")
        sys.exit(1)

    save_transcript(segments)


if __name__ == "__main__":
    transcribe()
