#!/usr/bin/env python3

import time
import io
import queue
import threading
import json
from collections import deque
from configparser import ConfigParser
import argparse

import resampy
import requests
import numpy as np
from scipy.io import wavfile
import sounddevice as sd
import regex
from vosk import Model, KaldiRecognizer, SetLogLevel
import ollama

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

def parse_config_list(list_as_string):
    return [element.strip().strip('"') for element in list_as_string.strip().split(',')]

def record_callback(in_data, frames, time, status, q):
    """
    Fill global input queue with audio data
    """
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(in_data))

def wait_for_stt(q, recognizer):
    """
    Wait for STT to hear something and return the text
    """

    # Listen for wake word/phrase
    with sd.RawInputStream(
        dtype="int16",
        channels=1,
        callback=lambda in_data, frames, time, status: record_callback(in_data, frames, time, status, q)
    ):
        if DEBUG:
            print("Listening...")

        # Perform keyword spotting
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):

                # Perform speech-to-text (STT)
                result = recognizer.Result()
                result_dict = json.loads(result)
                result_text = result_dict.get("text", "")

                return result_text

def play_msg(msg, tts_q, sound_semaphore):
    """
    Parse message into sentences and play them. This is blocking until sound is done playing.
    """

    # Only do this if TTS is enabled
    if TTS_ENABLE:

        # Create regex pattern for parsing sentences
        pattern = regex.compile(SENTENCE_REGEX, flags=regex.VERSION1)

        # Parse message into sentences and send them to the TTS thread
        msg = msg.replace("\n", " ")
        sentences = pattern.split(msg)
        for sentence in sentences:
            tts_q.put(sentence)
        tts_q.put(None)

        # Wait for sound to stop
        sound_semaphore.acquire(blocking=True)

def query_chat(chat_client, msg, msg_history, q):
    """
    Send message to chat backend (Ollama) and return response text
    """

    # Create regex pattern for parsing sentences
    pattern = regex.compile(SENTENCE_REGEX, flags=regex.VERSION1)

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

    # Parse reply for sentences
    reply = ""
    sentences = deque([""])
    for chunk in stream:

        # Get the next string part from the stream
        part = chunk["message"]["content"]
        reply += part

        # Parse sentences and put them into the queue
        tmp_str = sentences[0] + part
        tmp_sentences = pattern.split(tmp_str)
        sentences[0] = tmp_sentences[0]
        if len(tmp_sentences) > 1:
            ret_sentence = sentences.popleft()
            ret_sentence = ret_sentence.replace("\n", " ")
            if TTS_ENABLE:
                q.put(ret_sentence)
            if DEBUG:
                print(f"RECV: {ret_sentence}")
            for tmp in tmp_sentences[1:]:
                sentences.append(tmp)

    # All done. Add final sentence and None delimiter.
    if TTS_ENABLE:
        q.put(sentences[0])
        q.put(None)
    if DEBUG:
        print(f"RECV: {sentences[0]}")

    # Add reply to message history
    msg_history.push({
        "role": "assistant",
        "content": reply,
    })

    # Print the chat
    if DEBUG:
        print(f"Whole reply: {reply}")

def start_chat_thread(in_q, tts_q, sound_semaphore):
    """
    Main chat thread: performs STT and sends queries to chat server.
    """

    # Get sample rate
    device_info = sd.query_devices(sd.default.device[0], "input")
    sample_rate = int(device_info["default_samplerate"])

    # Display input device info
    if DEBUG:
        print(f"Input device info: {json.dumps(device_info, indent=2)}")

    # Load notification sound into memory
    if NOTIFICATION_PATH:
        notification_sample_rate, notification_wav = wavfile.read(NOTIFICATION_PATH)
        if notification_wav.dtype == np.int16:
            notification_wav = notification_wav.astype(np.float32) / np.iinfo(np.int16).max
        notification_wav = np.array(notification_wav) * AUDIO_OUTPUT_VOLUME
        notification_wav = resampy.resample(
            notification_wav,
            notification_sample_rate,
            AUDIO_OUTPUT_SAMPLE_RATE
        )

    # Build the model
    model = Model(lang="en-us")
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(False)

    # Initialize Ollama client
    chat_client = ollama.Client(host=OLLAMA_SERVER_URL)

    # Main chat loop
    msg_history = FixedSizeQueue(CHAT_MAX_HISTORY)
    while True:

        # Listen for wake word or phrase
        timestamp = time.time()
        text = wait_for_stt(in_q, recognizer)
        if DEBUG:
            print(f"Heard: {text}")
        if text in WAKE_PHRASES:
            if DEBUG:
                print(f"Wake phrase detected.")
                print(f"STT time: {round(time.time() - timestamp, 1)} sec")
        else:
            continue

        # Play notification sound
        if NOTIFICATION_PATH:
            sd.play(
                notification_wav,
                samplerate=AUDIO_OUTPUT_SAMPLE_RATE,
                device=AUDIO_OUTPUT_INDEX
            )
            sd.wait()

        # Listen for query
        timestamp = time.time()
        text = wait_for_stt(in_q, recognizer)
        if text != "":
            if DEBUG:
                print(f"Heard: {text}")
                print(f"STT time: {round(time.time() - timestamp, 1)} sec")
        else:
            if DEBUG:
                print("No sound detected. Returning to wake word detection.")
            continue

        # Perform actions for particular phrases
        if text in ACTION_CLEAR_HISTORY:
            if DEBUG:
                print("ACTION: clearing history")
            msg_history = FixedSizeQueue(CHAT_MAX_HISTORY)
            play_msg(
                "OK. My chat history is cleared.",
                tts_q,
                sound_semaphore
            )
            continue
        elif text in ACTION_STOP:
            if DEBUG:
                print("ACTION: stop listening")
            continue

        # Default action: query chat backend
        else:

            # Start wall clock timer
            wall_timestamp = time.time()

            # Send request with limited reply length. Sentences are added to TTS queue.
            if CHAT_MAX_REPLY_SENTENCES > 0:
                msg = text + \
                    f". Your response must be {CHAT_MAX_REPLY_SENTENCES} sentences or fewer."
            else:
                msg = text
            if DEBUG:
                print(f"Sending: {msg}")
            timestamp = time.time()
            query_chat(
                chat_client,
                msg,
                msg_history,
                tts_q
            )
            if DEBUG:
                print(f"LLM time: {round(time.time() - timestamp, 1)} sec")

            # Wait for TTS thread to finish
            if TTS_ENABLE:
                sound_semaphore.acquire(blocking=True)
            if DEBUG:
                print(f"Full query complete in {round(time.time() - wall_timestamp, 1)} sec")

