# ChatGPT Replica — Local Chat PoC

A lightweight, local ChatGPT-style web app powered by **Ollama** and **ChromaDB**. Supports multiple independent chat pages with persistent conversation history — no cloud APIs or accounts required.

---

## Architecture

```
chatGptReplica/
├── server.py           # Flask backend — REST API + static file serving
├── ollama_client.py    # Ollama LLM integration (OpenAI-compatible endpoint)
├── persistence.py      # ChromaDB helpers (create, save, list, delete pages)
├── simple_inspect.py   # CLI utility to inspect stored ChromaDB data
├── ui/
│   └── Index.html      # Single-page vanilla JS frontend
└── data/               # ChromaDB persistent storage (auto-created, git-ignored)
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | |
| [Ollama](https://ollama.com) | Running locally on `http://localhost:11434` |
| `llama3.1` model pulled | `ollama pull llama3.1` |

---

## Setup

**1. Install dependencies**
```bash
pip install flask flask-cors chromadb requests
```

**2. Start Ollama** (if not already running)
```bash
ollama serve
ollama pull llama3.1
```

**3. Run the server**
```bash
python server.py
```

**4. Open in browser**
```
http://127.0.0.1:5000
```

---

## Features

- **Multi-page chat** — create, rename, and delete independent conversation pages
- **Persistent history** — conversations survive server restarts (stored in ChromaDB)
- **Context-aware replies** — last 12 messages sent as context to the model
- **Feedback** — attach a rating/comment to any conversation
- **Zero external dependencies** — fully local, no API keys needed

---

## Configuration

The Ollama host can be overridden via environment variable:

```bash
OLLAMA_HOST=http://192.168.1.10:11434 python server.py
```

To switch models, edit `model_name` in `server.py`:
```python
resp_text = generate_reply(messages, model_name='llama3.1')  # change here
```

---

## Inspecting Stored Data

Use the built-in inspector to view all persisted conversations:

```bash
python simple_inspect.py
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/pages` | List all chat pages |
| `POST` | `/api/pages` | Create a new page `{"title": "..."}` |
| `DELETE` | `/api/pages/<id>` | Delete a page and its history |
| `GET` | `/api/pages/<id>/messages` | Get last 40 messages |
| `POST` | `/api/pages/<id>/messages` | Send a message, get AI reply |
| `POST` | `/api/pages/<id>/feedback` | Submit feedback `{"rating": 5, "comment": "..."}` |
