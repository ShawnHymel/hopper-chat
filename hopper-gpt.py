"""
Hopper Chat with ChatGPT backend

Author: Shawn Hymel
Date: April 20, 2024
License: 0BSD (https://opensource.org/license/0bsd)
"""

import queue
import time
import sys
import json
import os

from dotenv import load_dotenv
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import openai

#---------------------------------------------------------------------------------------------------
# Settings

# Print stuff to console
DEBUG = True

# Set input and output audio devices (get from the "Available sound devices")
AUDIO_INPUT_INDEX = 2
AUDIO_OUTPUT_INDEX = 1

# Set wake word or phrase
WAKE_PHRASE = "hey hopper"

# Set action phrases
ACTION_CLEAR_HISTORY = ["clear history", "clear chat history"]
ACTION_STOP = ["stop", "nevermind", "never mind"]

# ChatGPT settings
GPT_API_KEY = "" # Leave blank to load from OPENAI_API_KEY environment variable
GPT_MODEL = "gpt-4"

#---------------------------------------------------------------------------------------------------
# Functions

def callback_record(in_data, frames, time, debug):
    """
    Fill global input queue with audio data
    """
    if debug:
        print(status, file=sys.stderr)
    in_q.put(bytes(in_data))

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

# Set up queue and callback
in_q = queue.Queue()

# Build the model
model = Model(lang="en-us")
recognizer = KaldiRecognizer(model, sample_rate)
recognizer.SetWords(False)

# Load ChatGPT API key
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass
gpt_api_key = os.environ.get("OPENAI_API_KEY", GPT_API_KEY)

# List available models
if DEBUG:
    models = openai.models.list()
    for model in models:
        print(model.id)

# Initialize ChatGPT client
gpt_client = openai.OpenAI(api_key=gpt_api_key)

# Superloop
msg_history = []
while True:
    
    # Listen for wake word/phrase
    with sd.RawInputStream(
        dtype="int16",
        channels=1,
        callback=callback_record
    ):
        listening_for_ww = True
        if DEBUG:
            print("Listening for keyword...")
    
        # Perform keyword spotting
        while listening_for_ww:
            data = in_q.get()
            if recognizer.AcceptWaveform(data):

                # Perform speech-to-text (STT)
                result = recognizer.Result()
                result_dict = json.loads(result)
                result_text = result_dict.get("text", "")
                if result_text != "":
                    if DEBUG:
                        print(f"Heard: {result_text}")
                    if result_text == WAKE_PHRASE:
                        listening_for_ww = False
                else:
                    if DEBUG:
                        print("No sound detected")

    # Listen for query
    with sd.RawInputStream(
        dtype="int16",
        channels=1,
        callback=callback_record
    ):
        listening_for_query = True
        if DEBUG:
            print("Listening for query...")
    
        # Get text from query
        while listening_for_query:
            data = in_q.get()
            if recognizer.AcceptWaveform(data):

                # Perform speech-to-text (STT)
                result = recognizer.Result()
                result_dict = json.loads(result)
                result_text = result_dict.get("text", "")
                if result_text != "":
                    if DEBUG:
                        print(f"Heard: {result_text}")
                else:
                    if DEBUG:
                        print("No sound detected. Returning to wake word detection.")
                    continue
                listening_for_query = False

    # Perform predetermined actions for particular phrases
    if result_text in ACTION_CLEAR_HISTORY:
        if DEBUG:
            print("ACTION: clearning history")
        msg_history = []
        continue
    if result_text in ACTION_STOP:
        if DEBUG:
            print("ACTION: stop listening")
        continue
    else:
        if DEBUG:
            print("No actions detected. Querying chat backend.")

    # Send text query to LLM
    if DEBUG:
        print(f"Sending: {result_text}")
    