# 🤖 MultiAgentOrchestrator

A Python framework for building and running **multiple AI agents locally** using **Ollama (Llama 3.1)** as the LLM backend and **Semantic Kernel** for agent orchestration.

---

## 🎯 What Does It Actually Do?

You define an agent — give it a name, a system prompt, and optionally some tools or documents — and the framework spins it up, routes queries to it, tracks its conversation history, and logs every interaction.

You can run **multiple agents at the same time**, each with its own role, and route different questions to the right one automatically.

**Concrete example:** You could have three agents running simultaneously:
- A `code-reviewer` agent that only answers questions about code quality
- A `doc-writer` agent that generates documentation
- A `data-analyst` agent that queries your ChromaDB knowledge base via RAG

Each agent gets its own conversation history, token usage tracking, and response quality score — all written to a structured log automatically.

### The Four Components

| Component | What it does |
|---|---|
| **AgentManager** | Creates, registers, and routes queries across multiple agents |
| **PromptManager** | Stores and versions reusable prompt templates (with variable substitution) |
| **ToolManager** | Registers Python functions as callable tools that agents can invoke |
| **RAGManager** | Ingests documents into ChromaDB and retrieves relevant chunks at query time |

### What You Get Without Writing It Yourself

| Capability | Detail |
|---|---|
| Ollama + Semantic Kernel wiring | Configured automatically from `.env` |
| Conversation history per agent | Stored in-memory across calls |
| Token + cost tracking | Logged per agent per call |
| Response quality scoring | Auto-evaluated on every response |
| Document ingestion → vector search | Drop files into RAGManager, query instantly |
| MCP tool protocol support | Expose tools as Model Context Protocol endpoints |

---

## 🚀 Quick Start - Create Your First Agent in 3 Lines

```python
from MultiAgentOrchestrator import AgentFramework, create_simple_agent

framework = AgentFramework()
agent = await create_simple_agent(framework, "my_assistant", "A helpful AI assistant")
response = await agent.execute("What can you help me with?")
```

**That's it!** You now have a fully functional AI agent with:
- ✅ Ollama/Llama3.1 integration
- ✅ Conversation history tracking
- ✅ Performance logging
- ✅ Quality evaluation
- ✅ Error handling

---

## 🏗️ Framework Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentFramework (Main Entry)               │
│                   Your Single Point of Control               │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        │            │            │              │
   ┌────▼────┐  ┌───▼────┐  ┌───▼─────┐  ┌────▼─────┐
   │ Agent   │  │ Prompt │  │  Tool   │  │   RAG    │
   │ Manager │  │Manager │  │ Manager │  │ Manager  │
   └────┬────┘  └───┬────┘  └───┬─────┘  └────┬─────┘
        │           │            │             │
        │           │            │             │
   ┌────▼───────────▼────────────▼─────────────▼─────┐
   │            Logging & Evaluation Service          │
   │         (Tracks Everything Automatically)        │
   └──────────────────────────────────────────────────┘
```

---

## 🛠️ Core Services Explained

### 1️⃣ **Agent Manager** - Agent Lifecycle Orchestration

**What it does**: Complete agent lifecycle management from creation to retirement with Semantic Kernel integration.

**Core Components**:
- **Agent Class**: Individual agent instance with SK kernel, tools, and state
- **AgentManager Class**: Registry and orchestrator for multiple agents

**Key Capabilities**:
- 📋 **Agent Registry**: Central catalog of all agents with metadata
- 🚀 **Deployment**: Hot-deploy agents without system restart
- 🔄 **State Management**: Track conversations, tokens, costs per agent
- 🎯 **Routing**: Intelligent request routing to appropriate agents
- 🔌 **SK Integration**: Semantic Kernel for advanced planning
- 🛠️ **Tool-as-Plugin**: Automatically wraps tools as SK plugins
- 🧠 **Memory**: Built-in conversation history and context

**Internal Architecture**:
```python
class Agent:
    - config: AgentConfig           # Agent configuration
    - kernel: Kernel                # Semantic Kernel instance
    - state: AgentState             # Runtime state (status, metrics)
    - _setup_kernel()               # Configure SK with Ollama
    - _register_tools_as_plugins()  # Wrap tools for SK
    - execute(query, context)       # Main execution flow
    
class AgentManager:
    - agents: Dict[str, Agent]      # Active agent instances
    - agent_configs: Dict           # Agent configurations
    - deploy_agent(config)          # Create and start agent
    - route_request(query)          # Find best agent for task
    - get_agent_status(agent_id)    # Metrics and health
