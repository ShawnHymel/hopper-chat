"""
ChatGPT API test

From: https://www.youtube.com/watch?v=c-g6epk3fFE

Installation:

    python -m pip install openai
    
Create OpenAI account and set up API billing. Create a new secret key
and copy it. Paste API key into ../../key.txt.
"""

import time
import openai

# Settings
KEY_PATH = "../../key.txt"
MODEL = "gpt-4"

# Load API key
openai.api_key = open(KEY_PATH, 'r').read().strip('\n')

# List available models
models = openai.Model.list()
for model in models['data']:
    print(model['id'])

# Send input prompt to ChatGPT
timestamp = time.time()
msg_history = []
prompt = "How do you pass an array as a pointer to a function in C++?"
msg_history.append({'role': "user", 'content': prompt})
completion = openai.ChatCompletion.create(
    model=MODEL,
    messages=msg_history
)
resp_time = time.time() - timestamp

# Extract text reply and append to message history
reply = completion.choices[0].message.content
msg_history.append({'role': "assistant", 'content': reply})
print(f"Reply: {reply}")

# Print response metrics
print(f"Response time: {resp_time}")
print(f"Token usage: {completion.usage['total_tokens']}")
print()

# Create follow-up question prompt
timestamp = time.time()
prompt = "Please summarize the previous response in 2 sentences."
msg_history.append({'role': "user", 'content': prompt})
completion = openai.ChatCompletion.create(
    model=MODEL,
    messages=msg_history
)
resp_time = time.time() - timestamp

# Extract text reply and append to message history
reply = completion.choices[0].message.content
msg_history.append({'role': "assistant", 'content': reply})
print(f"Reply: {reply}")

# Print response metrics
print(f"Response time: {resp_time}")
print(f"Token usage: {completion.usage['total_tokens']}")
print()
