from collections import deque

import regex
from ollama import Client

# Settings
CHAT_MAX_HISTORY = 20           # Number of prompts and replies to remember
OLLAMA_MODEL = "llama3:8b"      # Must match what the server is running

# New settings
SENTENCE_REGEX = r"(?<=\.|\?|\!|\:|\;|\.\.\.|\n|\n\n)\s+(?=[A-Z0-9]|\Z)"

chat_client = Client(host="http://10.0.0.100:10802")
messages = []

# Create regex pattern
pattern = regex.compile(SENTENCE_REGEX, flags=regex.VERSION1)

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

def query_chat(msg):

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
    
    # Parse reply for sentences
    reply = ""
    sentences = deque([""])
    for chunk in stream:

        # Get the next string part from the stream
        part = chunk["message"]["content"]
        reply = reply + part

        # Parse sentences
        tmp_str = sentences[0] + part
        tmp_sentences = pattern.split(tmp_str)
        sentences[0] = tmp_sentences[0]
        if len(tmp_sentences) > 1:
          ret_sentence = sentences.popleft()
          ret_sentence = ret_sentence.replace("\n", " ")
          print(f"RETURN: {ret_sentence}")
          for tmp in tmp_sentences[1:]:
            sentences.append(tmp)

    # All done. Print final sentence (or whatever is left)
    print(f"RETURN: {sentences[0]}")
        
    # TEST: print full reply, parsed.
    reply = reply.replace("\n", " ")
    print(f"ANS: {pattern.split(reply)}")

# Main
msg_history = FixedSizeQueue(CHAT_MAX_HISTORY)
chat = "tell me a joke"
query_chat(chat)