```

**Execution Flow**:
```
User Query
    ↓
Agent.execute(query)
    ↓
1. RAG Retrieval (if enabled) → Get relevant context
2. Prompt Generation → Build contextualized prompt
3. Semantic Kernel → LLM inference with Ollama
4. Tool Execution (if needed) → Execute requested tools
5. Response Assembly → Combine results
    ↓
Return to user
```

**Example Use Case**:
```python
# Register an agent
agent_id = framework.create_agent(config)

# Deploy it (makes it active, sets up SK kernel)
agent = await framework.deploy_agent(agent_id)

# Use it immediately
response = await agent.execute("Hello!")

# Check its status anytime
status = framework.get_agent_status(agent_id)
print(f"Total interactions: {status['total_interactions']}")
print(f"Average response time: {status['avg_response_time_ms']:.2f}ms")
print(f"Total tokens used: {status['total_tokens']}")

# Retire when done
framework.retire_agent(agent_id)
```

**How it helps**: 
- No need to manage SK kernel setup manually
- Automatic tool-to-plugin conversion
- Built-in conversation tracking
- Production-ready state management
- Create, deploy, monitor, and retire agents programmatically

---

### 2️⃣ **Prompt Manager** - Template & Prompt Engineering

**What it does**: Centralized prompt template management with versioning, performance tracking, and dynamic generation.

**Core Components**:
- **PromptTemplate Class**: Individual template with metadata and performance tracking
- **PromptManager Class**: Template registry and optimization engine

**Key Capabilities**:
- 📝 **Template Library**: Pre-built templates (general, support, research)
- 🔧 **Dynamic Generation**: Context-aware prompt building with variable substitution
- 📊 **Performance Tracking**: Track which prompts perform best (usage count, avg score)
- 🎨 **Customization**: Create custom templates with variables
- 🔄 **Versioning**: Template version management (1.0.0, 1.1.0, 2.0.0, etc.)
- 🎯 **Optimization**: Automatic performance-based template selection
- 📈 **A/B Testing**: Compare template variants and select best performer

**Template Structure**:
```python
class PromptTemplate:
    template_id: str                    # Unique identifier
    name: str                           # Human-readable name
    description: str                    # What this template does
    template: str                       # Template string with {variables}
    variables: List[str]                # Required variables
    version: str = "1.0.0"             # Semantic versioning
    category: str = "general"           # Template category
    usage_count: int = 0                # How many times used
    performance_score: float = 0.0      # Running average quality
    created_at: datetime
    updated_at: datetime
```

**Built-in Templates**:
1. **general_assistant** - General-purpose conversational agent
2. **customer_support** - Customer service with empathy and professionalism
3. **research_assistant** - Research and analysis tasks

**Template Variables**:
- `{user_input}` - User's query or message
- `{rag_context}` - Retrieved documents from knowledge base
- `{conversation_history}` - Recent conversation context
- `{current_date}` - Current date/time
- Custom variables as needed

**Example Use Case - Create Custom Template**:
```python
# Create a custom prompt template
framework.create_prompt_template(
    template_id="sales_agent_v1",
    name="Sales Assistant",
    description="Helps with sales inquiries",
    template="""You are a sales expert at {company_name}.

Product Information:
{rag_context}

Customer Question: {user_input}

Provide a helpful, professional response focusing on value and benefits.

Sales Agent:""",
    variables=["company_name", "rag_context", "user_input"],
    version="1.0.0",
    category="sales"
)

# Use it in agent config
config.capabilities.prompts = ["sales_agent_v1"]

# Template is automatically rendered with context during execution
```

**Example Use Case - Version and Optimize**:
```python
# Get template performance stats
template = framework.get_template("sales_agent_v1")
print(f"Usage: {template.usage_count}")
print(f"Avg Score: {template.performance_score:.2f}")

# Create improved version
framework.create_prompt_template(
    template_id="sales_agent_v2",
    name="Sales Assistant v2",
    template="[Improved prompt...]",
    version="2.0.0"
)

# Framework tracks which version performs better
# You can A/B test by randomly assigning versions
```

**Prompt Generation Flow**:
```
Agent receives query
    ↓
PromptManager.generate_prompt(template_id, context)
    ↓
1. Retrieve template from registry
2. Check if RAG context needed → Call RAG Manager
3. Build context dict with all variables
4. Substitute {variables} in template
5. Return fully rendered prompt
    ↓
