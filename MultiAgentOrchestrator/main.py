"""
AI Agentic Framework - Main entry point
"""
import asyncio
import logging
from typing import Optional
from pathlib import Path

from .models import AgentConfig
from .core import AgentManager, PromptManager, ToolManager, RAGManager
from .services import LoggingService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class AgentFramework:
    """Main framework class - orchestrates all components"""
    
    def __init__(
        self,
        log_directory: str = "./logs",
        rag_persist_directory: str = "./chroma_db"
    ):
        """Initialize the agent framework"""
        logger.info("Initializing AI Agentic Framework...")
        
        # Initialize services
        self.logging_service = LoggingService(log_directory=log_directory)
        
        # Initialize core managers
        self.prompt_manager = PromptManager()
        self.tool_manager = ToolManager()
        self.rag_manager = RAGManager(persist_directory=rag_persist_directory)
        
        # Initialize agent manager with dependencies
        self.agent_manager = AgentManager(
            prompt_manager=self.prompt_manager,
            tool_manager=self.tool_manager,
            rag_manager=self.rag_manager
        )
        
        logger.info("Framework initialized successfully")
    
    def create_agent(self, config: AgentConfig) -> str:
        """Create and register a new agent"""
        agent_id = self.agent_manager.register_agent(config)
        logger.info(f"Created agent: {config.agent_name} ({agent_id})")
        return agent_id
    
    async def deploy_agent(self, agent_id: str):
        """Deploy an agent (make it active and ready to use)"""
        agent = await self.agent_manager.deploy_agent(agent_id)
        logger.info(f"Deployed agent: {agent_id}")
        return agent
    
    async def create_and_deploy_agent(self, config: AgentConfig):
        """Create and immediately deploy an agent"""
        agent_id = self.create_agent(config)
        agent = await self.deploy_agent(agent_id)
        return agent
    
    def get_agent(self, agent_id: str):
        """Get an active agent"""
        return self.agent_manager.get_agent(agent_id)
    
    def list_agents(self, status: Optional[str] = None):
        """List all registered agents"""
        return self.agent_manager.list_agents(status)
    
    def retire_agent(self, agent_id: str):
        """Retire an agent"""
        self.agent_manager.retire_agent(agent_id)
        logger.info(f"Retired agent: {agent_id}")
    
    # Prompt management
    def create_prompt_template(self, template_id: str, name: str, description: str, 
                               template: str, variables: list, category: str = "custom"):
        """Create a new prompt template"""
        return self.prompt_manager.create_template(
            template_id, name, description, template, variables, category
        )
    
    def list_prompt_templates(self, category: Optional[str] = None):
        """List prompt templates"""
        return self.prompt_manager.list_templates(category)
    
    # Tool management
    def register_tool(self, tool_def, executor=None):
        """Register a new tool"""
        self.tool_manager.register_tool(tool_def, executor)
    
    def list_tools(self, category: Optional[str] = None):
        """List available tools"""
        return self.tool_manager.list_tools(category=category)
    
    # RAG management
    def add_rag_source(self, source_id: str, name: str, collection_name: str,
                       embedding_model: str = "all-MiniLM-L6-v2"):
        """Add a RAG knowledge source"""
        self.rag_manager.add_source(source_id, name, collection_name, embedding_model)
    
    async def add_documents_to_rag(self, source_id: str, documents: list, 
                                   metadatas: Optional[list] = None):
        """Add documents to a RAG source"""
        await self.rag_manager.add_documents(source_id, documents, metadatas)
    
    def list_rag_sources(self):
        """List RAG sources"""
        return self.rag_manager.list_sources()
    
    # Logging and evaluation
    def get_agent_logs(self, agent_id: str, limit: int = 100):
        """Get logs for an agent"""
        return self.logging_service.get_logs(agent_id=agent_id, limit=limit)
    
    def generate_agent_report(self, agent_id: str, time_range: tuple):
        """Generate performance report for an agent"""
        return self.logging_service.generate_report(agent_id, time_range)
    
    def get_agent_status(self, agent_id: str):
        """Get comprehensive agent status"""
        return self.agent_manager.get_agent_status(agent_id)
    
    async def execute_agent(self, agent_id: str, user_input: str, context: dict = None):
        """Execute an agent with user input"""
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found or not deployed")
        
        # Execute
        response = await agent.execute(user_input, context)
        
        # Log interaction
        self.logging_service.log_interaction(
            agent_id=agent_id,
            user_input=user_input,
            agent_response=response,
            tools_used=[],  # Would be populated by agent
            rag_sources=agent.config.capabilities.rag_sources
        )
        
        return response
    
    # Convenience method for quick agent creation
    @staticmethod
    def quick_agent(
        name: str,
        description: str,
        model: str = "llama3.1",
        temperature: float = 0.7,
        tools: list = None,
        rag_sources: list = None
    ) -> AgentConfig:
        """Quickly create an agent config with common settings"""
        from .models import AgentCapabilities, AgentBehavior
        
        config = AgentConfig(
            agent_name=name,
            agent_description=description,
            capabilities=AgentCapabilities(
                prompts=["general_assistant"],
                tools=tools or [],
                rag_sources=rag_sources or []
            ),
            behavior=AgentBehavior(
                model=model,
                temperature=temperature
            )
        )
        
        return config


# Example helper function
async def create_simple_agent(
    framework: AgentFramework,
    name: str,
    description: str,
    model: str = "llama3.1"
):
    """Helper to create a simple agent"""
    config = AgentFramework.quick_agent(name, description, model)
    agent = await framework.create_and_deploy_agent(config)
    return agent


__all__ = [
    'AgentFramework',
    'create_simple_agent'
]
