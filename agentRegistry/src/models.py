from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid

class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"

class AgentType(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    CLASSIFIER = "classifier"
    ROUTER = "router"
    MULTI_AGENT = "multi_agent"

class ParameterDefinition(BaseModel):
    name: str
    type: str
    required: bool = True
    description: str
    default: Optional[Any] = None

class CapabilityDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str = "General"
    parameters: List[ParameterDefinition] = []
    tags: List[str] = []

class AgentMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: str
    owner: str = "System"
    status: AgentStatus = AgentStatus.ACTIVE
    agent_type: AgentType = AgentType.TOOL
    endpoint: Optional[str] = None
    tags: List[str] = []
    
    capabilities: List[CapabilityDefinition] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