Pass to Semantic Kernel for LLM inference
```

**How it helps**: 
- Separate prompt engineering from code
- Version, test, and optimize prompts independently
- Track which prompts work best over time
- Easy A/B testing of prompt variations
- Reuse templates across multiple agents

---

### 3️⃣ **Tool Manager** - Extensible Plugin System with MCP Support

**What it does**: Registry and execution engine for agent tools/functions, supporting both direct Python functions and MCP (Model Context Protocol) servers.

**Key Capabilities**:
- 🔌 **Built-in Tools**: Calculator, echo, and more
- ⚙️ **Custom Tools**: Easy plugin creation
- 🌐 **MCP Integration**: Connect to standardized MCP tool servers
- 🔄 **Dual-Mode Execution**: Direct functions OR MCP protocol
- 🚦 **Rate Limiting**: Prevent abuse with configurable limits
- ✅ **Validation**: Automatic parameter validation
- 🔄 **Retry Logic**: Automatic retry on failures
- 🔌 **Transport Support**: stdio, SSE, WebSocket for MCP

**Tool Types Supported**:
1. **FUNCTION** - Direct Python function calls (fast, local)
2. **MCP** - Model Context Protocol servers (standardized, language-agnostic)
3. **API** - External REST APIs
4. **DATABASE** - Database operations
5. **FILE_SYSTEM** - File operations
6. **CUSTOM** - User-defined types

**Example Use Case - Direct Function Tool**:
```python
from MultiAgentOrchestrator.models import ToolDefinition, ToolType

# Define a custom tool
weather_tool = ToolDefinition(
    tool_id="weather_lookup",
    name="Weather Lookup",
    description="Get current weather for a location",
    type=ToolType.FUNCTION,
    parameters=[
        {"name": "location", "type": "string", "required": True}
    ]
)

# Create executor
async def weather_executor(location: str):
    # Your API call here
    return f"Weather in {location}: Sunny, 72°F"

# Register it
framework.register_tool(weather_tool, weather_executor)

# Agents can now use it!
config.capabilities.tools = ["weather_lookup"]
```

**Example Use Case - MCP Tool**:
```python
from MultiAgentOrchestrator.models import ToolDefinition, ToolType, MCPConfig

# Define MCP tool connecting to filesystem server
mcp_config = MCPConfig(
    server_name="filesystem",
    transport="stdio",  # Use stdio for local MCP server
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    env={}
)

filesystem_tool = ToolDefinition(
    tool_id="read_file",
    name="File Reader",
    description="Read file contents via MCP",
    type=ToolType.MCP,
    mcp_config=mcp_config,
    parameters=[
        {"name": "path", "type": "string", "required": True}
    ]
)

# Register MCP tool (no executor needed - uses MCP protocol)
framework.register_tool(filesystem_tool)

# Agent can now read files through MCP server!
config.capabilities.tools = ["read_file"]
```

**MCP Transport Types**:
- **stdio**: Local MCP server via subprocess (best for local tools)
- **sse**: Server-Sent Events over HTTP (for remote MCP servers)
- **websocket**: WebSocket connection (for real-time MCP servers)

**Architecture Flow**:
```
Agent Request
    ↓
Tool Manager
    ↓
├─→ Direct Function? → Python Executor → Result
└─→ MCP Tool? → MCP Client → [stdio/SSE/WebSocket] → MCP Server → Result
```

**How it helps**: 
- Extend agent capabilities without modifying core code
- Use pre-built MCP servers from npm ecosystem
- Mix local (fast) and remote (standardized) tools
- Language-agnostic tool integration via MCP protocol
- Add new tools in minutes with either approach

---

### 4️⃣ **RAG Manager** - Knowledge Base Integration

**What it does**: Retrieval-Augmented Generation with vector databases, enabling agents to access external knowledge dynamically.

**Core Components**:
- **RAGSource Class**: Individual knowledge base with metadata
- **RAGManager Class**: Manages multiple ChromaDB collections and retrieval
- **EmbeddingFunction**: Sentence transformers for text-to-vector conversion

**Key Capabilities**:
- 🗄️ **ChromaDB Integration**: Persistent vector storage with HNSW indexing
- 🔍 **Semantic Search**: Find relevant context automatically using cosine similarity
- 📚 **Multi-Source**: Query multiple knowledge bases simultaneously
- 🎯 **Relevance Filtering**: Only retrieve high-quality matches (configurable threshold)
- 🔄 **Live Updates**: Add/update/delete documents dynamically
- 📊 **Metadata**: Store and filter by custom metadata (tags, dates, sources)
- ⚡ **Efficient**: Uses sentence-transformers for fast embeddings
- 🎛️ **Configurable**: Tune top_k, similarity threshold, reranking

**Architecture**:
```python
class RAGSource:
    source_id: str                      # Unique identifier
    name: str                           # Human-readable name
    collection_name: str                # ChromaDB collection
    embedding_model: str                # Model for embeddings
    metadata: Dict                      # Custom metadata

