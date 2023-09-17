"""
Vosk test

From: https://singerlinks.com/2022/03/how-to-convert-microphone-speech-to-text-using-python-and-vosk/

Installation:

	python -m pip install vosk sounddevice

References:
 - https://alphacephei.com
"""

#!/usr/bin/env python3

import queue
import time
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import sys
import json

'''This script processes audio input from the microphone and displays the transcribed text.'''
    
# list all audio devices known to your system
print("Display input/output devices")
print(sd.query_devices())


# get the samplerate - this is needed by the Kaldi recognizer
device_info = sd.query_devices(sd.default.device[0], 'input')
samplerate = int(device_info['default_samplerate'])

# display the default input device
print("===> Initial Default Device Number:{} Description: {}".format(sd.default.device[0], device_info))

# setup queue and callback function
q = queue.Queue()

def recordCallback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))
    
# build the model and recognizer objects.
print("===> Build the model and recognizer objects.  This will take a few minutes.")
model = Model(lang="en-us")
recognizer = KaldiRecognizer(model, samplerate)
recognizer.SetWords(False)

# Try opening and closing the stream
print("===> Begin recording. Press Ctrl+C to stop the recording ")
try:
    with sd.RawInputStream(dtype='int16',
                           channels=1,
                           callback=recordCallback):
        while True:
            data = q.get()        
            if recognizer.AcceptWaveform(data):
                
                # Perform STT
                timestamp_stt = time.time()
                recognizerResult = recognizer.Result()
                print(f"STT time: {time.time() - timestamp_stt}")
                
                # convert the recognizerResult string into a dictionary  
                resultDict = json.loads(recognizerResult)
                if not resultDict.get("text", "") == "":
                    print(recognizerResult)
                else:
                    print("no input sound")

except KeyboardInterrupt:
    print('===> Finished Recording')
except Exception as e:
    print(str(e))
