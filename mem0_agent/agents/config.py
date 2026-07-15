import os

OLLAMA_HOST   = os.getenv("OLLAMA_HOST",   "http://localhost:11434")
CHAT_MODEL    = os.getenv("CHAT_MODEL",    "llama3.1")
EMBED_MODEL   = os.getenv("EMBED_MODEL",   "nomic-embed-text:latest")
EMBED_DIMS    = int(os.getenv("EMBED_DIMS", "768"))
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", "./db/shared_memory_v4")
