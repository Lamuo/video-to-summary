# video-to-summary

Pipeline per estrarre un riassunto strutturato da una sessione di D&D registrata in video.

## Struttura

```
video-to-summary/
├── input/               ← metti qui il tuo .mp4
├── output/
│   ├── audio/           ← audio estratto (.mp3)
│   ├── keyframes/       ← frame estratti dai cambi scena (.jpg)
│   ├── transcript/      ← trascrizione Whisper (.txt / .json)
│   └── summary/         ← riassunto finale (.md)
├── scripts/
│   ├── 01_extract_audio.py
│   ├── 02_extract_keyframes.py
│   ├── 03_transcribe.py
│   └── 04_summarize.py
├── config.py            ← configurazione centralizzata
├── requirements.txt
└── README.md
```

## Prerequisiti

- Python 3.10+
- ffmpeg installato e nel PATH ([download](https://ffmpeg.org/download.html))
- Per la trascrizione: `faster-whisper` locale, senza API key
- Per il riassunto e le descrizioni visive: Google Gemini API key free tier
- Nessuna API a pagamento necessaria

## Setup

```bash
pip install -r requirements.txt
```

Copia il file `.env.example` in `.env` e inserisci la tua `GEMINI_API_KEY`.

## Utilizzo

Esegui gli script in ordine:

```bash
# 1. Estrai l'audio dal video
python scripts/01_extract_audio.py

# 2. Estrai i keyframe dai cambi scena
python scripts/02_extract_keyframes.py

# 3. Trascrivi l'audio
python scripts/03_transcribe.py

# 4. Genera il riassunto
python scripts/04_summarize.py
```

Oppure esegui la pipeline completa:

```bash
python run_all.py
```

## Note

- Gli script sono idempotenti: se un output esiste già viene saltato
- Ogni script legge i path da `config.py`
- Il riassunto finale viene salvato in `output/summary/` come Markdown
- I keyframe estratti vengono anche descritti con Gemini e usati nel riepilogo finale
