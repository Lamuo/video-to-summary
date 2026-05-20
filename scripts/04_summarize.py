"""
04_summarize.py
Divide la trascrizione in chunk e genera un riassunto strutturato per sessione D&D.
Supporta Google Gemini (free tier) e usa i keyframe estratti per aggiungere contesto visivo.
Output: Markdown in output/summary/
"""

import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TRANSCRIPT_PATH, SUMMARY_PATH, VISUAL_NOTES_PATH,
    KEYFRAMES_DIR, SUMMARY_PROVIDER, CHUNK_SIZE,
    GEMINI_API_KEY, SUMMARY_LANGUAGE, SESSION_CONTEXT,
    SESSION_NAME, VISUAL_FRAME_LIMIT,
)


# ── Prompt templates ──────────────────────────────────────────────────────────

CHUNK_SYSTEM_PROMPT = f"""Sei un assistente specializzato nel riassumere sessioni di gioco di ruolo (D&D / TTRPG).
Analizza il seguente frammento di trascrizione e produci un riassunto strutturato in {SUMMARY_LANGUAGE}.

Contesto della campagna:
{SESSION_CONTEXT}

Per ogni frammento estrai:
- **Eventi principali**: cosa è successo narrativamente
- **Combattimenti / scontri**: se presenti, esito e momenti salienti
- **Decisioni importanti**: scelte dei giocatori con conseguenze
- **Personaggi / PNG incontrati**: nomi e ruolo nella scena
- **Informazioni ottenute**: lore, indizi, segreti rivelati
- **Tiri rilevanti**: se menzionati nel testo (es. "ho fatto 20 sulla Percezione")

Sii conciso ma non omettere nulla di rilevante. Usa il formato Markdown con elenchi puntati."""

FINAL_SYSTEM_PROMPT = f"""Sei un assistente specializzato nel riassumere sessioni di D&D.
Hai ricevuto i riassunti parziali di una sessione divisa in segmenti temporali.
Produci un riassunto finale completo e coerente in {SUMMARY_LANGUAGE}.

Contesto della campagna:
{SESSION_CONTEXT}

Il riassunto finale deve avere questa struttura Markdown:

# Sessione — [titolo evocativo che cattura il tema della sessione]

## Riepilogo rapido
[2-3 frasi che descrivono l'essenza della sessione]

## Cronologia degli eventi
[Lista ordinata degli eventi principali con timestamp approssimativo se disponibile]

## Combattimenti e scontri
[Se presenti: chi, dove, come è andata, conseguenze]

## Personaggi e PNG
[Chi è apparso, cosa ha detto/fatto di rilevante]

## Informazioni e lore ottenute
[Tutto ciò che i personaggi hanno scoperto]

## Decisioni chiave
[Scelte importanti dei giocatori e loro impatto]

## Domande aperte / Fili narrativi
[Cose non risolte, misteri, hook per la prossima sessione]

## Note per il DM
[Cose da ricordare per la prossima sessione: promesse fatte, conseguenze pendenti, ecc.]"""


# ── Chunking ──────────────────────────────────────────────────────────────────

def load_transcript() -> list[dict]:
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_transcript(segments: list[dict]) -> list[str]:
    """Raggruppa i segmenti in chunk di circa CHUNK_SIZE caratteri."""
    chunks = []
    current_chunk = []
    current_size  = 0

    for seg in segments:
        ts   = f"[{int(seg['start']//60):02d}:{int(seg['start']%60):02d}]"
        line = f"{ts} {seg['text']}\n"
        current_chunk.append(line)
        current_size += len(line)

        if current_size >= CHUNK_SIZE:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_size  = 0

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


# ── Provider: Google Gemini ───────────────────────────────────────────────────

def call_gemini(system: str, user: str) -> str:
    try:
        import google.generativeai as genai
        from PIL import Image
    except ImportError:
        print("[ERRORE] dipendenze Gemini non installate. Esegui: pip install google-generativeai Pillow")
        sys.exit(1)

    if not GEMINI_API_KEY:
        print("[ERRORE] GEMINI_API_KEY non impostata nel file .env")
        sys.exit(1)

    genai.configure(api_key=GEMINI_API_KEY)
    model    = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
    response = model.generate_content(user)
    return response.text


def call_gemini_vision(system: str, user: str, image_paths: list[Path]) -> str:
    try:
        import google.generativeai as genai
        from PIL import Image
    except ImportError:
        print("[ERRORE] dipendenze Gemini non installate. Esegui: pip install google-generativeai Pillow")
        sys.exit(1)

    if not GEMINI_API_KEY:
        print("[ERRORE] GEMINI_API_KEY non impostata nel file .env")
        sys.exit(1)

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
    images = [Image.open(path).convert("RGB") for path in image_paths]
    response = model.generate_content([user, *images])
    return response.text


# ── Dispatcher ────────────────────────────────────────────────────────────────

def call_llm(system: str, user: str) -> str:
    if SUMMARY_PROVIDER == "gemini":
        return call_gemini(system, user)
    else:
        print(f"[ERRORE] SUMMARY_PROVIDER non valido: '{SUMMARY_PROVIDER}'. Usa 'gemini'.")
        sys.exit(1)


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.name)
    key = []
    for part in parts:
        key.append(int(part) if part.isdigit() else part.lower())
    return key


