"""
Agent Manager - Core component for agent lifecycle management
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import semantic_kernel as sk
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.contents import ChatHistory

from ..models import AgentConfig, AgentState, AgentStatus
from .prompt_manager import PromptManager
from .tool_manager import ToolManager
from .rag_manager import RAGManager


logger = logging.getLogger(__name__)


class Agent:
    """Individual agent instance with Semantic Kernel integration"""
    
    def __init__(
        self,
        config: AgentConfig,
        kernel: sk.Kernel,
        prompt_manager: PromptManager,
        tool_manager: ToolManager,
        rag_manager: Optional[RAGManager] = None
    ):
        self.config = config
        self.kernel = kernel
        self.prompt_manager = prompt_manager
        self.tool_manager = tool_manager
        self.rag_manager = rag_manager
        self.state = AgentState(agent_id=config.agent_id)
        self.chat_history = ChatHistory()
        
        # Configure kernel with Ollama
        self._setup_kernel()
    
    def _setup_kernel(self):
        """Setup Semantic Kernel with Ollama"""
        service_id = f"ollama_{self.config.behavior.model}"
        
        # Add Ollama chat completion service
        self.kernel.add_service(
            OllamaChatCompletion(
                service_id=service_id,
                ai_model_id=self.config.behavior.model,
                url="http://localhost:11434"  # Default Ollama URL
            )
        )
        
        # Register tools as plugins
        self._register_tools_as_plugins()
    
    def _register_tools_as_plugins(self):
        """Register available tools as Semantic Kernel plugins"""
        for tool_id in self.config.capabilities.tools:
            try:
                tool_def = self.tool_manager.get_tool(tool_id)
                if tool_def:
                    # Create a plugin function for this tool
                    plugin_func = self._create_plugin_function(tool_def)
                    # Register with kernel (simplified - actual implementation would use SK decorators)
                    logger.info(f"Registered tool {tool_id} as plugin for agent {self.config.agent_name}")
            except Exception as e:
                logger.error(f"Failed to register tool {tool_id}: {e}")
    
    def _create_plugin_function(self, tool_def):
        """Create a Semantic Kernel plugin function from tool definition"""
        async def plugin_function(**kwargs):
            result = await self.tool_manager.execute_tool(
                tool_def.tool_id,
                kwargs,
                self.config.agent_id
            )
            return result.result if result.success else None
        
        return plugin_function
    
    async def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        use_rag: bool = True
    ) -> str:
        """Execute agent with user input"""
        try:
            # Update state
            self.config.status = AgentStatus.ACTIVE
            
            # Retrieve RAG context if enabled
            rag_context = ""
            if use_rag and self.rag_manager and self.config.capabilities.rag_sources:
                rag_results = await self.rag_manager.retrieve_context(
                    query=user_input,
                    agent_id=self.config.agent_id,
                    sources=self.config.capabilities.rag_sources
                )
                rag_context = rag_results.get('context', '')
            
            # Generate prompt using prompt manager
            prompt = await self._generate_prompt(user_input, context or {}, rag_context)
            
            # Add to chat history
            self.chat_history.add_user_message(user_input)
            
            # Execute with Semantic Kernel
            response = await self._execute_with_kernel(prompt)
            
            # Add assistant response to history
            self.chat_history.add_assistant_message(response)
            
            # Update state
            self.state.add_interaction(
                user_input=user_input,
                assistant_response=response,
                tokens_used=len(prompt.split()) + len(response.split()),  # Rough estimate
                cost=0.0  # Ollama is free
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            self.config.status = AgentStatus.ERROR
            raise
    
    async def _generate_prompt(
        self,
        user_input: str,
        context: Dict[str, Any],
        rag_context: str
    ) -> str:
        """Generate prompt using prompt manager"""
        # Use first prompt template if available
        if self.config.capabilities.prompts:
            template_id = self.config.capabilities.prompts[0]
            
            # Build context
            full_context = {
                **context,
                'user_input': user_input,
                'rag_context': rag_context,
                'agent_name': self.config.agent_name,
                'agent_description': self.config.agent_description
            }
            
            return await self.prompt_manager.generate_prompt(
                template_id=template_id,
                context=full_context,
                history=self.state.conversation_history
            )
        else:
            # Default prompt
            base_prompt = f"You are {self.config.agent_name}. {self.config.agent_description}\n\n"
            if rag_context:
                base_prompt += f"Context:\n{rag_context}\n\n"
            base_prompt += f"User: {user_input}\n\nAssistant:"
            return base_prompt
    
    async def _execute_with_kernel(self, prompt: str) -> str:
        """Execute prompt with Semantic Kernel"""
        try:
            # Get the chat completion service
            chat_service = self.kernel.get_service(type=OllamaChatCompletion)
            
            # Create settings
            settings = sk.PromptExecutionSettings(
                service_id=f"ollama_{self.config.behavior.model}",
                extension_data={
                    "temperature": self.config.behavior.temperature,
                    "max_tokens": self.config.behavior.max_tokens,
                    "top_p": self.config.behavior.top_p,
                    "top_k": self.config.behavior.top_k,
                }
            )
            
            # Execute
            result = await chat_service.get_chat_message_contents(
                chat_history=self.chat_history,
                settings=settings
            )
            
            # Extract response
            if result and len(result) > 0:
                return str(result[0].content)
            return ""
            
        except Exception as e:
            logger.error(f"Kernel execution failed: {e}")
            raise
    
    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state
    
    def reset_state(self):
        """Reset agent state"""
        self.state = AgentState(agent_id=self.config.agent_id)
        self.chat_history = ChatHistory()


class AgentManager:
    """Manages agent lifecycle and registry"""
    
    def __init__(
        self,
        prompt_manager: PromptManager,
        tool_manager: ToolManager,
        rag_manager: Optional[RAGManager] = None
    ):
        self.prompt_manager = prompt_manager
        self.tool_manager = tool_manager
        self.rag_manager = rag_manager
        
        self.registry: Dict[str, AgentConfig] = {}
        self.active_agents: Dict[str, Agent] = {}
        
        logger.info("AgentManager initialized")
    
    def register_agent(self, config: AgentConfig) -> str:
        """Register a new agent"""
        if config.agent_id in self.registry:
            raise ValueError(f"Agent {config.agent_id} already registered")
        
        self.registry[config.agent_id] = config
        config.status = AgentStatus.CREATED
        
        logger.info(f"Registered agent: {config.agent_name} ({config.agent_id})")
        return config.agent_id
    
    async def deploy_agent(self, agent_id: str) -> Agent:
        """Deploy an agent (make it active)"""
        if agent_id not in self.registry:
            raise ValueError(f"Agent {agent_id} not found in registry")
        
        if agent_id in self.active_agents:
            logger.warning(f"Agent {agent_id} already deployed")
            return self.active_agents[agent_id]
        
        config = self.registry[agent_id]
        
        # Create Semantic Kernel instance
        kernel = sk.Kernel()
        
        # Create agent instance
        agent = Agent(
            config=config,
            kernel=kernel,
            prompt_manager=self.prompt_manager,
            tool_manager=self.tool_manager,
            rag_manager=self.rag_manager
        )
        
        self.active_agents[agent_id] = agent
        config.status = AgentStatus.DEPLOYED
        
        logger.info(f"Deployed agent: {config.agent_name} ({agent_id})")
        return agent
    
    def retire_agent(self, agent_id: str):
        """Retire an agent (remove from active agents)"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            if agent_id in self.registry:
                self.registry[agent_id].status = AgentStatus.RETIRED
            logger.info(f"Retired agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an active agent"""
        return self.active_agents.get(agent_id)
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration"""
        return self.registry.get(agent_id)
    
    def list_agents(self, status: Optional[AgentStatus] = None) -> List[AgentConfig]:
        """List all registered agents, optionally filtered by status"""
        if status:
            return [
                config for config in self.registry.values()
                if config.status == status
            ]
        return list(self.registry.values())
    
    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]):
        """Update agent configuration"""
        if agent_id not in self.registry:
            raise ValueError(f"Agent {agent_id} not found")
        
        config = self.registry[agent_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.update_timestamp()
        logger.info(f"Updated agent config: {agent_id}")
    
    async def route_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[Agent, str]:
        """Route a request to the most appropriate agent"""
        # Simple routing - in production, use semantic similarity or other logic
        if not self.active_agents:
            raise ValueError("No active agents available")
        
        # For now, route to first active agent
        # TODO: Implement intelligent routing based on agent capabilities
        agent_id = list(self.active_agents.keys())[0]
        agent = self.active_agents[agent_id]
        
        response = await agent.execute(request, context)
        return agent, response
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed agent status"""
        config = self.registry.get(agent_id)
        if not config:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.active_agents.get(agent_id)
        
        status = {
            "agent_id": agent_id,
            "agent_name": config.agent_name,
            "status": config.status,
            "version": config.version,
            "is_active": agent is not None,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
        
        if agent:
            state = agent.get_state()
            status.update({
                "total_interactions": state.interaction_count,
                "total_tokens_used": state.total_tokens_used,
                "total_cost": state.total_cost,
                "last_interaction": state.last_interaction.isoformat() if state.last_interaction else None
            })
        
        return status
