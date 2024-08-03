import io

import numpy as np
import requests
import resampy
from scipy.io import wavfile
import sounddevice as sd

# Settings
SERVER_IP = "127.0.0.1"
PIPER_SERVER_PORT = 10803
TTS_MODEL_SAMPLE_RATE = 22050       # Determined by model
AUDIO_OUTPUT_SAMPLE_RATE = 48000    # Determined by speaker's capabilities
AUDIO_OUTPUT_VOLUME = 1.0
MESSAGE = "Hello, this is a test message."
AUDIO_OUTPUT_INDEX = 0

# Derived settings
PIPER_URL = f"http://{SERVER_IP}:{PIPER_SERVER_PORT}"

# Make request to TTS server
params = {"text": MESSAGE}
resp = requests.get(PIPER_URL, params=params)
if resp.status_code != 200:
    raise RuntimeError(f"Failed to get response from TTS server: {resp.status_code}")

# Convert response to wav, adjust volume, and resample as needed
sample_rate, wav = wavfile.read(io.BytesIO(resp.content))

# Convert wav array to float
if wav.dtype == np.int16:
    wav = wav.astype(np.float32) / np.iinfo(np.int16).max

# Print dtype and max value
print(f"Array dtype: {wav.dtype}")
print(f"Array max value: {np.max(wav)}")

# Adjust volume and resample
wav = np.array(wav) * AUDIO_OUTPUT_VOLUME
if sample_rate != AUDIO_OUTPUT_SAMPLE_RATE:
    wav = resampy.resample(
        wav,
        sample_rate,
        AUDIO_OUTPUT_SAMPLE_RATE
    )

# Play wav
print(f"Playing wav with sample rate {AUDIO_OUTPUT_SAMPLE_RATE}")
sd.play(wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
sd.wait()
