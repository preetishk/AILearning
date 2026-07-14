# Context-Aware Print Management — AI Agent PoC

A local, privacy-focused AI agent for intelligent print job management. Uses **LangGraph** for agentic workflows, **Ollama (Llama 3.1)** as the LLM, and **Streamlit** for the UI. All data is stored locally in SQLite — no cloud dependencies.

---

## Folder Structure

```
ContextEngineering/
├── src/
│   ├── app.py                      # Streamlit UI — dynamic, context-driven interface
│   ├── agent.py                    # LangGraph agent — intent detection & recommendations
│   ├── db.py                       # SQLite layer — sessions, preferences, usage history
│   ├── db_extended.py              # Extended DB helpers
│   ├── test_scenarios.py           # Manual test scenarios
│   └── test_agentic_scenarios.py   # Agentic behaviour test cases
├── DOCUMENTATION.md                # Full technical documentation
├── requirements.txt
└── .gitignore
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | |
| [Ollama](https://ollama.com) | Running locally on `http://localhost:11434` |
| `llama3.1` model | `ollama pull llama3.1` |

---

## Setup

```bash
# 1. Pull the model
ollama pull llama3.1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
cd src
streamlit run app.py
```

---

## Features

- **Intent detection** — classifies user input into print intents (setup, troubleshoot, color/BW print, settings change)
- **Context-aware recommendations** — reads full session + preference history to suggest smart defaults
- **Transparent AI reasoning** — surfaces the LLM's reasoning for every decision
- **Adaptive UI** — Streamlit interface changes layout based on detected intent
- **Persistent history** — SQLite stores sessions, preferences, and usage patterns across restarts
- **100% local** — no API keys, no cloud calls

---

## Agent Intents

| Intent | Trigger |
|---|---|
| `SETUP_REQUIRED` | User needs to configure a printer |
| `TROUBLESHOOT_ERROR` | Printer error detected |
| `STANDARD_PRINT_COLOR` | User wants colour printing |
| `STANDARD_PRINT_BW` | User wants black & white printing |
| `CHANGE_SETTINGS` | User wants to adjust printer settings |
| `GENERAL_CHAT` | General conversation |

---

## Running Tests

```bash
cd src
python test_scenarios.py
python test_agentic_scenarios.py
```

---

## Architecture

```
User Input
    │
    ▼
[Streamlit UI] ──► [LangGraph Agent]
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
      [fetch_context]      [analyze_intent]
              │                    │
              └─────────┬──────────┘
                        ▼
              [generate_response]
                        │
                        ▼
              [SQLite — user_context.db]
```

For full architecture and database schema details see [DOCUMENTATION.md](DOCUMENTATION.md).