class RAGManager:
    sources: Dict[str, RAGSource]       # Registered knowledge bases
    chroma_client: chromadb.Client      # ChromaDB connection
    embedding_function: SentenceTransformer
    
    add_source(source_id, ...)          # Register new knowledge base
    add_documents(source_id, docs)      # Add documents to collection
    retrieve(source_id, query, top_k)   # Semantic search
    retrieve_from_multiple(sources, query)  # Multi-source retrieval
```

**Embedding Process**:
```
Document Text
    ↓
Sentence Transformer (all-MiniLM-L6-v2)
    ↓
384-dimensional vector
    ↓
ChromaDB HNSW Index
    ↓
Stored with metadata
```

**Retrieval Flow**:
```
User Query → "What's your refund policy?"
    ↓
Encode query to vector using same model
    ↓
ChromaDB cosine similarity search
    ↓
Retrieve top_k most similar documents (default: 5)
    ↓
Filter by similarity threshold (default: 0.7)
    ↓
Return ranked results with scores
    ↓
Inject into prompt as {rag_context}
```

**Example Use Case - Basic RAG**:
```python
# Add a knowledge source
framework.add_rag_source(
    source_id="product_kb",
    name="Product Knowledge Base",
    collection_name="products"
)

# Add documents
docs = [
    "Our premium plan costs $99/month and includes 24/7 support",
    "The basic plan is $29/month with email support",
    "Enterprise plans start at $499/month with dedicated account manager"
]
await framework.add_documents_to_rag("product_kb", docs)

# Enable RAG for agent
config.capabilities.rag_sources = ["product_kb"]

# Agent now has context!
response = await agent.execute("What's your pricing?")
# Agent retrieves relevant pricing docs automatically
```

**Example Use Case - Advanced RAG with Metadata**:
```python
# Add documents with metadata for filtering
docs_with_metadata = [
    {
        "text": "Premium plan: $99/mo with 24/7 support",
        "metadata": {
            "category": "pricing",
            "plan_type": "premium",
            "last_updated": "2024-01-15"
        }
    },
    {
        "text": "Enterprise SLA guarantees 99.9% uptime",
        "metadata": {
            "category": "sla",
            "plan_type": "enterprise",
            "last_updated": "2024-01-10"
        }
    }
]

await framework.add_documents_to_rag(
    "product_kb", 
    [d["text"] for d in docs_with_metadata],
    metadata=[d["metadata"] for d in docs_with_metadata]
)

# Retrieve with metadata filtering
results = await framework.retrieve_from_rag(
    source_id="product_kb",
    query="What are premium features?",
    top_k=3,
    where={"plan_type": "premium"}  # Only premium plan docs
)
```

**Example Use Case - Multi-Source RAG**:
```python
# Add multiple knowledge bases
framework.add_rag_source("company_kb", "Company KB", "company_docs")
framework.add_rag_source("technical_kb", "Technical KB", "tech_docs")
framework.add_rag_source("legal_kb", "Legal KB", "legal_docs")

# Agent can query multiple sources
config.capabilities.rag_sources = ["company_kb", "technical_kb"]

# Retrieval automatically queries both and merges results
response = await agent.execute("Tell me about your API and company history")
# Retrieves from both company_kb AND technical_kb
```

**Configuration Options**:
```python
# Customize retrieval behavior
rag_config = RAGConfig(
    embedding_model="all-MiniLM-L6-v2",  # Embedding model
    top_k=5,                              # Number of results
    similarity_threshold=0.7,             # Min similarity score
    rerank=True,                          # Re-rank results
    max_context_length=2000               # Max chars in context
)

