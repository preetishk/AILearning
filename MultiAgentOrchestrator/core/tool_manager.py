"""
Tool Manager - Manages tool registry and execution with MCP support
"""
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import json
import subprocess

from ..models import ToolDefinition, ToolResult, ToolType, MCPConfig


logger = logging.getLogger(__name__)


class MCPClient:
    """Client for Model Context Protocol (MCP) server communication"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.connected = False
        logger.info(f"MCPClient initialized for {config.server_name}")
    
    async def connect(self):
        """Establish connection to MCP server"""
        try:
            if self.config.transport == "stdio":
                # Start MCP server as subprocess with stdio communication
                if not self.config.command:
                    raise ValueError("stdio transport requires command")
                
                self.process = subprocess.Popen(
                    [self.config.command] + self.config.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={**subprocess.os.environ, **self.config.env},
                    text=True
                )
                self.connected = True
                logger.info(f"MCP server {self.config.server_name} started via stdio")
            
            elif self.config.transport == "sse":
                # SSE-based MCP connection (HTTP streaming)
                if not self.config.server_url:
                    raise ValueError("SSE transport requires server_url")
                logger.info(f"MCP SSE connection to {self.config.server_url}")
                self.connected = True
            
            elif self.config.transport == "websocket":
                # WebSocket-based MCP connection
                if not self.config.server_url:
                    raise ValueError("WebSocket transport requires server_url")
                logger.info(f"MCP WebSocket connection to {self.config.server_url}")
                self.connected = True
            
            else:
                raise ValueError(f"Unsupported transport: {self.config.transport}")
        
        except Exception as e:
            logger.error(f"MCP connection failed: {e}")
            raise
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool via MCP protocol"""
        if not self.connected:
            await self.connect()
        
        try:
            if self.config.transport == "stdio":
                # Send JSON-RPC request via stdio
                request = {
                    "jsonrpc": "2.0",
                    "id": f"{tool_name}_{time.time()}",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": parameters
                    }
                }
                
                if self.process and self.process.stdin:
                    self.process.stdin.write(json.dumps(request) + "\n")
                    self.process.stdin.flush()
                    
                    # Read response
                    if self.process.stdout:
                        response_line = self.process.stdout.readline()
                        response = json.loads(response_line)
                        
                        if "error" in response:
                            raise Exception(f"MCP error: {response['error']}")
                        
                        return response.get("result")
                
            elif self.config.transport in ["sse", "websocket"]:
                # For HTTP-based transports, use appropriate client
                # This is a placeholder - actual implementation would use
                # httpx for SSE or websockets library for WebSocket
                logger.warning(f"{self.config.transport} transport not fully implemented")
                return {"status": "placeholder", "message": f"{self.config.transport} execution pending"}
            
        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            raise
    
    async def disconnect(self):
        """Close MCP connection"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.connected = False
            logger.info(f"MCP server {self.config.server_name} disconnected")
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.process and self.process.poll() is None:
            self.process.terminate()


class RateLimiter:
    """Simple rate limiter for tool executions"""
    
    def __init__(self):
        self.call_history: Dict[str, List[datetime]] = defaultdict(list)
    
    def can_execute(self, tool_id: str, rate_limit: Any) -> bool:
        """Check if tool can be executed based on rate limits"""
        now = datetime.utcnow()
        history = self.call_history[tool_id]
        
        # Clean old entries
        history = [t for t in history if now - t < timedelta(days=1)]
        self.call_history[tool_id] = history
        
        # Check limits
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        calls_last_minute = sum(1 for t in history if t > minute_ago)
        calls_last_hour = sum(1 for t in history if t > hour_ago)
        calls_today = len(history)
        
        if calls_last_minute >= rate_limit.calls_per_minute:
            return False
        if calls_last_hour >= rate_limit.calls_per_hour:
            return False
        if calls_today >= rate_limit.calls_per_day:
            return False
        
        return True
    
    def record_call(self, tool_id: str):
        """Record a tool call"""
        self.call_history[tool_id].append(datetime.utcnow())


class ToolManager:
    """Manages tool registry and execution with MCP support"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.executors: Dict[str, Callable] = {}
        self.mcp_clients: Dict[str, MCPClient] = {}  # MCP clients for MCP tools
        self.rate_limiter = RateLimiter()
        self._load_default_tools()
        logger.info("ToolManager initialized with MCP support")
    
    def _load_default_tools(self):
        """Load default built-in tools"""
        # Calculator tool
        calculator = ToolDefinition(
            tool_id="calculator",
            name="Calculator",
            description="Perform basic arithmetic calculations",
            type=ToolType.FUNCTION,
            parameters=[
                {
                    "name": "expression",
                    "type": "string",
                    "description": "Mathematical expression to evaluate",
                    "required": True
                }
            ]
        )
        self.register_tool(calculator, self._calculator_executor)
        
        # Echo tool (for testing)
        echo = ToolDefinition(
            tool_id="echo",
            name="Echo",
            description="Returns the input text",
            type=ToolType.FUNCTION,
            parameters=[
                {
                    "name": "text",
                    "type": "string",
                    "description": "Text to echo",
                    "required": True
                }
            ]
        )
        self.register_tool(echo, self._echo_executor)
    
    async def _calculator_executor(self, expression: str) -> Any:
        """Execute calculator tool"""
        try:
            # Safe eval for basic math
            allowed_chars = "0123456789+-*/()%. "
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")
            
            result = eval(expression, {"__builtins__": {}}, {})
            return result
        except Exception as e:
            raise ValueError(f"Calculation error: {e}")
    
    async def _echo_executor(self, text: str) -> str:
        """Execute echo tool"""
        return text
    
    def register_tool(
        self,
        tool_def: ToolDefinition,
        executor: Optional[Callable] = None
    ):
        """Register a new tool (function-based or MCP-based)"""
        if tool_def.tool_id in self.tools:
            logger.warning(f"Tool {tool_def.tool_id} already exists, overwriting")
        
        self.tools[tool_def.tool_id] = tool_def
        
        # Handle different tool types
        if tool_def.type == ToolType.MCP:
            # Register MCP tool - create MCP client if not exists
            if tool_def.mcp_config:
                if tool_def.mcp_config.server_name not in self.mcp_clients:
                    mcp_client = MCPClient(tool_def.mcp_config)
                    self.mcp_clients[tool_def.mcp_config.server_name] = mcp_client
                    logger.info(f"Created MCP client for {tool_def.mcp_config.server_name}")
        else:
            # Register direct function executor
            if executor:
                self.executors[tool_def.tool_id] = executor
        
        logger.info(f"Registered tool: {tool_def.name} ({tool_def.tool_id}) - Type: {tool_def.type}")
    
    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get a tool definition"""
        return self.tools.get(tool_id)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        tool_type: Optional[ToolType] = None
    ) -> List[ToolDefinition]:
        """List available tools"""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        if tool_type:
            tools = [t for t in tools if t.type == tool_type]
        
        return tools
    
    def validate_tool_call(
        self,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Validate tool call parameters"""
        tool_def = self.get_tool(tool_id)
        if not tool_def:
            return False
        
        # Check required parameters
        param_names = {p.name for p in tool_def.parameters}
        required_params = {p.name for p in tool_def.parameters if p.required}
        
        provided_params = set(parameters.keys())
        
        # Check all required params are provided
        if not required_params.issubset(provided_params):
            missing = required_params - provided_params
            logger.error(f"Missing required parameters: {missing}")
            return False
        
        # Check no unknown params
        if not provided_params.issubset(param_names):
            unknown = provided_params - param_names
            logger.warning(f"Unknown parameters: {unknown}")
        
        return True
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        agent_id: str,
        retry: bool = True
    ) -> ToolResult:
        """Execute a tool (direct function or MCP)"""
        start_time = time.time()
        
        try:
            # Get tool definition
            tool_def = self.get_tool(tool_id)
            if not tool_def:
                return ToolResult(
                    tool_id=tool_id,
                    success=False,
                    error=f"Tool {tool_id} not found"
                )
            
            # Validate parameters
            if not self.validate_tool_call(tool_id, parameters):
                return ToolResult(
                    tool_id=tool_id,
                    success=False,
                    error="Invalid parameters"
                )
            
            # Check rate limits
            if not self.rate_limiter.can_execute(tool_id, tool_def.rate_limit):
                return ToolResult(
                    tool_id=tool_id,
                    success=False,
                    error="Rate limit exceeded"
                )
            
            # Execute based on tool type
            try:
                if tool_def.type == ToolType.MCP:
                    # Execute via MCP
                    result = await self._execute_mcp_tool(tool_def, parameters)
                else:
                    # Execute via direct function
                    result = await self._execute_direct_tool(tool_def, parameters)
                
                # Record successful call
                self.rate_limiter.record_call(tool_id)
                
                execution_time = (time.time() - start_time) * 1000
                
                return ToolResult(
                    tool_id=tool_id,
                    success=True,
                    result=result,
                    execution_time_ms=execution_time,
                    cost=tool_def.cost_per_call
                )
                
            except asyncio.TimeoutError:
                return ToolResult(
                    tool_id=tool_id,
                    success=False,
                    error=f"Tool execution timeout after {tool_def.timeout_seconds}s"
                )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            
            # Retry if enabled
            if retry and tool_def.retry_on_failure and tool_def.max_retries > 0:
                logger.info(f"Retrying tool {tool_id}...")
                await asyncio.sleep(1)  # Simple backoff
                return await self.execute_tool(
                    tool_id, parameters, agent_id, retry=False
                )
            
            execution_time = (time.time() - start_time) * 1000
            return ToolResult(
                tool_id=tool_id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    async def _execute_direct_tool(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute a direct function tool"""
        executor = self.executors.get(tool_def.tool_id)
        if not executor:
            raise ValueError(f"No executor found for tool {tool_def.tool_id}")
        
        # Execute with timeout
        result = await asyncio.wait_for(
            executor(**parameters),
            timeout=tool_def.timeout_seconds
        )
        return result
    
    async def _execute_mcp_tool(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute a tool via MCP protocol"""
        if not tool_def.mcp_config:
            raise ValueError(f"Tool {tool_def.tool_id} has no MCP config")
        
        # Get or create MCP client
        mcp_client = self.mcp_clients.get(tool_def.mcp_config.server_name)
        if not mcp_client:
            mcp_client = MCPClient(tool_def.mcp_config)
            self.mcp_clients[tool_def.mcp_config.server_name] = mcp_client
        
        # Execute with timeout
        result = await asyncio.wait_for(
            mcp_client.execute_tool(tool_def.name, parameters),
            timeout=tool_def.timeout_seconds
        )
        return result
    
    def get_available_tools(self, agent_id: str) -> List[str]:
        """Get list of tools available to an agent"""
        # In production, check permissions
        # For now, return all tools
        return list(self.tools.keys())
    
    def create_semantic_kernel_function(self, tool_id: str):
        """Create a Semantic Kernel function from tool definition"""
        # This would create an SK-compatible function
        # For now, return the executor
        return self.executors.get(tool_id)
    
    async def cleanup(self):
        """Cleanup resources, disconnect MCP clients"""
        logger.info("Cleaning up ToolManager resources...")
        for server_name, client in self.mcp_clients.items():
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MCP client {server_name}: {e}")
