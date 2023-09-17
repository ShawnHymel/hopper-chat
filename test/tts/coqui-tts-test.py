"""

Installation:

    python -m pip install TTS
    python -m pip install numpy==1.22.4
    
From: https://tts.readthedocs.io/en/latest/inference.html
    
"""

import subprocess
import time

from TTS.api import TTS

TEXT = "In a hole in the ground there lived a hobbit. Not a nasty, " \
    "dirty, wet hole, filled with the ends of worms and an oozy " \
    "smell, nor yet a dry, bare, sandy hole with nothing in it to " \
    "sit down on or to eat: it was a hobbit-hole, and that means " \
    "comfort."
MODEL = "tts_models/en/ljspeech/speedy-speech"
OUT_FILE = "out.wav"

# List models
print("--- Models ---")
models = TTS().list_models()
for model in models:
    print(model)
print()

# Initialize TTS
tts = TTS(model_name=MODEL, progress_bar=False)

# Convert text to speech
timestamp = time.time()
tts.tts_to_file(text=TEXT, file_path=OUT_FILE)
print(f"TTS time: {time.time() - timestamp}")
