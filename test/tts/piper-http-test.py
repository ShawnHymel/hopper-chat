import io

import requests
import numpy as np
import resampy
import sounddevice as sd
import soundfile as sf

# URL and parameters
url = 'http://127.0.0.1:10803'
params = {'text': 'This is a test.'}
wav_path = "./test.wav"

# Set input and output audio devices (get from the "Available sound devices")
AUDIO_INPUT_INDEX = 1
AUDIO_OUTPUT_INDEX = 0

# Volume (1.0 = normal, 2.0 = double volume)
AUDIO_OUTPUT_VOLUME = 0.5

# Sample rate (determined by speaker hardware)
AUDIO_OUTPUT_SAMPLE_RATE = 48000
TTS_MODEL_SAMPLE_RATE = 22050   # Determined by model

print("Available sound devices:")
print(sd.query_devices())

# Making GET request with parameters
response = requests.get(url, params=params)

# Play the audio
wav, sample_rate = sf.read(io.BytesIO(response.content))
wav = np.array(wav) * AUDIO_OUTPUT_VOLUME
wav = resampy.resample(
    wav,
    sample_rate,
    AUDIO_OUTPUT_SAMPLE_RATE
)
sd.play(wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
sd.wait()