framework.configure_rag(rag_config)
```

**How it helps**: 
- Give agents access to your knowledge base without fine-tuning
- Update knowledge in real-time (no model retraining)
- Semantic search finds relevant info even with different wording
- Persistent storage - data survives restarts
- Scalable to millions of documents
- Reduce hallucinations by grounding responses in facts

---

### 5️⃣ **Logging Service** - Observability & Evaluation

**What it does**: Comprehensive tracking, monitoring, and quality assessment for all agent interactions.

**Core Components**:
- **LoggingService Class**: Centralized logging and metrics collection
- **InteractionLog**: Individual conversation record with full context
- **EvaluationMetrics**: Quality scores and safety checks
- **PerformanceReport**: Aggregate analytics and insights

**Key Capabilities**:
- 📊 **Interaction Logging**: Every conversation tracked with full context
- 🎯 **Quality Metrics**: Automated scoring (relevance, coherence, helpfulness)
- 🔒 **Safety Checks**: Hallucination detection, PII detection, policy violations
- 📈 **Performance Reports**: Aggregate metrics and insights
- 💾 **Persistent Storage**: JSONL logs for analysis and replay
- ⏱️ **Latency Tracking**: Response time monitoring
- 💰 **Cost Tracking**: Token usage and API costs per agent
- 🔍 **Error Analysis**: Failure patterns and debugging

**Log Structure**:
```python
class InteractionLog:
    timestamp: datetime                 # When interaction occurred
    agent_id: str                       # Which agent handled it
    user_input: str                     # Original user query
    agent_response: str                 # Agent's response
    context: Dict                       # RAG context, tools used, etc.
    
    # Performance Metrics
    response_time_ms: float             # How long it took
    tokens_used: int                    # Total tokens consumed
    cost: float                         # API cost if applicable
    
    # Quality Scores (0.0 - 1.0)
    relevance_score: float              # How relevant to query
    coherence_score: float              # How well-structured
    helpfulness_score: float            # How useful to user
    overall_quality: float              # Aggregate score
    
    # Safety Checks
    hallucination_detected: bool        # Factual errors detected
    pii_detected: bool                  # Personal info found
    policy_violation: bool              # Against guidelines
    
    # Tool Usage
    tools_called: List[str]             # Which tools were used
    tool_results: Dict                  # Tool execution results
    
    # RAG Details
    rag_sources_used: List[str]         # Which knowledge bases
    documents_retrieved: int            # How many docs retrieved
    rag_relevance: float                # Quality of retrieved context
```

**Automated Quality Scoring**:
```python
# Automatically calculated for each interaction

Relevance Score:
- Does response address the query?
- Are retrieved documents relevant?
- Keyword/semantic alignment check

Coherence Score:
- Is response well-structured?
- Logical flow and consistency
- Grammar and readability

Helpfulness Score:
- Does it provide actionable info?
- Completeness of answer
- Appropriate level of detail

Overall Quality = (relevance + coherence + helpfulness) / 3
```

**Safety Detection**:
```python
# Automatic safety checks on every response

Hallucination Detection:
- Claims not supported by RAG context
- Fabricated facts or statistics
- Inconsistent information

PII Detection:
- Email addresses, phone numbers
- Social security numbers, credit cards
- Personal identifiable information

Policy Violation:
- Harmful content
- Inappropriate language
- Terms of service violations
```

**Example Use Case - Query Logs**:
```python
# Logs are automatic, but you can query them

# Get recent interactions for an agent
logs = framework.get_agent_logs(agent_id, limit=50)

for log in logs:
    print(f"User: {log.user_input}")
    print(f"Agent: {log.agent_response}")
    print(f"Quality: {log.overall_quality:.2f}")
    print(f"Time: {log.response_time_ms:.0f}ms")
    print(f"Tokens: {log.tokens_used}")
    print("---")
```

**Example Use Case - Performance Report**:
```python
from datetime import datetime, timedelta

# Generate performance report for last 7 days
report = framework.generate_agent_report(
    agent_id,
    time_range=(datetime.now() - timedelta(days=7), datetime.now())
)

