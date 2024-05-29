import regex
from ollama import Client

# Settings
chat_client = Client(host="http://0.0.0.0:10802")
prompt = "tell me a joke"

def send(chat):

  # Send message to LLM server
  messages = [{
     'role': 'user',
      'content': chat,
  }]
  response = chat_client.chat(model='llama3:8b', 
    messages=messages,
    stream=False,
  )

  # Calculate tokens per second
  tokens = response["eval_count"]
  eval_time = response["eval_duration"] / 10**9
  tokens_per_second = tokens / eval_time

  # Print metrics
  print(f"Response: {response['message']['content']}")
  print(f"Tokens: {tokens}")
  print(f"Eval time (sec): {eval_time}")
  print(f"Tokens per second: {tokens_per_second}")

def main():
   send(prompt)

if __name__ == "__main__":
    main()