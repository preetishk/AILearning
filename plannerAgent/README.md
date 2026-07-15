# AI Planner Agent

A FastAPI microservice that decomposes a natural-language task into an ordered execution plan, assigning each step to a registered AI agent. It combines live agent discovery (via the Agent Registry), optional RAG context, and local LLM reasoning (Ollama / Llama 3.1) through Microsoft Semantic Kernel.

## Architecture

```
plannerAgent/
└── src/
    ├── config.py               # Pydantic-settings config (env-driven)
    ├── main.py                 # FastAPI app + /plan endpoint (port 9002)
    ├── models.py               # Pydantic models (PlanningRequest, ExecutionPlan, …)
    ├── clients/
    │   ├── ollama_client.py    # Semantic Kernel wrapper for Llama 3.1
    │   ├── registry_client.py  # HTTP client → Agent Registry (port 9001)
    │   └── rag_client.py       # HTTP client → RAG service (port 8080)
    └── planner/
        ├── planner.py          # Core planning logic + retry loop
        ├── prompts.py          # Prompt template builder
        └── parsers.py          # JSON extraction + plan validation
```

### Planning Pipeline

```
POST /plan
    │
    ├─ 1. Health-check Ollama
    ├─ 2. Fetch available agents  ← Agent Registry (:9001)
    ├─ 3. Query RAG knowledge base ← RAG service (:8080)  [optional]
    ├─ 4. Build planning prompt
    └─ 5. LLM call → parse → validate  (retried up to PLANNING_RETRIES times)
               │
               ▼
         ExecutionPlan (JSON)
```

## LLM Stack

| Component | Model | Provider |
|---|---|---|
| Chat completions | `llama3.1` | Ollama (local) via Semantic Kernel |
| Orchestration framework | Semantic Kernel | Microsoft |

All inference runs **locally**. No cloud API keys required.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) running at `http://localhost:11434`
- `llama3.1` pulled: `ollama pull llama3.1`
- **Agent Registry** running on port `9001` (see `agentRegistry/`)
- **RAG service** on port `8080` is optional — the planner degrades gracefully without it

## Installation

```bash
cd plannerAgent
pip install -r requirements.txt
```

## Configuration

All defaults work out of the box. To override, create a `.env` file in `plannerAgent/src/`:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | LLM model for planning |
| `OLLAMA_TEMPERATURE` | `0.3` | Sampling temperature |
| `OLLAMA_TOP_P` | `0.9` | Top-p sampling |
| `REGISTRY_BASE_URL` | `http://127.0.0.1:9001` | Agent Registry URL |
| `REGISTRY_TIMEOUT` | `5` | Registry HTTP timeout (s) |
| `RAG_BASE_URL` | `http://127.0.0.1:8080` | RAG service URL |
| `RAG_TOP_K` | `5` | Documents to retrieve |
| `RAG_SIMILARITY_THRESHOLD` | `0.7` | Min relevance score |
| `PLANNING_MAX_TOKENS` | `2048` | Max tokens per LLM call |
| `PLANNING_RETRIES` | `3` | Max LLM retry attempts |
| `PLANNING_TIMEOUT` | `30` | Overall planning timeout (s) |
| `PLANNER_AGENT_ID` | `task-planner-live` | This agent's own registry ID (excluded from plans) |

## Running the Service

```bash
cd plannerAgent/src
python main.py
# Runs on http://127.0.0.1:9002
```

Ensure the **Agent Registry** is running first:

```bash
# Terminal 1
cd agentRegistry/src && python registry_service.py   # port 9001

# Terminal 2
cd plannerAgent/src && python main.py                # port 9002
```

## API

Base URL: `http://127.0.0.1:9002`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health check |
| POST | `/plan` | Generate an execution plan |

### POST `/plan`

**Request body:**

```json
{
  "task": "Research the latest AI trends and write a blog post about them",
  "context": "Target audience is developers",
  "constraints": {},
  "user_id": "user_1"
}
```

**Response:**

```json
{
  "steps": [
    { "step": "Research AI trends", "agent": "llama-coder-live", "dependencies": [] },
    { "step": "Write blog post", "agent": "tech-writer-live", "dependencies": [0] }
  ],
  "reasoning": "...",
  "confidence": 0.95,
  "created_at": "2026-07-15T10:00:00"
}
```

### Confidence Score

The `confidence` field is a heuristic (0–1):
- **0.7 × (valid agent assignments / total steps)** — rewards correct agent routing
- **+0.25** base
- **+0.05** if any steps have dependencies (rewards reasoning about order)

### GET `/health`

```json
{ "status": "active", "service": "planner-agent" }
```

## Known Gaps & Limitations

| Gap | Notes |
|---|---|
| No unit or integration tests | The planner has no test suite |
| RAG service not included | Requires an external RAG service; returns empty context if unavailable |
| No authentication | `/plan` endpoint is unauthenticated; add middleware before exposing publicly |
| Retry delay | Retries are immediate with no back-off; consider `asyncio.sleep` between attempts |

## Security Notes

- No API keys, secrets, or HP credentials in this codebase.
- All service URLs (`localhost`) are configured via `.env` — never commit a `.env` file.
- Do not expose port 9002 publicly without a reverse proxy and authentication.