print(f"=== Agent Performance Report ===")
print(f"Total Interactions: {report['total_interactions']}")
print(f"Success Rate: {report['metrics']['success_rate']:.1%}")
print(f"")
print(f"Average Quality: {report['metrics']['average_quality_score']:.2f}/1.0")
print(f"Average Relevance: {report['metrics']['average_relevance']:.2f}")
print(f"Average Coherence: {report['metrics']['average_coherence']:.2f}")
print(f"Average Helpfulness: {report['metrics']['average_helpfulness']:.2f}")
print(f"")
print(f"Performance:")
print(f"  Avg Response Time: {report['metrics']['avg_response_time_ms']:.0f}ms")
print(f"  Total Tokens Used: {report['metrics']['total_tokens']:,}")
print(f"  Total Cost: ${report['metrics']['total_cost']:.2f}")
print(f"")
print(f"Safety:")
print(f"  Hallucinations Detected: {report['metrics']['hallucinations_detected']}")
print(f"  PII Detected: {report['metrics']['pii_detected']}")
print(f"  Policy Violations: {report['metrics']['policy_violations']}")
print(f"")
print(f"Tools:")
print(f"  Most Used Tool: {report['metrics']['most_used_tool']}")
print(f"  Tool Success Rate: {report['metrics']['tool_success_rate']:.1%}")
```

**Example Use Case - Real-time Monitoring**:
```python
# Monitor agent in real-time
async def monitor_agent(agent_id, interval=10):
    while True:
        status = framework.get_agent_status(agent_id)
        recent_logs = framework.get_agent_logs(agent_id, limit=10)
        
        # Calculate rolling averages
        recent_quality = sum(l.overall_quality for l in recent_logs) / len(recent_logs)
        recent_response_time = sum(l.response_time_ms for l in recent_logs) / len(recent_logs)
        
        print(f"[{datetime.now()}] Agent: {agent_id}")
        print(f"  Recent Quality: {recent_quality:.2f}")
        print(f"  Recent Response Time: {recent_response_time:.0f}ms")
        print(f"  Total Interactions: {status['total_interactions']}")
        
        # Alert if quality drops
        if recent_quality < 0.6:
            print(f"  ⚠️ WARNING: Quality below threshold!")
        
        await asyncio.sleep(interval)

# Run monitoring in background
asyncio.create_task(monitor_agent("my_agent"))
```

**Log Storage**:
```python
# Logs are stored in JSONL format
# Location: logs/agent_{agent_id}_{date}.jsonl

# Each line is a JSON interaction log
{"timestamp": "2024-01-15T10:30:00", "agent_id": "support_bot", ...}
{"timestamp": "2024-01-15T10:31:15", "agent_id": "support_bot", ...}

# Can be analyzed with pandas, Spark, or any JSON tool
import pandas as pd
logs_df = pd.read_json("logs/agent_support_bot_2024-01-15.jsonl", lines=True)
print(logs_df.describe())
```

**Integration with External Tools**:
```python
# Export logs to external systems
logs = framework.get_agent_logs(agent_id, limit=1000)

# Send to analytics platform
for log in logs:
    analytics.track("agent_interaction", {
        "agent_id": log.agent_id,
        "quality": log.overall_quality,
        "response_time": log.response_time_ms,
        "timestamp": log.timestamp
    })

# Send alerts on issues
if log.hallucination_detected:
    slack.send_alert(f"Hallucination detected in agent {agent_id}")

if log.overall_quality < 0.5:
    pagerduty.trigger_incident(f"Low quality response from {agent_id}")
```

**How it helps**: 
- Full observability out of the box - know exactly how agents perform
- Identify quality issues before users complain
- Track costs and optimize token usage
- Detect safety issues automatically
- Generate reports for stakeholders
- Debug failures with full context
- Continuous improvement based on metrics
- Compliance and audit trail

---

## ⚡ How This Framework Helps You Create Agents Quickly

### **Traditional Workflow (Without Framework)**
```
1. Set up LLM connection (Ollama/OpenAI)      → 2-3 hours
2. Implement conversation history              → 1-2 hours
3. Build RAG pipeline (embeddings, vector DB)  → 4-6 hours
4. Create tool/function calling system         → 3-4 hours
5. Add logging and monitoring                  → 2-3 hours
6. Implement error handling                    → 1-2 hours
7. Create evaluation metrics                   → 2-3 hours
8. Test and debug integration                  → 3-5 hours

TOTAL: 18-28 hours (2-4 days)
```

### **With AI Agentic Framework**
```python
from MultiAgentOrchestrator import AgentFramework, AgentConfig, AgentCapabilities

framework = AgentFramework()

config = AgentConfig(
    agent_name="my_agent",
    agent_description="Does amazing things",
    capabilities=AgentCapabilities(
        tools=["calculator", "weather_lookup"],
        rag_sources=["my_knowledge_base"]
    )
)

agent = await framework.create_and_deploy_agent(config)

