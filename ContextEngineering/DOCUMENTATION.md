# 🖨️ Context-Aware Print Management Application - Complete Documentation

**A local, privacy-focused AI agent using Ollama (Llama 3.1), LangGraph, and Streamlit**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Installation](#installation)
6. [Usage Guide](#usage-guide)
7. [Testing & Scenarios](#testing--scenarios)
8. [AI Agent Details](#ai-agent-details)
9. [Database Schema](#database-schema)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This application demonstrates a **truly agentic AI system** for print management that:
- Learns from user behavior patterns
- Provides intelligent recommendations with transparent reasoning
- Handles errors proactively
- Adapts to individual user preferences
- Runs 100% locally (no cloud dependencies)

### Key Principles
- **Privacy-First**: All data stored locally in SQLite
- **AI-Powered**: Decisions made by LLM, not hardcoded rules
- **Transparent**: Shows AI reasoning for every recommendation
- **Context-Aware**: Analyzes complete user history for personalization

---

## Quick Start

### Prerequisites
- Python 3.9+
- Ollama with llama3.1 model

### Installation

```bash
# 1. Install Ollama (if not already installed)
# Download from https://ollama.ai

# 2. Pull Llama 3.1 model
ollama pull llama3.1

# 3. Clone/navigate to project directory
cd ContextEngineering

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Run the application
run.bat
# OR
python -m streamlit run src/app.py
```

### First Run
1. App opens in browser at http://localhost:8501
2. If no printer configured, shows setup wizard
3. Complete setup with your printer model
4. Start printing with AI-powered smart defaults!

---

## Features

### Core Capabilities

#### 1. **Smart Defaults (AI-Powered)**
- Analyzes last 5-10 print jobs
- Recommends color mode, quality, copies, paper size
- Shows reasoning: "You consistently print B&W high-quality documents"

#### 2. **Error Detection & Recovery**
- Automatically detects errors from last session
- Blocks print form until error resolved
- Provides AI-generated troubleshooting steps

#### 3. **Conversational AI**
- Chat interface for printer questions
- Context-aware responses (knows your printer model and history)
- Natural language interaction

#### 4. **Setup Wizard**
- Guides first-time users through configuration
- Saves printer model and preferences
- One-time setup, persistent storage

#### 5. **Scenario Testing** (NEW)
- Test different user behaviors and patterns
- Simulate various errors (Wi-Fi, paper jam, ink, etc.)
- Quick context switching (B&W user, color enthusiast, budget mode)

---

## Architecture

### System Components

```
┌─────────────────────────────────────┐
│      STREAMLIT UI (app.py)          │
│  - Dynamic rendering                │
│  - Chat interface                   │
│  - Setup wizard                     │
│  - Print configurator               │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   LANGGRAPH AGENT (agent.py)        │
│  - Intent detection (AI)            │
│  - Smart defaults (AI)              │
│  - Context analysis                 │
│  - Response generation              │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│   OLLAMA / LLAMA 3.1 (Local LLM)    │
│  - Intent: SETUP/PRINT/ERROR/CHAT   │
│  - Recommendations + reasoning      │
│  - Natural language responses       │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│    DATABASE LAYER (db.py)           │
│  - SQLite storage                   │
│  - Context aggregation              │
│  - Smart defaults calculation       │
└─────────────────────────────────────┘
```

### Files Structure

```
ContextEngineering/
├── src/
│   ├── app.py              # Streamlit UI
│   ├── agent.py            # LangGraph agent logic
│   ├── db.py               # Database layer
│   ├── db_extended.py      # Extended schema (23 scenarios)
│   └── user_context.db     # SQLite database
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows launcher
└── DOCUMENTATION.md        # This file
```

---

## Installation

### Step 1: Install Ollama

```bash
# Windows/Mac/Linux
# Download from https://ollama.ai
# Follow installation instructions

# Verify installation
ollama --version
```

### Step 2: Install Llama 3.1 Model

```bash
# Pull the model (this downloads ~4.7GB)
ollama pull llama3.1

# Test it's working
ollama run llama3.1
# Type a message, press Ctrl+D to exit
```

### Step 3: Install Python Dependencies

```bash
# Navigate to project directory
cd ContextEngineering

# Install dependencies
pip install -r requirements.txt

# Requirements include:
# - streamlit
# - langchain
# - langgraph
# - langchain-community
```

### Step 4: Run the Application

**Option A: Using batch file (Windows)**
```bash
run.bat
```

**Option B: Direct python command**
```bash
python -m streamlit run src/app.py
```

**Option C: From src directory**
```bash
cd src
streamlit run app.py
```

App opens at: http://localhost:8501

---

## Usage Guide

### First-Time Setup

1. **Launch app** - Run `run.bat` or `streamlit run src/app.py`
2. **Setup wizard appears** - No printer configured yet
3. **Enter printer details**:
   - Printer model (e.g., "HP DeskJet 3755")
   - Default color mode (B&W or Color)
   - Default paper size (A4, Letter, etc.)
4. **Click "Complete Setup"**
5. **Ready to print!**

### Printing a Document

1. **Start print job**:
   - Click "New Print Job" button
   - OR let AI detect your intent automatically

2. **Review smart defaults**:
   - Color Mode: Pre-selected based on your history
   - Quality: Based on your pattern (draft/standard/high)
   - Copies: Average of your recent prints
   - Paper Size: Your most-used size
   
3. **See AI reasoning** (optional):
   - Expand "🤖 Why these defaults?"
   - Read AI's explanation

4. **Adjust settings** if needed

5. **Click "Print"**

### Error Handling

**If error detected:**
1. App automatically shows troubleshooting flow
2. Print form is blocked until error resolved
3. AI provides troubleshooting steps
4. Choose action:
   - "Problem Solved" - Mark resolved, continue
   - "More Help" - Open chat for assistance
   - "Ignore for Now" - Skip (not recommended)

### Chat Interface

1. Click "Ask a Question" button
2. Type your question (e.g., "How do I clear a paper jam?")
3. AI responds with context-aware answer
4. Ask follow-up questions
5. Click "Back to Main" to return

### Testing Controls (Sidebar)

**Expand "🧪 Testing Controls" to:**

#### Error Simulation
- Select error type from dropdown (10 options):
  - Paper jam
  - Wi-Fi disconnected
  - Low ink
  - Driver issues
  - Spooler errors
  - Paper tray empty
  - Door open
  - Network timeout
  - USB error
  - Paper size mismatch
- Click "Simulate Error"
- See how AI handles it!

#### Scenario Simulation

**Setup Flow Scenarios:**
- First-time user (no printer)
- HP DeskJet configured
- Canon PIXMA configured

**Print Flow Scenarios:**
- Recent B&W prints (x5)
- Recent color prints (x5)
- Mixed history
- High-quality pattern (x8)
- Draft mode pattern (x8)

**Quick Context:**
- B&W high-quality user
- Color photo enthusiast
- Budget-conscious (draft mode)
- Default settings user

#### Context Controls
- Clear Context - Reset everything
- Reset to Setup - Clear printer configuration

---

## Testing & Scenarios

### Manual Testing Workflow

**Test 1: Smart Defaults Learning**
```
1. Apply scenario: "B&W high-quality user"
2. Check sidebar - Smart Defaults show: B&W, high quality
3. Start new print job
4. Verify defaults pre-selected
5. Change to "Color photo enthusiast"
6. Smart Defaults update to: Color, high quality
```

**Test 2: Error Recovery**
```
1. Select error: "Wi-Fi connection lost"
2. Click "Simulate Error"
3. Try to start print job
4. Verify troubleshooting flow appears
5. Print form blocked
6. Click "Problem Solved"
7. Verify can print now
```

**Test 3: AI Reasoning**
```
1. Enable "Show Debug Info"
2. Apply scenario with clear pattern
3. Start print job
4. Expand "Why these defaults?"
5. Read AI's reasoning
6. Verify it matches the pattern
```

### Automated Testing

**Schema validation:**
```bash
cd src
python test_scenarios.py
```

**AI decision testing (requires Ollama):**
```bash
cd src
python test_agentic_scenarios.py
```

---

## AI Agent Details

### How the Agent Works

#### 1. Intent Detection (AI-Powered)

**Input to LLM:**
```
Context:
- Has printer: true/false
- Last session status: success/error
- Prints today: count
- User message: "..." (if chat)

Task: Determine user's intent
```

**LLM Output:**
```json
{
  "intent": "STANDARD_PRINT",
  "reasoning": "User has printer configured and no errors",
  "confidence": "high"
}
```

**Possible intents:**
- `FIRST_TIME_SETUP` - No printer configured
- `ERROR_RECOVERY` - Previous session had error
- `STANDARD_PRINT` - Normal printing
- `CHAT` - User asked a question

#### 2. Smart Defaults (AI-Powered)

**Input to LLM:**
```
Recent activity (last 10 prints):
1. B&W, high quality, 2 copies, A4
2. B&W, high quality, 2 copies, A4
3. B&W, high quality, 3 copies, A4
...

Task: Recommend settings with reasoning
```

**LLM Output:**
```json
{
  "color_mode": "black_white",
  "print_quality": "high",
  "num_copies": 2,
  "paper_size": "A4",
  "reasoning": "You consistently print 2-3 copies of high-quality B&W documents, suggesting professional reports or filing copies."
}
```

#### 3. Fallback Mechanism

If AI unavailable (Ollama not running):
- Falls back to **statistical defaults**
- Uses mode (most frequent) for categorical settings
- Uses average for numeric settings
- Shows "📊 Statistical Analysis" instead of "🤖 AI-Powered"

### AI Transparency

**All AI decisions are visible:**
1. **Sidebar**: Shows "🤖 AI-Powered Recommendations" badge
2. **Print Form**: "Why these defaults?" expander with reasoning
3. **Debug Panel**: Full AI reasoning and intent detection

---

## Database Schema

### Tables

#### 1. `user_sessions`
Tracks each session for error detection.

```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,           -- 'success' or 'error'
    error_message TEXT,
    session_data TEXT
)
```

#### 2. `user_preferences`
Stores printer setup and default preferences.

```sql
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    printer_setup BOOLEAN DEFAULT 0,
    last_printer_model TEXT,
    default_color_mode TEXT,
    default_paper_size TEXT,
    preferences_data TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 3. `usage_history`
Records every print operation for pattern learning.

```sql
CREATE TABLE usage_history (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    color_mode TEXT,
    paper_size TEXT,
    num_copies INTEGER,
    print_quality TEXT,
    operation_type TEXT,
    success BOOLEAN DEFAULT 1
)
```

### Key Methods

**Context Retrieval:**
- `get_user_context(user_id)` - Complete context
- `summarize_context(user_id)` - Natural language summary
- `get_smart_defaults(user_id)` - Statistical defaults (fallback)

**Context Updates:**
- `update_context(user_id, type, data)` - Update session/preferences
- `add_to_usage_history(...)` - Record print operation
- `save_printer_setup(...)` - Save printer configuration

**Utilities:**
- `has_printer_setup(user_id)` - Check if configured
- `get_last_session_status(user_id)` - Check for errors
- `clear_context(user_id)` - Reset for testing

---

## Troubleshooting

### Problem: "AI Agent Not Available"

**Cause:** Cannot connect to Ollama

**Solutions:**
1. Check Ollama is running:
   ```bash
   ollama list
   ```
2. Start Ollama if needed:
   ```bash
   ollama serve
   ```
3. Verify llama3.1 is installed:
   ```bash
   ollama pull llama3.1
   ```
4. App will fallback to statistical defaults if AI unavailable

### Problem: "Module not found" errors

**Cause:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: Database locked

**Cause:** Multiple instances accessing database

**Solution:**
1. Close all Streamlit instances
2. Delete database (will recreate):
   ```bash
   del src\user_context.db
   ```

### Problem: Smart defaults not updating

**Cause:** Not enough usage history

**Solution:**
- Need at least 5 prints for meaningful patterns
- Use scenario simulation to create history quickly:
  1. Sidebar → Testing Controls
  2. Scenario Simulation → Print Flow
  3. Select "Recent B&W prints (x5)"
  4. Click "Apply Print Scenario"

### Problem: Port already in use

**Cause:** Previous Streamlit instance still running

**Solution:**
```bash
# Kill the process on port 8501
# Windows:
netstat -ano | findstr :8501
taskkill /PID <process_id> /F

# Linux/Mac:
lsof -ti:8501 | xargs kill -9
```

---

## Advanced Topics

### Extending the Agent

**Add new intent:**
1. In `agent.py`, update intent detection prompt
2. Add handler node in LangGraph workflow
3. Add UI flow in `app.py`

**Add new database fields:**
1. Update schema in `db.py` `init_database()`
2. Add getters/setters
3. Update context aggregation in `get_user_context()`

### Extended Schema (db_extended.py)

For production use with complete scenarios:
- 9 comprehensive tables
- Supports 23 printer app scenarios
- Eco optimization tracking
- Scanner support
- Network discovery
- Recent file detection
- Alert management

See `db_extended.py` and test files for implementation.

---

## Privacy & Security

- ✅ **100% Local**: All data in local SQLite database
- ✅ **No Cloud**: No data sent to external servers
- ✅ **Local AI**: Ollama runs entirely on your machine
- ✅ **No Tracking**: No analytics or telemetry
- ✅ **No API Calls**: No internet connection required (except Ollama install)

Your print history, preferences, and interactions never leave your computer.

---

## Contributing

This is an educational/demonstration project showing:
- Truly agentic AI (decisions by LLM, not rules)
- Local-first privacy
- Context-aware personalization
- Transparent AI reasoning

Feel free to:
- Extend functionality
- Add new scenarios
- Improve UI/UX
- Integrate actual printer drivers

---

## License

Educational/Demo Project - Use freely for learning and experimentation.

---

## Acknowledgments

- **Ollama** - Local LLM runtime
- **LangChain/LangGraph** - Agent framework
- **Streamlit** - Rapid UI development
- **Llama 3.1** - Meta's language model

---

**Built with ❤️ for privacy-conscious, AI-powered local applications**

*Last Updated: February 11, 2026*
