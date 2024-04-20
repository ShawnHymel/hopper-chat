"""
ChatGPT API test

From: https://www.youtube.com/watch?v=c-g6epk3fFE

Installation:

    python -m pip install openai
    
Create OpenAI account and set up API billing. Create a new secret key
and copy it. Paste API key into .env or set it for a session via:

    export OPENAI_API_KEY=my_open_ai_key
"""

import os
import time

import openai

# Settings
GPT_API_KEY = "" # Leave blank to load from OPENAI_API_KEY environment variable
MODEL = "gpt-3.5-turbo"

# Load ChatGPT API key
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass
gpt_api_key = os.environ.get("OPENAI_API_KEY", GPT_API_KEY)

# List available models
models = openai.models.list()
for model in models:
    print(model.id)

# Initialize ChatGPT client
gpt_client = openai.OpenAI(api_key=gpt_api_key)

# Send input prompt to ChatGPT
timestamp = time.time()
msg_history = []
prompt = "How do you pass an array as a pointer to a function in C++?"
msg_history.append({'role': "user", 'content': prompt})
completion = gpt_client.chat.completions.create(
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
print(f"Token usage: {completion.usage.total_tokens}")
print()

# Create follow-up question prompt
timestamp = time.time()
prompt = "Please summarize the previous response in 2 sentences or fewer."
msg_history.append({'role': "user", 'content': prompt})
completion = gpt_client.chat.completions.create(
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
print(f"Token usage: {completion.usage.total_tokens}")
print()
