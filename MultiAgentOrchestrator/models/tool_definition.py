"""
Tool definition models for the AI Agentic Framework
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime


class ToolType(str, Enum):
    """Tool type enum"""
    FUNCTION = "function"
    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    MCP = "mcp"  # Model Context Protocol
    CUSTOM = "custom"


class ParameterType(str, Enum):
    """Parameter type enum"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ParameterDefinition(BaseModel):
    """Tool parameter definition"""
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enum_values: Optional[List[Any]] = None


class AuthConfig(BaseModel):
    """Authentication configuration for tools"""
    type: str = Field(default="none", description="Auth type: none, api_key, oauth, basic")
    credentials_key: Optional[str] = Field(default=None, description="Environment variable for credentials")


class MCPConfig(BaseModel):
    """MCP-specific configuration"""
    server_name: str = Field(..., description="MCP server name")
    server_url: Optional[str] = Field(default=None, description="MCP server URL (if remote)")
    transport: str = Field(default="stdio", description="Transport type: stdio, sse, websocket")
    command: Optional[str] = Field(default=None, description="Command to start MCP server (for stdio)")
    args: List[str] = Field(default_factory=list, description="Arguments for server command")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    

class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    calls_per_minute: int = Field(default=60, ge=1)
    calls_per_hour: int = Field(default=3600, ge=1)
    calls_per_day: int = Field(default=10000, ge=1)


class ToolDefinition(BaseModel):
    """Complete tool definition"""
    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    version: str = Field(default="1.0.0")
    type: ToolType = Field(default=ToolType.FUNCTION)
    
    # Function/API configuration
    endpoint: Optional[str] = Field(default=None, description="API endpoint or function path")
    method: Optional[str] = Field(default="POST", description="HTTP method for API calls")
    
    # Parameters
    parameters: List[ParameterDefinition] = Field(default_factory=list)
    
    # Auth and limits
    authentication: AuthConfig = Field(default_factory=AuthConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    
    # MCP-specific configuration
    mcp_config: Optional[MCPConfig] = Field(default=None, description="MCP server configuration")
    
    # Permissions and cost
    permissions_required: List[str] = Field(default_factory=list)
    cost_per_call: float = Field(default=0.0, ge=0.0, description="Cost in USD per call")
    
    # Runtime
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0, le=10)
    
    # Metadata
    category: str = Field(default="general")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_id": "web_search",
                "name": "Web Search",
                "description": "Search the web for information",
                "type": "api",
                "endpoint": "https://api.search.com/v1/search",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "Search query",
                        "required": True
                    },
                    {
                        "name": "max_results",
                        "type": "integer",
                        "description": "Maximum number of results",
                        "required": False,
                        "default": 10
                    }
                ]
            }
        }
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for parameters"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.enum_values:
                properties[param.name]["enum"] = param.enum_values
            if param.required:
                required.append(param.name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }


class ToolResult(BaseModel):
    """Tool execution result"""
    tool_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cost: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_id": self.tool_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "cost": self.cost,
            "timestamp": self.timestamp.isoformat()
        }