# Done! ✅
# TOTAL: 5-10 minutes
```

---

## 📦 Installation

### **Prerequisites**
1. **Python 3.11+**
2. **Ollama** with Llama3.1:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.1
   ```

### **Install Framework**
```bash
cd MultiAgentOrchestrator
pip install -r requirements.txt
```

---

## 🎓 Usage Examples

### **Example 1: Simple Q&A Agent**
```python
import asyncio
from MultiAgentOrchestrator import AgentFramework, create_simple_agent

async def main():
    framework = AgentFramework()
    agent = await create_simple_agent(
        framework, 
        "qa_bot", 
        "Answers questions helpfully"
    )
    
    response = await agent.execute("What is machine learning?")
    print(response)

asyncio.run(main())
```

### **Example 2: Customer Support with Knowledge Base**
```python
async def main():
    framework = AgentFramework()
    
    # Add company knowledge
    framework.add_rag_source("company_kb", "Company KB", "company_docs")
    await framework.add_documents_to_rag("company_kb", [
        "We offer 24/7 support via email and chat",
        "Refunds are available within 30 days",
        "Premium plans include priority support"
    ])
    
    # Create support agent with RAG
    config = AgentConfig(
        agent_name="support_bot",
        agent_description="Handles customer support inquiries",
        capabilities=AgentCapabilities(
            prompts=["customer_support"],
            rag_sources=["company_kb"]
        )
    )
    
    agent = await framework.create_and_deploy_agent(config)
    response = await agent.execute("What's your refund policy?")
    print(response)  # Uses RAG to pull relevant info!
```

### **Example 3: Multi-Agent System**
```python
# Create specialized agents
research_agent = await create_simple_agent(framework, "researcher", "Gathers information")
analyst_agent = await create_simple_agent(framework, "analyst", "Analyzes data")
writer_agent = await create_simple_agent(framework, "writer", "Creates reports")

# Use them together
research = await research_agent.execute("Find info on AI trends")
analysis = await analyst_agent.execute(f"Analyze this: {research}")
report = await writer_agent.execute(f"Write a report: {analysis}")
```

### **Example 4: MCP Tool Integration**
```python
from MultiAgentOrchestrator.models import ToolDefinition, ToolType, MCPConfig

async def main():
    framework = AgentFramework()
    
    # Register MCP filesystem tool
    filesystem_config = MCPConfig(
        server_name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
        env={}
    )
    
    filesystem_tool = ToolDefinition(
        tool_id="read_file",
        name="File Reader",
        description="Read file contents via MCP",
        type=ToolType.MCP,
        mcp_config=filesystem_config,
        parameters=[
            {"name": "path", "type": "string", "required": True}
        ]
    )
    
    framework.register_tool(filesystem_tool)
    
    # Create agent with MCP tool
    config = AgentConfig(
        agent_name="file_agent",
        agent_description="Agent with file system access via MCP",
        capabilities=AgentCapabilities(
            tools=["read_file", "calculator"]  # Mix MCP and direct tools!
        )
    )
    
    agent = await framework.create_and_deploy_agent(config)
    response = await agent.execute("Read the contents of config.json")
    print(response)  # Agent uses MCP to read file!
```

### **Example 5: Combining All Features**
```python
async def main():
    framework = AgentFramework()
    
    # 1. Add knowledge base
    framework.add_rag_source("company_kb", "Company KB", "company_docs")
    await framework.add_documents_to_rag("company_kb", [
        "Our company was founded in 2020",
        "We specialize in AI solutions",
        "Contact us at support@company.com"
    ])
    
    # 2. Create custom prompt
    framework.create_prompt_template(
        template_id="support_v1",
        name="Support Agent",
        template="""You are a helpful support agent.

Company Info:
{rag_context}

Customer: {user_input}

Agent:""",
        variables=["rag_context", "user_input"]
    )
    
    # 3. Register custom tool (direct function)
    async def check_order_status(order_id: str):
        return f"Order {order_id} is shipped"
    
    order_tool = ToolDefinition(
        tool_id="check_order",
        name="Order Status",
        type=ToolType.FUNCTION,
        parameters=[{"name": "order_id", "type": "string", "required": True}]
    )
    framework.register_tool(order_tool, check_order_status)
    
    # 4. Register MCP tool
    mcp_config = MCPConfig(
        server_name="database",
        transport="sse",
        server_url="http://localhost:3000/mcp",
        command=None,
        args=[],
        env={}
    )
    
    db_tool = ToolDefinition(
        tool_id="query_db",
        name="Database Query",
        type=ToolType.MCP,
        mcp_config=mcp_config,
        parameters=[{"name": "query", "type": "string", "required": True}]
    )
    framework.register_tool(db_tool)
    
    # 5. Create comprehensive agent
    config = AgentConfig(
        agent_name="super_agent",
        agent_description="Full-featured support agent",
        capabilities=AgentCapabilities(
            prompts=["support_v1"],
            tools=["check_order", "query_db", "calculator"],  # Direct + MCP + built-in
            rag_sources=["company_kb"]
        )
    )
    
    agent = await framework.create_and_deploy_agent(config)
    
    # 6. Use it!
    response = await agent.execute("When was the company founded and what's the status of order #12345?")
    # Uses RAG for company info + check_order tool for status
    
    # 7. Check performance
    report = framework.generate_agent_report(agent.config.agent_id)
    print(f"Quality Score: {report['metrics']['average_quality_score']:.2f}")
```

