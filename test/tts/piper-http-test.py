import requests
import numpy as np
import resampy
import sounddevice as sd
from scipy.io import wavfile

# URL and parameters
url = 'http://10.0.0.100:5002'
params = {'text': 'This is a test.'}

# Set input and output audio devices (get from the "Available sound devices")
AUDIO_OUTPUT_INDEX = 2

# Volume (1.0 = normal, 2.0 = double volume)
AUDIO_OUTPUT_VOLUME = 1.0

# Sample rate (determined by speaker hardware)
AUDIO_OUTPUT_SAMPLE_RATE = 48000

TTS_MODEL_SAMPLE_RATE = 22050   # Determined by model

print("Available sound devices:")
print(sd.query_devices())

# Making GET request with parameters
response = requests.get(url, params=params)

# Play sound
wav = wavfile.read(response.content)
wav = np.array(wav) * AUDIO_OUTPUT_VOLUME
wav = resampy.resample(wav, TTS_MODEL_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE)
sd.play(wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
sd.wait()