"""
Context-Aware Print Management Application

A privacy-focused AI agent for intelligent print management using:
- Ollama (Llama 3.1) for natural language understanding
- LangGraph for agent workflow orchestration
- Streamlit for dynamic, context-aware UI
- SQLite for local data persistence
"""

__version__ = "1.0.0"
__author__ = "AI Learning Project"
__description__ = "Context-Aware Print Management with Local AI"

from .db import ContextDatabase, get_db
from .agent import PrintManagementAgent, get_agent

__all__ = [
    "ContextDatabase",
    "get_db",
    "PrintManagementAgent",
    "get_agent"
]
