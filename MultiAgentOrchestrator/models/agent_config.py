"""
Core models and schemas for the AI Agentic Framework
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class AgentStatus(str, Enum):
    """Agent status enum"""
    CREATED = "created"
    DEPLOYED = "deployed"
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"
    ERROR = "error"


class AgentCapabilities(BaseModel):
    """Agent capabilities configuration"""
    prompts: List[str] = Field(default_factory=list, description="Prompt template IDs")
    tools: List[str] = Field(default_factory=list, description="Tool IDs")
    rag_sources: List[str] = Field(default_factory=list, description="RAG source IDs")
    max_iterations: int = Field(default=10, description="Max iterations for planning")
    timeout_seconds: int = Field(default=300, description="Execution timeout")


class AgentBehavior(BaseModel):
    """Agent behavior configuration"""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    model: str = Field(default="llama3.1", description="LLM model name")
    fallback_model: Optional[str] = Field(default=None, description="Fallback model")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=0, le=100)
    stream: bool = Field(default=False, description="Enable streaming responses")


class AgentPermissions(BaseModel):
    """Agent permissions and access control"""
    allowed_tools: List[str] = Field(default_factory=list)
    restricted_tools: List[str] = Field(default_factory=list)
    data_access_level: str = Field(default="team", description="Access level: public, team, private")
    max_cost_per_day: float = Field(default=10.0, description="Max cost in USD per day")


class AgentLogging(BaseModel):
    """Agent logging configuration"""
    level: str = Field(default="info", description="Logging level")
    retention_days: int = Field(default=90, description="Log retention period")
    evaluation_enabled: bool = Field(default=True, description="Enable evaluation")
    trace_enabled: bool = Field(default=True, description="Enable tracing")


class AgentMetadata(BaseModel):
    """Agent metadata"""
    owner: str = Field(default="", description="Agent owner")
    department: str = Field(default="", description="Department")
    tags: List[str] = Field(default_factory=list, description="Agent tags")
    created_by: str = Field(default="system", description="Creator")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Complete agent configuration"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique agent ID")
    agent_name: str = Field(..., description="Agent name")
    agent_description: str = Field(..., description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: AgentStatus = Field(default=AgentStatus.CREATED)
    
    metadata: AgentMetadata = Field(default_factory=AgentMetadata)
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    behavior: AgentBehavior = Field(default_factory=AgentBehavior)
    permissions: AgentPermissions = Field(default_factory=AgentPermissions)
    logging: AgentLogging = Field(default_factory=AgentLogging)
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "customer_support_agent",
                "agent_description": "Handles customer inquiries and support tickets",
                "version": "1.0.0",
                "metadata": {
                    "owner": "support_team",
                    "department": "customer_service",
                    "tags": ["support", "customer"]
                },
                "behavior": {
                    "temperature": 0.7,
                    "model": "llama3.1"
                }
            }
        }
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
    
    @validator('agent_name')
    def validate_agent_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Agent name cannot be empty')
        return v.strip().lower().replace(' ', '_')


class AgentState(BaseModel):
    """Runtime agent state"""
    agent_id: str
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    total_tokens_used: int = 0
    total_cost: float = 0.0
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    
    def add_interaction(self, user_input: str, assistant_response: str, tokens_used: int = 0, cost: float = 0.0):
        """Add an interaction to the state"""
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.total_tokens_used += tokens_used
        self.total_cost += cost
        self.interaction_count += 1
        self.last_interaction = datetime.utcnow()
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.interaction_count = 0
