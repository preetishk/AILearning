import requests
import os


# Ollama defaults to http://localhost:11434
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')


# Use OpenAI-compatible chat completions endpoint offered by Ollama
# This function accepts a list of messages: [{'role':'user','content':'...'}, ...]


def generate_reply(messages, model_name='llama3.1'):
    payload = {
    'model': model_name,
    'messages': messages,
    # you can tune temperature/streaming here if desired
    'temperature': 0.2,
    'max_tokens': 512
    }
    url = f"{OLLAMA_HOST}/v1/chat/completions"
    r = requests.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    # OpenAI-compatible response structure: choices[0].message.content
    return data['choices'][0]['message']['content']