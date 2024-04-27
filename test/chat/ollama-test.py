import regex
from ollama import Client

chat_client = Client(host="http://10.0.0.100:10802")
SENTENCE_REGEX = r"(?<=\.|\?|\!|\:|\;|\.\.\.)\s+(?=[A-Z0-9]|\Z)"

messages = []

# Create regex pattern
pattern = regex.compile(SENTENCE_REGEX, flags=regex.VERSION1)

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
    response += part

    # Try to parse into sentences
    sentences = pattern.split(response)

    # TODO: Figure out how to extract one part at a time
    if len(sentences) > 1:
      print(sentences[-2])

  print(f"Response: {response}")

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