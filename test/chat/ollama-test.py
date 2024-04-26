from ollama import Client

chat_client = Client(host="http://10.0.0.143:10802")

messages = []

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
  for chunk in stream:
    part = chunk['message']['content']
    print(part, end='', flush=True)
    response = response + part

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