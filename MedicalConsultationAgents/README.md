# Medical Consultation Agents

A multi-specialist medical Q&A system built with **AutoGen** and **Ollama (Llama 3.1)**. An Orchestrator agent analyses each user question and routes it to the most appropriate specialist agent, which then responds with domain-specific guidance.

> **Disclaimer:** This is a PoC for demonstrating multi-agent orchestration. It is not a substitute for professional medical advice.

---

## How It Works

```
User Question
      │
      ▼
┌─────────────┐
│ Orchestrator │  ← routes query based on keywords + LLM reasoning
└──────┬───────┘
       │
  ┌────┴─────────────────────────┐
  │             │                │
  ▼             ▼                ▼
General MD  Heart Specialist  Pathologist
(general    (cardiology,      (lab results,
 symptoms,   chest pain,       imaging, scans,
 prevention) pulmonary)        biopsies)
```

The Orchestrator uses Llama 3.1 to reason over the question and pick the right specialist. If the query spans multiple domains, it can route to more than one.

---

## Folder Structure

```
MedicalConsultationAgents/
└── src/
    ├── main.py                  # Entry point — wires agents and starts chat loop
    ├── config/
    │   └── ollama_config.json   # Ollama LLM connection config
    └── agents/
        ├── orchestrator.py      # Routes queries to the right specialist
        ├── general_md.py        # General Medical Doctor agent
        ├── heart_specialist.py  # Cardiologist agent
        └── pathologist.py       # Pathologist / Radiologist agent
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | |
| [Ollama](https://ollama.com) | Running on `http://localhost:11434` |
| `llama3.1` model | `ollama pull llama3.1` |
| `pyautogen` | AutoGen multi-agent framework |

---

## Setup

```bash
# 1. Pull the model
ollama pull llama3.1

# 2. Install dependencies
pip install pyautogen

# 3. Run
cd src
python main.py
```

---

## Example Session

```
Welcome to the Medical Agent System! Enter your medical question (or 'quit' to exit).

Your question: I have chest pain and shortness of breath

→ Orchestrator routes to: Heart Specialist
→ Heart Specialist: "Chest pain combined with shortness of breath can indicate
  several conditions including angina, pulmonary embolism, or anxiety. I strongly
  recommend seeking immediate medical attention if symptoms are severe..."
```

---

## Agent Routing Logic

| Symptom / Topic | Routed To |
|---|---|
| General health, fever, headache, prevention | General MD |
| Chest pain, palpitations, blood pressure, lungs, breathing | Heart Specialist |
| Lab results, X-rays, scans, biopsies, blood tests | Pathologist |

Routing is handled by the Orchestrator using a two-step approach:
1. **Keyword matching** for common terms (fast path)
2. **LLM reasoning** via Llama 3.1 for ambiguous queries

---

## Configuration

Edit [`src/config/ollama_config.json`](src/config/ollama_config.json) to change the model or Ollama endpoint:

```json
[
    {
        "model": "llama3.1",
        "api_base": "http://localhost:11434/api",
        "api_type": "ollama"
    }
]
```
