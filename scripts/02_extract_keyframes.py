"""
02_extract_keyframes.py
Rileva i cambi di scena nel video ed estrae un frame per ogni scena.
Dipendenza: scenedetect[opencv]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import VIDEO_PATH, KEYFRAMES_DIR, SCENE_THRESHOLD


def extract_keyframes():
    if not VIDEO_PATH.exists():
        print(f"[ERRORE] Video non trovato: {VIDEO_PATH}")
        sys.exit(1)

    if KEYFRAMES_DIR.exists() and any(KEYFRAMES_DIR.iterdir()):
        print(f"[SKIP] Keyframe già estratti in: {KEYFRAMES_DIR}")
        return

    KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
        from scenedetect.scene_manager import save_images
    except ImportError:
        print("[ERRORE] scenedetect non installato. Esegui: pip install scenedetect[opencv]")
        sys.exit(1)

    print(f"[1/2] Rilevamento scene in: {VIDEO_PATH.name} (threshold={SCENE_THRESHOLD}) ...")
    video      = open_video(str(VIDEO_PATH))
    manager    = SceneManager()
    manager.add_detector(ContentDetector(threshold=SCENE_THRESHOLD))
    manager.detect_scenes(video, show_progress=True)
    scene_list = manager.get_scene_list()

    print(f"      Scene rilevate: {len(scene_list)}")

    if not scene_list:
        print("[WARN] Nessun cambio scena rilevato. Prova ad abbassare SCENE_THRESHOLD in config.py")
        return

    print(f"[2/2] Salvataggio keyframe in: {KEYFRAMES_DIR} ...")
    video = open_video(str(VIDEO_PATH))   # reopen per save_images
    save_images(
        scene_list,
        video,
        num_images=1,
        output_dir=str(KEYFRAMES_DIR),
        image_name_template="$SCENE_NUMBER-$TIMECODE",
    )

    saved = list(KEYFRAMES_DIR.glob("*.jpg"))
    print(f"[OK] {len(saved)} keyframe salvati in: {KEYFRAMES_DIR}")


if __name__ == "__main__":
    extract_keyframes()
