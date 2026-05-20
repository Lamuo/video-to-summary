"""
run_all.py — esegue la pipeline completa in sequenza.
"""

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent
SCRIPT_DIR = ROOT_DIR / "scripts"


def run_script(script_name: str) -> None:
	script_path = SCRIPT_DIR / script_name
	result = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT_DIR))
	if result.returncode != 0:
		raise SystemExit(result.returncode)


print("=" * 60)
print("  video-to-summary — pipeline completa")
print("=" * 60)

print("\n▶ Step 1: Estrazione audio")
run_script("01_extract_audio.py")

print("\n▶ Step 2: Estrazione keyframe")
run_script("02_extract_keyframes.py")

print("\n▶ Step 3: Trascrizione")
run_script("03_transcribe.py")

print("\n▶ Step 4: Riassunto")
run_script("04_summarize.py")

print("\n" + "=" * 60)
print("  Pipeline completata!")
print("=" * 60)
