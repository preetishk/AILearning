# mem0 Multi-Agent System

A local multi-agent pipeline that uses **mem0** for persistent memory across agent interactions. Three specialised agents — Researcher, Summarizer, and Humanizer — collaborate through a shared Qdrant vector store, all running locally via Ollama.

## Architecture

```
mem0_agent/
├── main.py                  # Interactive CLI entry point
├── test_run.py              # Non-interactive test runner
└── agents/
    ├── base_agent.py        # Base class: memory + LLM client setup
    ├── orchestrator.py      # Coordinates the 3-agent pipeline
    └── worker_agents.py     # ResearchAgent, SummarizerAgent, HumanizeAgent
```

### Agent Pipeline

```
User Input
    │
    ▼
[Orchestrator]
    │
    ├─► ResearchAgent   → detailed facts on the topic
    │
    ├─► SummarizerAgent → condenses research into bullet points
    │
    └─► HumanizeAgent   → rewrites summary in a friendly, readable tone
                              │
                              ▼
                        Final Response
```

All three agents share a **single mem0 Memory instance** (`shared_memory_v4`) so context flows between them automatically.

## LLM Stack

| Component | Model | Provider |
|---|---|---|
| Chat completions | `llama3.1` | Ollama (local) |
| Semantic embeddings | `nomic-embed-text:latest` | Ollama (local) |
| Memory framework | mem0 | Open-source |
| Vector store | Qdrant | Local (embedded) |

All inference runs **fully locally**. No cloud API keys or external services required.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running at `http://localhost:11434`
- Required Ollama models pulled:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

## Installation

```bash
cd mem0_agent
pip install -r requirements.txt
```

## Configuration

All settings default to local Ollama with no changes needed. To override, copy `.env.example` to `.env` and edit:

```bash
copy .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `CHAT_MODEL` | `llama3.1` | LLM for chat completions |
| `EMBED_MODEL` | `nomic-embed-text:latest` | Embedding model |
| `EMBED_DIMS` | `768` | Embedding dimensions (must match `db/` data) |
| `MEMORY_DB_PATH` | `./db/shared_memory_v4` | Qdrant vector store path |

## Usage

### Interactive CLI
```bash
cd mem0_agent
python main.py
```
Type a topic and press Enter. Type `exit` to quit.

```
You: Tell me about Black Holes
Agent System: [Humanized response here]

You: What are the risks of it?   ← uses memory from prior turn
```

### Non-Interactive Test Run
```bash
cd mem0_agent
python test_run.py
```
Runs two pre-defined queries (initial topic + follow-up memory recall) and prints results.

## Memory & Data Storage

- Memory is persisted to **Qdrant** vector store at `./db/shared_memory_v4/` (768-dim vectors, `nomic-embed-text`).
- Each agent lookup retrieves relevant past context before calling the LLM.
- Each agent response is stored back into shared memory after generation.
- The `db/` directory is excluded from version control (see `.gitignore`).

> Earlier `db/` directories (`shared_memory`, `shared_memory_v2`, `shared_memory_v3`, `Researcher/`, `Summarizer/`) used 1536-dim vectors and are **no longer active**. They can be deleted safely.

## Known Gaps & Limitations

| Gap | Notes |
|---|---|
| No logging setup | Debug output relies on `print()` statements |
| Volatile memory on schema change | If the embedding model changes, old `db/` data is incompatible and must be deleted |
| No unit tests | `test_run.py` is an integration script, not a test suite |

## Security Notes

- `api_key="ollama"` in `base_agent.py` is a **placeholder** required by the OpenAI client library — it is not a real key and is never sent to a remote service.
- No HP credentials, client IDs, secrets, or internal URLs are present in this codebase.
- `output.txt` and `output_v2.txt` (local test logs) are excluded from version control via `.gitignore` because they contain local file paths.
- The `db/` directory is excluded for the same reason and because it is runtime-generated data.
