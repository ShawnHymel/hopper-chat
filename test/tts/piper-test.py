"""

Installation:

    python -m pip install piper-tts
    
From: https://github.com/rhasppy/piper/tree/master

Available models: https://huggingface.co/rhasspy/piper-voices/tree/main

"""

import json
import subprocess
import time

TEXT = "In a hole in the ground there lived a hobbit. Not a nasty, " \
    "dirty, wet hole, filled with the ends of worms and an oozy " \
    "smell, nor yet a dry, bare, sandy hole with nothing in it to " \
    "sit down on or to eat: it was a hobbit-hole, and that means " \
    "comfort."
MODEL = "en_US-lessac-medium"

cmd_tts = f"piper --model {MODEL} --output-raw"
cmd_play = "aplay -r 22050 -f S16_LE -t raw -"

# Convert speech and play
timestamp = time.time()
p1 = subprocess.Popen(
    ["echo", f"{TEXT}"], 
    stdout=subprocess.PIPE
)
p2 = subprocess.Popen(
    cmd_tts.split(), 
    stdin=p1.stdout,
    stdout=subprocess.PIPE
)
p3 = subprocess.Popen(
    cmd_play.split(),
    stdin=p2.stdout
)
p3.wait()
print(f"TTS time: {time.time() - timestamp}")
