from collections import deque
import json

import ollama

# Settings
MODEL = "allenporter/xlam:1b"
OLLAMA_HOST = "http://localhost:11434"
PREAMBLE = "You are a helpful assistant that turns an LED on or off."
MAX_MESSAGES = 5

# Define tools for the model to use (i.e. functions)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "led_write",
            "description": "Turn the LED on or off",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "number",
                        "description": "The value to write to the LED pin. 0 for " \
                            "off, 1 for on",
                    },
                },
                "required": ["value"],
            },
        }
    }
]

# -----------------------------------------------------------------------------
# Classes

class FixedSizeQueue:
    """
    Fixed size array with FIFO and optional preamble.
    """
    def __init__(self, max_size, preamble=None):
        self.queue = deque(maxlen=max_size)
        self.preamble = {
            "role": "system",
            "content": preamble
        }

    def push(self, item):
        self.queue.append(item)

    def get(self):
        if self.preamble is None:
            return list(self.queue)
        else:
            return [self.preamble] + list(self.queue)

# -----------------------------------------------------------------------------
# Functions

def led_write(value):
    """
    Simulate turning an LED on or off
    """

    print(f"LED is now {'off' if value == 0 else 'on'}")

def send(chat, msg_history, client, model, tools):
    """
    Send a message to the LLM server and print the response.
    """

    # Add user message to the conversation history
    msg_history.push({
        "role": "user",
        "content": chat
    })

    # Send message to LLM server
    response = client.chat(
        model=model,
        messages=msg_history.get(),
        tools=tools,
        stream=False
    )

    # Add the model's response to the conversation history
    msg_history.push({
        "role": "assistant",
        "content": response["message"]["content"]
    })

    # Check if the model used the provided function
    if not response["message"].get("tool_calls"):
        print("The model didn't use the function. Its response was:")
        print(response["message"]["content"])
        return
    else:
        print(f"Tool used. Response: {response['message']}")
        for tool in response["message"]["tool_calls"]:
            print(tool["function"]["name"])
            print(tool["function"]["arguments"])

# -----------------------------------------------------------------------------
# Main

if __name__ == "__main__":

    # Configure chat history and connect to the LLM server
    msg_history = FixedSizeQueue(MAX_MESSAGES, PREAMBLE)
    client = ollama.Client(host=OLLAMA_HOST)

    while True:
        user_input = input("> ")
        if user_input in ["/exit", "/quit", "/bye"]:
            break
        send(user_input, msg_history, client, MODEL, TOOLS)
