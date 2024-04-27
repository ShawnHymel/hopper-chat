import re
from ollama import Client

chat_client = Client(host="http://10.0.0.100:10802")
SENTENCE_REGEX = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!\:\;)\s'

messages = []

def split_sentences(str):
  start_idx = 0
  for i, char in enumerate(str):
    if char in SENTENCE_DELIMITERS:
      sentence = str[start_idx:i + 1].strip()
      print(sentence)
      start_idx = i + 1

def send(chat):
  messages.append(
    {
      'role': 'user',
      'content': chat,
    }
  )
  stream = chat_client.chat(model='llama3:8b', 
    messages=messages,
    stream=True,
  )

  response = ""
  sentence = ""
  for chunk in stream:
    part = chunk['message']['content']

    # Try to parse into a sentence
    sentence += part
    print(sentence)


    response += part

  messages.append(
    {
      'role': 'assistant',
      'content': response,
    }
  )

  print("")

while True:
    chat = input(">>> ")

    if chat == "/exit":
        break
    elif len(chat) > 0:
        send(chat)