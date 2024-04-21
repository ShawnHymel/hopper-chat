"""

Installation:

    python -m pip install TTS==0.22.0
    python -m pip install numpy==1.22.4
    
From: https://tts.readthedocs.io/en/latest/inference.html
    
"""

import subprocess
import time

import numpy as np
import resampy
import sounddevice as sd
import soundfile as sf
from TTS.api import TTS

TEXT = "In a hole in the ground there lived a hobbit. Not a nasty, " \
    "dirty, wet hole, filled with the ends of worms and an oozy " \
    "smell, nor yet a dry, bare, sandy hole with nothing in it to " \
    "sit down on or to eat: it was a hobbit-hole, and that means " \
    "comfort."
MODEL = "tts_models/en/ljspeech/speedy-speech"
MODEL_SAMPLE_RATE = 22050   # Sample rate determined by model
OUT_FILE = "out.wav"
AUDIO_OUTPUT_INDEX = 1
AUDIO_OUTPUT_SAMPLE_RATE = 48000    # Determined by speaker's capabilities
VOLUME = 4.0

# List models
print("--- Models ---")
print(TTS().list_models())
# for model in models:
#     print(model)
print()

# Initialize TTS
tts = TTS(model_name=MODEL, progress_bar=False)

# Convert text to speech
timestamp = time.time()
# tts.tts_to_file(text=TEXT, file_path=OUT_FILE)
# wav, sample_rate = sf.read(OUT_FILE)
# print(f"Sample rate: {sample_rate}")
wav = tts.tts(text=TEXT)

# Resample
wav = np.array(wav) * VOLUME
print(wav.shape)
wav = resampy.resample(wav, MODEL_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE)

# Play
sd.play(wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
sd.wait()

print(f"TTS time: {time.time() - timestamp}")