---

## 📂 Project Structure

```
MultiAgentOrchestrator/
├── __init__.py              # Package exports
├── main.py                  # AgentFramework main class
├── requirements.txt         # Dependencies
│
├── models/                  # Data models (Pydantic schemas)
│   ├── agent_config.py     # AgentConfig, AgentState, AgentCapabilities
│   ├── tool_definition.py  # ToolDefinition, ToolResult, MCPConfig
│   └── prompt_template.py  # PromptTemplate
│
├── core/                    # Core service managers
│   ├── agent_manager.py    # Agent lifecycle & SK orchestration
│   ├── prompt_manager.py   # Prompt template management & versioning
│   ├── tool_manager.py     # Tool registry, MCP client, execution
│   └── rag_manager.py      # RAG retrieval, ChromaDB, embeddings
│
├── services/                # Support services
│   └── logging_service.py  # Logging, evaluation, quality metrics
│
└── examples/                # Ready-to-run examples
    ├── quickstart.py       # Interactive chat demo
    ├── basic_agent.py      # Simple agent example
    ├── rag_agent.py        # Knowledge base agent
    ├── multi_agent.py      # Multi-agent collaboration
    ├── prompt_template_demo.py  # Template management showcase
    └── mcp_tool_demo.py    # MCP tool integration demo
```

---

## 🎯 Key Features Summary

| Feature | Description | Benefit |
|---------|-------------|---------|
| **One-Line Agent Creation** | `create_simple_agent()` | Get started in seconds |
| **Semantic Kernel Integration** | Built on Microsoft's SK framework | Advanced planning & plugins |
| **Local LLM (Ollama)** | No API costs, full privacy | Free & secure |
| **MCP Support** | Model Context Protocol for tools | Standardized, language-agnostic tools |
| **Dual-Mode Tools** | Direct functions + MCP servers | Flexible tool integration |
| **RAG Out-of-the-Box** | ChromaDB + embeddings included | Add knowledge bases easily |
| **Built-in Tools** | Calculator, echo, extensible | Extend capabilities fast |
| **Auto-Logging** | Every interaction tracked | Full observability |
| **Quality Evaluation** | Automated scoring | Know agent performance |
| **Multi-Agent Support** | Create specialized agent teams | Complex workflows |
| **Production Ready** | Error handling, retries, validation | Deploy with confidence |
| **Prompt Versioning** | Template management & A/B testing | Optimize prompts over time |

---

## 📚 Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Detailed setup and usage guide
- **[AI_Agentic_Framework.md](../AI_Agentic_Framework.md)** - Complete architecture documentation
- **[examples/](examples/)** - Working code examples

---

## 🤝 Contributing

Contributions welcome! This framework is designed to be extensible:
- Add new tools to `core/tool_manager.py`
- Create prompt templates in `core/prompt_manager.py`
- Extend evaluation metrics in `services/logging_service.py`

---

## 📄 License

MIT License - Use freely in personal and commercial projects

---

## 🎉 Get Started Now!

```bash
# 1. Install Ollama and pull model
ollama pull llama3.1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run interactive demo
python examples/quickstart.py

# 4. Build amazing agents! 🚀
```

**Questions?** Check [GETTING_STARTED.md](GETTING_STARTED.md) for troubleshooting and advanced usage.

---

*Built with ❤️ for developers who want to focus on what their agents do, not how they work.*
