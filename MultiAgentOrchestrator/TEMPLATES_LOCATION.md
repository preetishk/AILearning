# Quick Reference: Prompt Templates

## Where Are the Templates?

The prompt templates are **NOT** in the examples folder. They are defined in:

```
agentic_framework/core/prompt_manager.py
```

Specifically in the `_load_default_templates()` method (line ~20).

---

## How Templates Work

### 1. Templates are Pre-loaded at Framework Initialization

```python
framework = AgentFramework()
# ↓ This automatically calls PromptManager.__init__()
#   ↓ Which calls _load_default_templates()
#     ↓ Which creates 3 built-in templates
```

### 2. You Reference Templates by ID

In your agent config:

```python
AgentCapabilities(
    prompts=["general_assistant"],  # ← Template ID (not the template itself)
    ...
)
```

### 3. Templates are Used Behind the Scenes

When you call `agent.execute()`, the framework:
1. Gets the template from PromptManager
2. Injects your variables (user_input, rag_context, history, etc.)
3. Sends the rendered prompt to the LLM
4. Tracks usage and performance

---

## Built-in Templates

| Template ID | Purpose | Version |
|------------|---------|---------|
| `general_assistant` | General Q&A | 1.0.0 |
| `customer_support` | Customer service | 1.0.0 |
| `research_assistant` | Research & analysis | 1.0.0 |

---

## Viewing Templates

### Option 1: List all templates
```python
templates = framework.list_prompt_templates()
for t in templates:
    print(f"{t.name} (v{t.version}): {t.template_id}")
```

### Option 2: Get specific template
```python
template = framework.prompt_manager.get_template("general_assistant")
print(f"Template: {template.template}")
print(f"Version: {template.version}")
print(f"Usage Count: {template.usage_count}")
```

---

## Creating Custom Templates

```python
framework.create_prompt_template(
    template_id="my_custom_template",
    name="My Custom Template",
    description="Does something special",
    template="You are {agent_name}. User asks: {user_input}",
    variables=["agent_name", "user_input"],
    category="custom"
)

# Use it in an agent
config.capabilities.prompts = ["my_custom_template"]
```

---

## Template Versioning

Templates support versioning:

```python
# Get template
template = framework.prompt_manager.get_template("my_template")

# Update version
framework.prompt_manager.update_template(
    "my_template",
    {"version": "2.0.0", "template": "New improved template..."}
)
```

**Versioning Best Practices:**
- `1.0.0 → 1.0.1`: Bug fixes (PATCH)
- `1.0.0 → 1.1.0`: New features (MINOR)
- `1.0.0 → 2.0.0`: Breaking changes (MAJOR)

---

## Template Performance Tracking

Templates automatically track:
- **Usage Count**: How many times used
- **Performance Score**: Running average of quality (0.0 - 1.0)
- **Created/Updated timestamps**

```python
template = framework.prompt_manager.get_template("general_assistant")
print(f"Used {template.usage_count} times")
print(f"Performance: {template.performance_score:.2f}")
```

---

## Complete Examples

### See Templates in Action:

1. **Basic Usage** (Updated):
   ```bash
   python examples/basic_agent.py
   ```
   Now shows available templates and usage tracking!

2. **Full Template Management**:
   ```bash
   python examples/prompt_template_demo.py
   ```
   Complete demo of template system with versioning!

---

## Summary

✅ **Templates** are in `core/prompt_manager.py`  
✅ **Versioning** is built into the PromptTemplate model  
✅ **Usage** is tracked automatically  
✅ **Examples** now demonstrate the template system  

**Templates are a central feature that makes prompt engineering manageable and trackable!**