def start_tts_thread(tts_q, sound_q):
    """
    Wait for message in queue, send it to TTS server, then queue up sound to be played.
    """
    while True:
        while not tts_q.empty():

            # Get message from queue
            msg = tts_q.get()
            if msg is None:
                sound_q.put(None)
                continue

            # Send message to TTS server
            params = {"text": msg}
            resp = requests.get(PIPER_URL, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to get response from TTS server: {resp.status_code}")

            # Convert response to NumPy array and convert to float
            sample_rate, wav = wavfile.read(io.BytesIO(resp.content))
            if wav.dtype == np.int16:
                wav = wav.astype(np.float32) / np.iinfo(np.int16).max

            # Adjust volume and resample
            wav = np.array(wav) * AUDIO_OUTPUT_VOLUME
            if sample_rate != AUDIO_OUTPUT_SAMPLE_RATE:
                wav = resampy.resample(
                    wav,
                    sample_rate,
                    AUDIO_OUTPUT_SAMPLE_RATE
                )

            # Put sound in queue
            sound_q.put(wav)
        
        time.sleep(0.1)

def digital_write(ctrl, pin, value):
    """
    Controls a pin on or off. `ctrl` is the GPIO package or control object.
    """
    if pin != -1:
        if platform == "pi":
            ctrl.value = value
        elif platform == "jetson":
            ctrl.output(pin, value)

def start_sound_thread(sound_q, sound_semaphore, servo_notify):
    """
    Wait for sound binary in queue, then play it through the speaker.
    """
    while True:
        while not sound_q.empty():
            wav = sound_q.get()
            if wav is None:
                sound_semaphore.release()
                continue
            digital_write(servo_notify, SERVO_NOTIFY_PIN, 1)
            sd.play(wav, samplerate=AUDIO_OUTPUT_SAMPLE_RATE, device=AUDIO_OUTPUT_INDEX)
            sd.wait()
            digital_write(servo_notify, SERVO_NOTIFY_PIN, 0)
        time.sleep(0.1)

#---------------------------------------------------------------------------------------------------
# Main

def main():

    # Servo notify pin
    servo_notify = None
    if platform == "pi" and SERVO_NOTIFY_PIN != -1:
        import gpiozero
        servo_notify = gpiozero.LED(SERVO_NOTIFY_PIN)
    elif platform == "jetson" and SERVO_NOTIFY_PIN != -1:
        import Jetson.GPIO
        Jetson.GPIO.setmode(Jetson.GPIO.BCM)
        Jetson.GPIO.setup(SERVO_NOTIFY_PIN, Jetson.GPIO.OUT)
        servo_notify = Jetson.GPIO

    try:

        # Set Vosk logging
        if not DEBUG:
            SetLogLevel(-1)

        # Set the input and output devices
        sd.default.device = [AUDIO_INPUT_INDEX, AUDIO_OUTPUT_INDEX]

        # Set up queue and callback
        in_q = queue.Queue()

        # Semaphore used to notify main thread when TTS is done playing
        sound_semaphore = threading.BoundedSemaphore(1)
        sound_semaphore.acquire()

        # Start TTS and sound threads
        tts_q = queue.Queue()
        if TTS_ENABLE:
            sound_q = queue.Queue()
            tts_thread = threading.Thread(
                target=start_tts_thread, 
                args=(tts_q, sound_q)
            )
            tts_thread.start()
            sound_thread = threading.Thread(
                target=start_sound_thread, 
                args=(sound_q, sound_semaphore, servo_notify)
            )
            sound_thread.start()

        # Start STT and chat thread
        chat_thread = threading.Thread(
            target=start_chat_thread, 
            args=(in_q, tts_q, sound_semaphore)
        )
        chat_thread.start()

        # Keep main thread running
        while True:
            time.sleep(1.0)

    # Make sure to free up GPIO resources
    except KeyboardInterrupt:
        print("Main program stopped")
    finally:
        servo_notify.close()

#---------------------------------------------------------------------------------------------------
# Settings

# Interface
WELCOME_MSG = """
    __ __                         _______        __ 
   / // /__  ___  ___  ___ ____  / ___/ /  ___ _/ /_
  / _  / _ \/ _ \/ _ \/ -_) __/ / /__/ _ \/ _ `/ __/
 /__/_/\___/ .__/ .__/\__/_/    \___/_//_/\_,_/\__/ 
          /_/  /_/                                  


Welcome to Hopper Chat! Say the wake phrase "Hey, Hopper" and ask a question.
Press 'ctrl+c' to exit.
"""

# Parsing sentences
SENTENCE_REGEX = r"(?<=\.|\?|\!|\:|\#|\.\.\.|\n|\n\n)\s+(?=[A-Z0-9]|\Z)"

# Parse configuration file
PARSER = argparse.ArgumentParser(description="Hopper Chat")
PARSER.add_argument(
    "--config",
    "-c",
    type=str,
    default="hopper-chat.conf",
    help="Path to the configuration file"
)
ARGS = PARSER.parse_args()
CONFIG_FILE_PATH = ARGS.config

# Parse config file
config = ConfigParser(inline_comment_prefixes="#")
config.read(CONFIG_FILE_PATH)

# Assign settings
DEBUG = config.getboolean("settings", "DEBUG", fallback=False)
AUDIO_INPUT_INDEX = config.getint("settings", "AUDIO_INPUT_INDEX", fallback=0)
AUDIO_OUTPUT_INDEX = config.getint("settings", "AUDIO_OUTPUT_INDEX", fallback=1)
AUDIO_OUTPUT_VOLUME = config.getfloat("settings", "AUDIO_OUTPUT_VOLUME", fallback=1.0)
AUDIO_OUTPUT_SAMPLE_RATE = config.getint("settings", "AUDIO_OUTPUT_SAMPLE_RATE", fallback=48000)
NOTIFICATION_PATH = config.get(
    "settings",
    "NOTIFICATION_PATH",
    fallback="./sounds/cowbell.wav"
).strip('"')
SERVER_IP = config.get("settings", "SERVER_IP", fallback="127.0.0.1").strip('"')
CHAT_MAX_HISTORY = config.getint("settings", "CHAT_MAX_HISTORY", fallback=20)
CHAT_MAX_REPLY_SENTENCES = config.getint("settings", "CHAT_MAX_REPLY_SENTENCES", fallback=0)
OLLAMA_SERVER_PORT = config.getint("settings", "OLLAMA_SERVER_PORT", fallback=10802)
OLLAMA_MODEL = config.get("settings", "OLLAMA_MODEL", fallback="llama3:8b").strip('"')
TTS_ENABLE = config.getboolean("settings", "TTS_ENABLE", fallback=True)
PIPER_SERVER_PORT = config.getint("settings", "PIPER_SERVER_PORT", fallback=10803)
TTS_MODEL_SAMPLE_RATE = config.getint("settings", "TTS_MODEL_SAMPLE_RATE", fallback=22050)

# Parse the lists
WAKE_PHRASES = parse_config_list(
    config.get("settings", "WAKE_PHRASES", fallback=["hey hopper"])
)
ACTION_CLEAR_HISTORY = parse_config_list(
    config.get("settings", "ACTION_CLEAR_HISTORY", fallback=["clear chat history"])
)
ACTION_STOP = parse_config_list(
    config.get("settings", "ACTION_STOP", fallback=["nevermind"])
)
SERVO_NOTIFY_PIN = config.getint("settings", "SERVO_NOTIFY_PIN", fallback=-1)

# Construct server URL strings
OLLAMA_SERVER_URL = f"http://{SERVER_IP}:{OLLAMA_SERVER_PORT}"
PIPER_URL = f"http://{SERVER_IP}:{PIPER_SERVER_PORT}"

# Import GPIO library depending on platform
platform = "other"
try:
    with open("/proc/device-tree/model", "r") as f:
        hw = f.read().strip()
        if "Raspberry Pi" in hw:
            platform = "pi"
        elif "Jetson" in hw:
            platform = "jetson"

except FileNotFoundError:
    pass

#---------------------------------------------------------------------------------------------------
# Entrypoint

if __name__ == "__main__":
    print(WELCOME_MSG)
    print(f"TTS: {TTS_ENABLE}")
    print(f"Servo notify pin: {SERVO_NOTIFY_PIN}")
    print(f"Platform: {platform}")
    main()
