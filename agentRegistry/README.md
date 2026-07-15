# Agent Registry

A local AI agent registry service for discovering, registering, and semantically searching AI agents. Built with FastAPI, Streamlit, SQLite, and Semantic Kernel backed by locally-hosted Ollama models.

## Architecture

```
agentRegistry/
└── src/
    ├── models.py            # Pydantic data models (AgentMetadata, etc.)
    ├── registry.py          # SQLite + Semantic Memory storage backend
    ├── registry_service.py  # FastAPI REST API (port 9001)
    ├── agents.py            # Agent invocation server (port 8000)
    ├── app.py               # Streamlit UI (port 8501)
    ├── health_monitor.py    # Background health checker
    ├── populate_agents.py   # Seed script for sample agents
    ├── agents.json          # Fallback seed data (JSON)
    ├── test_registry.py     # Unit tests
    ├── test_semantic_search.py  # Semantic search integration tests
    └── verify_registry_service.py  # End-to-end API verification
```

### Component Roles

| Component | Purpose | Port |
|---|---|---|
| `registry_service.py` | REST API to list, get, and search agents | 9001 |
| `agents.py` | Hosts the actual LLM agents (Llama Coder, Tech Writer, Task Planner) | 8000 |
| `app.py` | Streamlit dashboard for browsing and registering agents | 8501 |
| `health_monitor.py` | Polls agent server health and updates registry status | — |

## LLM Stack

| Component | Model | Provider |
|---|---|---|
| Chat completions | `llama3.1` | Ollama (local) |
| Semantic embeddings | `nomic-embed-text` | Ollama (local) |
| Orchestration | Semantic Kernel | Microsoft |

All inference runs **locally via Ollama**. No external LLM API keys or cloud endpoints are required.

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
cd agentRegistry/src
pip install -r requirements.txt
```

## Running the Services

Start each service in a separate terminal:

### 1. Agent Invocation Server (LLM agents)
```bash
cd agentRegistry/src
python agents.py
# Runs on http://localhost:8000
```

### 2. Registry REST API
```bash
cd agentRegistry/src
python registry_service.py
# Runs on http://localhost:9001
```

### 3. Streamlit UI
```bash
cd agentRegistry/src
streamlit run app.py
# Opens at http://localhost:8501
```

### 4. Health Monitor (optional)
```bash
cd agentRegistry/src
python health_monitor.py
```

### Seed Sample Agents
```bash
cd agentRegistry/src
python populate_agents.py
```

## REST API Endpoints

Base URL: `http://localhost:9001`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/agents` | List all registered agents |
| GET | `/agents/{agent_id}` | Get agent details by ID |
| GET | `/search?q=<query>` | Semantic search across agents |

### Example Requests

```bash
# List all agents
curl http://localhost:9001/agents

# Semantic search
curl "http://localhost:9001/search?q=python+code+generation"

# Get a specific agent
curl http://localhost:9001/agents/llama-coder-live
```

## Agent Invocation Endpoints

Base URL: `http://localhost:8000`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Agent server health |
| POST | `/agents/llama-coder/invoke` | Run Llama Coder agent |
| POST | `/agents/tech-writer/invoke` | Run Tech Writer agent |
| POST | `/agents/task-planner/invoke` | Run Task Planner agent |

### Example Invocation

```bash
curl -X POST http://localhost:8000/agents/llama-coder/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a Python function to reverse a linked list"}'
```

## Registered Agents

| Agent | Type | Description |
|---|---|---|
| **Llama Coder** | LLM | Writes, debugs, and explains Python code |
| **Tech Writer** | LLM | Creates technical documentation in Markdown |
| **Task Planner** | Multi-agent | Breaks complex goals into actionable steps |
| **Summarizer Agent** | LLM | Summarizes long text documents |
| **Search Agent** | Tool | Web search utility |

## Data Storage

- Agent metadata is persisted to **SQLite** (`agents.db`) in the `src/` directory.
- On first startup, if the database is empty, data is migrated from `agents.json`.
- Semantic embeddings are stored in **volatile in-memory** store (rebuilt each startup).

## Running Tests

```bash
cd agentRegistry/src

# Unit tests (no Ollama required)
python -m pytest test_registry.py -v

# Semantic search tests (requires Ollama running)
python -m pytest test_semantic_search.py -v

# End-to-end API verification
python verify_registry_service.py
```

## Known Gaps & Limitations

- **Ollama required**: All LLM and embedding functionality depends on Ollama running locally. Failures are logged but the app continues without semantic search.
- **Volatile embeddings**: Semantic memory is rebuilt in RAM each restart. Cold-start queries may return empty results until agents are re-embedded.
- **Single-writer registry**: The SQLite store is not safe for concurrent multi-process writes.
- **`test_registry.py` references `InMemoryRegistryStore`** which has been replaced by `SemanticMemoryRegistryStore` — those tests need updating.
- **No authentication**: The REST API and agent endpoints are unauthenticated. Do not expose publicly without adding auth middleware.

## Security Notes

- No API keys or secrets are used or required.
- All traffic is local (`localhost`). Do not expose ports 8000, 8501, or 9001 without a reverse proxy and authentication.
- `agents.db` (SQLite file) is excluded from version control via `.gitignore`.
