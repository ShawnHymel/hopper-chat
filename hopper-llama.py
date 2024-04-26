"""
Hopper Chat with Ollama backend (local network)

Install dependences

See README for STT and TTS. For Ollama:

    python -m pip install ollama

Author: Shawn Hymel
Date: April 20, 2024
License: 0BSD (https://opensource.org/license/0bsd)
"""

import queue
import time
import sys
import json
import os
from collections import deque
import time
import io

import requests
from dotenv import load_dotenv
import numpy as np
import resampy
import sounddevice as sd
import soundfile as sf
from vosk import Model, KaldiRecognizer
import ollama

#---------------------------------------------------------------------------------------------------
# Settings

# Print stuff to console
DEBUG = True

# Set input and output audio devices (get from the "Available sound devices")
AUDIO_INPUT_INDEX = 1
AUDIO_OUTPUT_INDEX = 2

# Volume (1.0 = normal, 2.0 = double volume)
AUDIO_OUTPUT_VOLUME = 1.0

# Sample rate (determined by speaker hardware)
AUDIO_OUTPUT_SAMPLE_RATE = 48000

# Set notification sound (when wake phrase is heard). Leave blank for no notification sound.
NOTIFICATION_PATH = "./sounds/cowbell.wav"

# Set wake words or phrases
WAKE_PHRASES = [
    "hey hopper",
    "a hopper",
]

# Set action phrases
ACTION_CLEAR_HISTORY = [    # Clear chat history
    "clear history",
    "clear chat history",
]
ACTION_STOP = [             # Return to waiting for wake phrase
    "stop",
    "stop listening",
    "nevermind", 
    "never mind",
]

# Server settings
SERVER_IP = "10.0.0.143"

# Chat settings
CHAT_MAX_HISTORY = 20           # Number of prompts and replies to remember
CHAT_MAX_REPLY_SENTENCES = 2    # Max number of sentences to respond with (0 is infinite)

# Ollama settings
OLLAMA_SERVER_URL = f"http://{SERVER_IP}:10802"
OLLAMA_MODEL = "llama3:8b"


# TTS settings
TTS_ENABLE = True
PIPER_URL = f"http://{SERVER_IP}:10803"
TTS_MODEL_SAMPLE_RATE = 22050   # Determined by model

#---------------------------------------------------------------------------------------------------
# Classes

class FixedSizeQueue:
    """
    Fixed size array with FIFO
    """
    def __init__(self, max_size):
        self.queue = deque(maxlen=max_size)

    def push(self, item):
        self.queue.append(item)

    def get(self):
        return list(self.queue)

#---------------------------------------------------------------------------------------------------
# Functions

def callback_record(in_data, frames, time, debug):
    """
    Fill global input queue with audio data
    """
    global in_q

    if debug:
        print(status, file=sys.stderr)
    in_q.put(bytes(in_data))

def wait_for_stt(sd, recognizer):
    """
    Wait for STT to hear something and return the text
    """

    global in_q

    # Listen for wake word/phrase
    with sd.RawInputStream(
        dtype="int16",
        channels=1,
        callback=callback_record
    ):
        if DEBUG:
            print("Listening...")
    
        # Perform keyword spotting
        while True:
            data = in_q.get()
            if recognizer.AcceptWaveform(data):

                # Perform speech-to-text (STT)
                result = recognizer.Result()
                result_dict = json.loads(result)
                result_text = result_dict.get("text", "")

                return result_text

def query_chat(msg):
    """
    Send message to chat backend (Ollama) and return response text
    """

    global msg_history
    global chat_client

    # Add prompt to message history
    msg_history.push({
        "role": "user",
        "content": msg,
    })

    # Query Ollama
    stream = chat_client.chat(
        model=OLLAMA_MODEL,
        messages=msg_history.get(),
        stream=True
    )

    # Stream reply
    reply = ""
    for chunk in stream:
        part = chunk["message"]["content"]
        # print(part, end="", flush=True)
        reply = reply + part

    # Add reply to message history
    msg_history.push({
        "role": "assistant",
        "content": reply,
    })

    return reply

