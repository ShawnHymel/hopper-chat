import regex
from ollama import Client

# Settings
chat_client = Client(host="http://0.0.0.0:10802")
prompt = "tell me a joke"

# Global message history
messages = []

def send(chat):
  
  global messages

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
    response += part
    print(f"{chunk}")

  print(f"Response: {response}")

  messages.append(
    {
      'role': 'assistant',
      'content': response,
    }
  )

  print("")

def main():
   send(prompt)

if __name__ == "__main__":
    main()