def select_keyframes(paths: list[Path], limit: int) -> list[Path]:
    if limit <= 0 or len(paths) <= limit:
        return paths

    if limit == 1:
        return [paths[len(paths) // 2]]

    chosen_indexes: list[int] = []
    last_index = len(paths) - 1
    for i in range(limit):
        index = round(i * last_index / (limit - 1))
        if index not in chosen_indexes:
            chosen_indexes.append(index)

    return [paths[index] for index in chosen_indexes]


def describe_keyframes() -> list[dict]:
    if not KEYFRAMES_DIR.exists():
        print(f"[INFO] Nessuna cartella keyframe trovata: {KEYFRAMES_DIR}")
        return []

    frame_paths = sorted(KEYFRAMES_DIR.glob("*.jpg"), key=natural_key)
    if not frame_paths:
        print(f"[INFO] Nessun keyframe trovato in: {KEYFRAMES_DIR}")
        return []

    selected_paths = select_keyframes(frame_paths, VISUAL_FRAME_LIMIT)
    if len(selected_paths) < len(frame_paths):
        print(f"[INFO] Keyframe selezionati: {len(selected_paths)}/{len(frame_paths)} per il contesto visivo")

    system = (
        "Sei un assistente che descrive immagini di una sessione di D&D. "
        "Devi essere concreto, breve e utile per un riassunto della sessione."
    )
    user = (
        "Descrivi l'immagine in italiano con taglio operativo per un riassunto di sessione D&D. "
        "Indica se vedi mappe, personaggi, miniature, schede, risultati di dadi, testo leggibile, "
        "o qualsiasi dettaglio visivo rilevante per la cronologia. Se non c'e' nulla di importante, dillo chiaramente."
    )

    notes = []
    batch_size = 4
    for start_index in range(0, len(selected_paths), batch_size):
        batch = selected_paths[start_index:start_index + batch_size]
        batch_label = ", ".join(path.stem for path in batch)
        print(f"      Visione keyframe ({start_index + 1}-{start_index + len(batch)}) / {len(selected_paths)} ...", end=" ", flush=True)
        description = call_gemini_vision(system, user, batch)
        notes.append({
            "frames": [path.name for path in batch],
            "labels": [path.stem for path in batch],
            "description": description.strip(),
        })
        print("✓")

    VISUAL_NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VISUAL_NOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

    return notes


# ── Pipeline principale ───────────────────────────────────────────────────────

def summarize():
    if SUMMARY_PATH.exists():
        print(f"[SKIP] Riassunto già presente: {SUMMARY_PATH}")
        return

    if not TRANSCRIPT_PATH.exists():
        print(f"[ERRORE] Trascrizione non trovata: {TRANSCRIPT_PATH}")
        print("  → Esegui prima 03_transcribe.py")
        sys.exit(1)

    print("[1/3] Caricamento trascrizione ...")
    segments = load_transcript()
    chunks   = chunk_transcript(segments)
    total_chars = sum(len(s["text"]) for s in segments)
    print(f"      Segmenti: {len(segments)} | Caratteri: {total_chars:,} | Chunk: {len(chunks)}")

    print("\n[1b/3] Estrazione contesto visivo dai keyframe ...")
    visual_notes = describe_keyframes()
    if visual_notes:
        print(f"      Blocchi visivi: {len(visual_notes)}")
    else:
        print("      Nessun contesto visivo aggiunto")

    # ── Step 1: riassunto per chunk ───────────────────────────────────────────
    print(f"\n[2/3] Riassunto chunk ({len(chunks)} chiamate a {SUMMARY_PROVIDER}) ...")
    chunk_summaries = []
    for i, chunk in enumerate(chunks, 1):
        start_min = int(chunk.split("]")[0].replace("[", "").split(":")[0]) if "[" in chunk else 0
        print(f"      Chunk {i}/{len(chunks)} (~{start_min} min) ...", end=" ", flush=True)
        summary = call_llm(CHUNK_SYSTEM_PROMPT, chunk)
        chunk_summaries.append(f"### Segmento {i}\n{summary}")
        print("✓")

    # ── Step 2: sintesi finale ────────────────────────────────────────────────
    print(f"\n[3/3] Sintesi finale ...")
    combined_parts = ["\n\n".join(chunk_summaries)]
    if visual_notes:
        visual_block = ["### Contesto visivo estratto dai keyframe"]
        for block in visual_notes:
            visual_block.append(f"- {', '.join(block['labels'])}: {block['description']}")
        combined_parts.append("\n".join(visual_block))

    combined = "\n\n".join(combined_parts)
    final    = call_llm(FINAL_SYSTEM_PROMPT, combined)

    # ── Salvataggio ───────────────────────────────────────────────────────────
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(final)

    # Salva anche i riassunti intermedi per debug/revisione
    chunks_path = SUMMARY_PATH.parent / f"{SESSION_NAME}_chunks.md"
    with open(chunks_path, "w", encoding="utf-8") as f:
        f.write(f"# Riassunti intermedi — {SESSION_NAME}\n\n")
        f.write(combined)

    print(f"\n[OK] Riassunto finale: {SUMMARY_PATH}")
    print(f"[OK] Riassunti intermedi: {chunks_path}")


if __name__ == "__main__":
    summarize()