def do_tts(msg):
    """
    Send text to TTS engine and play sound over speakers.
    """

    # Make request
    params = {"text": msg,}
    resp = requests.get(PIPER_URL, params=params)

    # Resample the audio
    wav, sample_rate = sf.read(io.BytesIO(resp.content))
    wav = np.array(wav) * AUDIO_OUTPUT_VOLUME
    wav = resampy.resample(
        wav,
        sample_rate,
        AUDIO_OUTPUT_SAMPLE_RATE
    )

    # Play the audio
    sd.play(wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
    sd.wait()

#---------------------------------------------------------------------------------------------------
# Main

# Print available sound devices
if DEBUG:
    print("Available sound devices:")
    print(sd.query_devices())

# Set the input and output devices
sd.default.device = [AUDIO_INPUT_INDEX, AUDIO_OUTPUT_INDEX]

# Get sample rate
device_info = sd.query_devices(sd.default.device[0], "input")
sample_rate = int(device_info["default_samplerate"])

# Display input device info
if DEBUG:
    print(f"Input device info: {json.dumps(device_info, indent=2)}")

# Load notification sound into memory
if NOTIFICATION_PATH:
    notification_wav, notification_sample_rate = sf.read(NOTIFICATION_PATH)
    notification_wav = np.array(notification_wav) * AUDIO_OUTPUT_VOLUME
    notification_wav = resampy.resample(
        notification_wav,
        notification_sample_rate,
        AUDIO_OUTPUT_SAMPLE_RATE
    )

# Set up queue and callback
in_q = queue.Queue()

# Build the model
model = Model(lang="en-us")
recognizer = KaldiRecognizer(model, sample_rate)
recognizer.SetWords(False)

# Initialize Ollama client
chat_client = ollama.Client(host=OLLAMA_SERVER_URL)

# Superloop
msg_history = FixedSizeQueue(CHAT_MAX_HISTORY)
while True:
    
    # Listen for wake word or phrase
    timestamp = time.time()
    text = wait_for_stt(sd, recognizer)
    if DEBUG:
        print(f"Heard: {text}")
    if text in WAKE_PHRASES:
        if DEBUG:
            print(f"Wake phrase detected.")
            print(f"STT time: {time.time() - timestamp}")
    else:
        continue

    # Play notification sound
    if NOTIFICATION_PATH:
        sd.play(notification_wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
        sd.wait()

    # Listen for query
    timestamp = time.time()
    text = wait_for_stt(sd, recognizer)
    if text != "":
        if DEBUG:
            print(f"Heard: {text}")
            print(f"STT time: {time.time() - timestamp}")
    else:
        if DEBUG:
            print("No sound detected. Returning to wake word detection.")
        continue
    listening_for_query = False

    # Perform actions for particular phrases
    if text in ACTION_CLEAR_HISTORY:
        if DEBUG:
            print("ACTION: clearning history")
        msg_history = FixedSizeQueue(CHAT_MAX_HISTORY)
        continue
    elif text in ACTION_STOP:
        if DEBUG:
            print("ACTION: stop listening")
        continue

    # Default action: query chat backend
    else:

        # Send request with limited reply length
        if CHAT_MAX_REPLY_SENTENCES > 0:
            msg = text + f". Your response must be {CHAT_MAX_REPLY_SENTENCES} sentences or fewer."
        else:
            msg = text
        if DEBUG:
            print(f"Sending: {msg}")
        timestamp = time.time()
        reply = query_chat(msg)
        if DEBUG:
            print(f"Received: {reply}")
            print(f"LLM time: {time.time() - timestamp}")

        # Perform text-to-speech (TTS)
        if TTS_ENABLE and reply:
            if DEBUG:
                print("Playing reply...")
            do_tts(reply)
            if DEBUG:
                print(f"TTS time: {time.time() - timestamp}")
