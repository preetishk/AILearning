# Prompt Template System Guide

## Overview

The AI Agentic Framework includes a comprehensive prompt template management system with built-in versioning, performance tracking, and dynamic rendering capabilities.

---

## Where Are Templates Defined?

Templates are managed by the **PromptManager** class located in:
```
agentic_framework/core/prompt_manager.py
```

When you initialize the framework, default templates are automatically loaded in the `_load_default_templates()` method.

```python
framework = AgentFramework()
# Default templates are now available:
# - "general_assistant"
# - "customer_support"
# - "research_assistant"
```

---

## Built-in Templates

### 1. General Assistant (`general_assistant`)
- **Purpose**: General-purpose conversational agent
- **Variables**: agent_name, agent_description, rag_context, history, user_input
- **Version**: 1.0.0
- **Category**: general

**Template:**
```
You are {agent_name}, a helpful AI assistant. {agent_description}

Context:
{rag_context}

Conversation History:
{history}

User: {user_input}