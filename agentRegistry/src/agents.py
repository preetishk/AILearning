from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Registry - Agent Server")

# Request/Response models
class AgentRequest(BaseModel):
    prompt: str
    context: Optional[str] = None

class AgentResponse(BaseModel):
    agent_name: str
    response: str
    status: str = "success"

# Initialize Semantic Kernel agents
class AgentService:
    def __init__(self):
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize Semantic Kernel agents with Ollama/Llama 3.1"""
        
        # Llama Coder Agent
        coder_kernel = Kernel()
        coder_kernel.add_service(
            OllamaChatCompletion(
                service_id="llama-coder",
                ai_model_id="llama3.1",
                host="http://localhost:11434"
            )
        )
        self.agents["llama-coder"] = {
            "kernel": coder_kernel,
            "name": "Llama Coder",
            "system_prompt": "You are an expert Python programmer. Generate clean, efficient, and well-documented code based on user requirements."
        }
        
        # Tech Writer Agent
        writer_kernel = Kernel()
        writer_kernel.add_service(
            OllamaChatCompletion(
                service_id="tech-writer",
                ai_model_id="llama3.1",
                host="http://localhost:11434"
            )
        )
        self.agents["tech-writer"] = {
            "kernel": writer_kernel,
            "name": "Tech Writer",
            "system_prompt": "You are a technical documentation specialist. Create clear, comprehensive documentation in markdown format."
        }
        
        # Task Planner Agent
        planner_kernel = Kernel()
        planner_kernel.add_service(
            OllamaChatCompletion(
                service_id="task-planner",
                ai_model_id="llama3.1",
                host="http://localhost:11434"
            )
        )
        self.agents["task-planner"] = {
            "kernel": planner_kernel,
            "name": "Task Planner",
            "system_prompt": "You are a strategic task planner. Break down complex goals into clear, actionable steps."
        }
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    async def invoke_agent(self, agent_id: str, prompt: str, context: Optional[str] = None) -> str:
        """Invoke a specific agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        kernel = agent["kernel"]
        
        # Create chat history with system prompt
        chat_history = ChatHistory()
        chat_history.add_system_message(agent["system_prompt"])
        
        if context:
            chat_history.add_user_message(f"Context: {context}")
        
        chat_history.add_user_message(prompt)
        
        # Get chat completion service
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
        
        # Execute
        settings = OpenAIChatPromptExecutionSettings(
            max_tokens=2000,
            temperature=0.7
        )
        
        response = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=settings,
            kernel=kernel
        )
        
        return str(response)

# Initialize agent service
agent_service = AgentService()

# Register agents with registry on startup
@app.on_event("startup")
async def register_agents_on_startup():
    """Register agents with the registry on startup"""
    try:
        from models import AgentMetadata, AgentType, CapabilityDefinition, AgentStatus
        from registry import get_registry
        
        registry = get_registry()
        base_url = "http://localhost:8000"
        
        # Register Llama Coder
        coder = AgentMetadata(
            id="llama-coder-live",
            name="Llama Coder",
            version="1.0.0",
            description="An AI agent powered by Llama 3.1 specialized in writing, debugging, and explaining Python code.",
            owner="Engineering Team",
            status=AgentStatus.ACTIVE,
            agent_type=AgentType.LLM,
            endpoint=f"{base_url}/agents/llama-coder/invoke",
            tags=["python", "coding", "llama3.1", "development"],
            capabilities=[
                CapabilityDefinition(
                    name="Write Code",
                    description="Generates Python code based on natural language description.",
                    category="Development"
                )
            ]
        )
        registry.register_agent(coder)
        
        # Register Tech Writer
        writer = AgentMetadata(
            id="tech-writer-live",
            name="Tech Writer",
            version="1.0.0",
            description="A documentation specialist agent using Llama 3.1 to create clear technical documentation.",
            owner="Docs Team",
            status=AgentStatus.ACTIVE,
            agent_type=AgentType.LLM,
            endpoint=f"{base_url}/agents/tech-writer/invoke",
            tags=["writing", "documentation", "llama3.1", "technical"],
            capabilities=[
                CapabilityDefinition(
                    name="Generate Documentation",
                    description="Creates markdown documentation for code or systems.",
                    category="Documentation"
                )
            ]
        )
        registry.register_agent(writer)
        
        # Register Task Planner
        planner = AgentMetadata(
            id="task-planner-live",
            name="Task Planner",
            version="1.0.0",
            description="A strategic agent that breaks down complex goals into actionable steps.",
            owner="Product Team",
            status=AgentStatus.ACTIVE,
            agent_type=AgentType.MULTI_AGENT,
            endpoint=f"{base_url}/agents/task-planner/invoke",
            tags=["planning", "strategy", "orchestration"],
            capabilities=[
                CapabilityDefinition(
                    name="Create Plan",
                    description="Decomposes a high-level goal into a list of tasks.",
                    category="Planning"
                )
            ]
        )
        registry.register_agent(planner)
        
        logger.info("Registered 3 agents with the registry")
    except Exception as e:
        logger.error(f"Failed to register agents: {e}")

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents": list(agent_service.agents.keys()),
        "agent_count": len(agent_service.agents)
    }

# Agent invocation endpoints
@app.post("/agents/llama-coder/invoke", response_model=AgentResponse)
async def invoke_llama_coder(request: AgentRequest):
    """Invoke the Llama Coder agent"""
    try:
        response = await agent_service.invoke_agent("llama-coder", request.prompt, request.context)
        return AgentResponse(agent_name="Llama Coder", response=response)
    except Exception as e:
        logger.error(f"Error invoking llama-coder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/tech-writer/invoke", response_model=AgentResponse)
async def invoke_tech_writer(request: AgentRequest):
    """Invoke the Tech Writer agent"""
    try:
        response = await agent_service.invoke_agent("tech-writer", request.prompt, request.context)
        return AgentResponse(agent_name="Tech Writer", response=response)
    except Exception as e:
        logger.error(f"Error invoking tech-writer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/task-planner/invoke", response_model=AgentResponse)
async def invoke_task_planner(request: AgentRequest):
    """Invoke the Task Planner agent"""
    try:
        response = await agent_service.invoke_agent("task-planner", request.prompt, request.context)
        return AgentResponse(agent_name="Task Planner", response=response)
    except Exception as e:
        logger.error(f"Error invoking task-planner: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
