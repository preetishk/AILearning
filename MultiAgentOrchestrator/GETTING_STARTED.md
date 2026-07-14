# Getting Started with AI Agentic Framework

## Installation

### 1. Prerequisites

Ensure you have:
- Python 3.11+
- Ollama installed and running
- Llama3.1 model pulled in Ollama

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai

# Pull the llama3.1 model
ollama pull llama3.1

# Verify Ollama is running
ollama list
```

### 2. Install Dependencies

```bash
cd agentic_framework
pip install -r requirements.txt
```

## Quick Start

### Option 1: Interactive Demo

Run the quickstart script for an interactive chat:

```bash
python examples/quickstart.py
```

### Option 2: Basic Agent Example

```bash
python examples/basic_agent.py
```

### Option 3: RAG-Enabled Agent

```bash
python examples/rag_agent.py
```

### Option 4: Multi-Agent System

```bash
python examples/multi_agent.py
```

## Simple Usage Example

```python
import asyncio
from MultiAgentOrchestrator import AgentFramework, create_simple_agent

async def main():
    # Initialize framework
    framework = AgentFramework()
    
    # Create an agent
    agent = await create_simple_agent(
        framework=framework,
        name="my_assistant",
        description="A helpful AI assistant",
        model="llama3.1"
    )
    
    # Use the agent
    response = await agent.execute("Hello! What can you do?")
    print(response)

asyncio.run(main())
```

## Advanced Usage

### Creating Custom Agents

```python
from MultiAgentOrchestrator import AgentFramework, AgentConfig, AgentCapabilities, AgentBehavior

framework = AgentFramework()

# Create custom configuration
config = AgentConfig(
    agent_name="custom_agent",
    agent_description="My custom agent",
    capabilities=AgentCapabilities(
        prompts=["general_assistant"],
        tools=["calculator", "echo"],
        rag_sources=[],
        max_iterations=10
    ),
    behavior=AgentBehavior(
        model="llama3.1",
        temperature=0.7,
        max_tokens=2048
    )
)

# Deploy agent
agent = await framework.create_and_deploy_agent(config)
```

### Adding RAG Knowledge Base

```python
# Add a knowledge source
framework.add_rag_source(
    source_id="my_docs",
    name="My Documentation",
    collection_name="my_knowledge"
)

# Add documents
documents = [
    "Document 1 content...",
    "Document 2 content...",
]

await framework.add_documents_to_rag(
    source_id="my_docs",
    documents=documents
)

# Create agent with RAG
config.capabilities.rag_sources = ["my_docs"]
agent = await framework.create_and_deploy_agent(config)
```

### Creating Custom Tools

```python
from MultiAgentOrchestrator.models import ToolDefinition, ToolType

# Define tool
tool_def = ToolDefinition(
    tool_id="my_custom_tool",
    name="My Custom Tool",
    description="Does something useful",
    type=ToolType.FUNCTION,
    parameters=[
        {
            "name": "input",
            "type": "string",
            "description": "Input parameter",
            "required": True
        }
    ]
)

# Create executor function
async def my_tool_executor(input: str):
    # Your custom logic here
    return f"Processed: {input}"

# Register tool
framework.register_tool(tool_def, my_tool_executor)
```

### Creating Custom Prompts

```python
# Create custom prompt template
framework.create_prompt_template(
    template_id="my_template",
    name="My Custom Template",
    description="Custom prompt template",
    template="You are {agent_name}. Context: {rag_context}\n\nUser: {user_input}\n\nAssistant:",
    variables=["agent_name", "rag_context", "user_input"],
    category="custom"
)

# Use in agent configuration
config.capabilities.prompts = ["my_template"]
```

## Monitoring and Evaluation

### Get Agent Status

```python
status = framework.get_agent_status(agent_id)
print(f"Interactions: {status['total_interactions']}")
print(f"Tokens Used: {status['total_tokens_used']}")
```

### View Logs

```python
logs = framework.get_agent_logs(agent_id, limit=100)
for log in logs:
    print(f"{log.timestamp}: {log.event_type}")
```

### Generate Report

```python
from datetime import datetime, timedelta

time_range = (
    datetime.now() - timedelta(days=7),
    datetime.now()
)

report = framework.generate_agent_report(agent_id, time_range)
print(f"Quality Score: {report['metrics']['average_quality_score']}")
```

## Project Structure

```
agentic_framework/
├── __init__.py              # Package exports
├── main.py                  # Main framework class
├── requirements.txt         # Dependencies
├── models/                  # Data models
│   ├── agent_config.py     # Agent configuration
│   ├── tool_definition.py  # Tool definitions
│   └── prompt_template.py  # Prompt templates
├── core/                    # Core managers
│   ├── agent_manager.py    # Agent lifecycle
│   ├── prompt_manager.py   # Prompt management
│   ├── tool_manager.py     # Tool execution
│   └── rag_manager.py      # RAG retrieval
├── services/                # Support services
│   └── logging_service.py  # Logging & evaluation
└── examples/                # Example scripts
    ├── quickstart.py       # Interactive demo
    ├── basic_agent.py      # Basic usage
    ├── rag_agent.py        # RAG example
    └── multi_agent.py      # Multi-agent example
```

## Troubleshooting

### Ollama Connection Issues

If you get connection errors:

1. Verify Ollama is running: `ollama list`
2. Check the service: `curl http://localhost:11434`
3. Restart Ollama if needed

### Import Errors

If you get import errors:

```bash
# Make sure you're in the right directory
cd agentic_framework

# Install in development mode
pip install -e .
```

### Model Not Found

If llama3.1 is not found:

```bash
# Pull the model
ollama pull llama3.1

# Verify it's available
ollama list
```

## Next Steps

1. **Explore Examples**: Run all example scripts to see different capabilities
2. **Build Custom Agents**: Create agents for your specific use cases
3. **Add Knowledge**: Populate RAG sources with your domain knowledge
4. **Create Tools**: Develop custom tools for specialized tasks
5. **Monitor Performance**: Use logging and evaluation features

## Support

For issues or questions:
- Check the main framework documentation: `../AI_Agentic_Framework.md`
- Review example code in `examples/` directory
- Ensure all dependencies are installed correctly

## License

MIT License - See LICENSE file for details
