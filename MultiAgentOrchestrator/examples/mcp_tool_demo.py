"""
MCP Tool Integration Demo

This example demonstrates how to use MCP (Model Context Protocol) tools
alongside direct function tools in the framework.

MCP allows agents to interact with external servers and services using
a standardized protocol, enabling:
- File system operations
- Database access
- API integrations
- Custom tool servers
"""

import asyncio
from MultiAgentOrchestrator.models import (
    AgentConfig,
    ToolDefinition,
    ToolType,
    MCPConfig,
    PromptTemplate
)
from MultiAgentOrchestrator.core import AgentManager, ToolManager


async def custom_weather_tool(location: str) -> str:
    """Custom direct function tool for weather"""
    # Simulate weather lookup
    return f"Weather in {location}: Sunny, 72°F"


async def main():
    print("=" * 60)
    print("MCP TOOL INTEGRATION DEMO")
    print("=" * 60)
    
    # Initialize managers
    agent_manager = AgentManager()
    tool_manager = ToolManager()
    
    # 1. Register a DIRECT FUNCTION tool
    print("\n1. Registering Direct Function Tool...")
    weather_tool = ToolDefinition(
        tool_id="weather",
        name="Weather Lookup",
        description="Get current weather for a location",
        type=ToolType.FUNCTION,
        parameters=[
            {
                "name": "location",
                "type": "string",
                "description": "City or location name",
                "required": True
            }
        ]
    )
    tool_manager.register_tool(weather_tool, custom_weather_tool)
    print(f"   ✓ Registered: {weather_tool.name} (Direct Function)")
    
    # 2. Register an MCP tool (filesystem example)
    print("\n2. Registering MCP Tool...")
    
    # Example MCP configuration for a filesystem server
    # This would typically be a separate MCP server process
    filesystem_mcp_config = MCPConfig(
        server_name="filesystem",
        transport="stdio",  # Use stdio for local communication
        command="npx",  # Or path to your MCP server executable
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        env={}
    )
    
    filesystem_tool = ToolDefinition(
        tool_id="mcp_read_file",
        name="MCP File Reader",
        description="Read file contents using MCP filesystem server",
        type=ToolType.MCP,
        mcp_config=filesystem_mcp_config,
        parameters=[
            {
                "name": "path",
                "type": "string",
                "description": "File path to read",
                "required": True
            }
        ]
    )
    tool_manager.register_tool(filesystem_tool)
    print(f"   ✓ Registered: {filesystem_tool.name} (MCP)")
    print(f"     Server: {filesystem_mcp_config.server_name}")
    print(f"     Transport: {filesystem_mcp_config.transport}")
    
    # 3. Register another MCP tool (database example)
    print("\n3. Registering Another MCP Tool (Database)...")
    
    database_mcp_config = MCPConfig(
        server_name="database",
        server_url="http://localhost:3000/mcp",
        transport="sse",  # HTTP Server-Sent Events
        command=None,  # No command needed for remote server
        args=[],
        env={}
    )
    
    database_tool = ToolDefinition(
        tool_id="mcp_query_db",
        name="MCP Database Query",
        description="Execute database queries via MCP",
        type=ToolType.MCP,
        mcp_config=database_mcp_config,
        parameters=[
            {
                "name": "query",
                "type": "string",
                "description": "SQL query to execute",
                "required": True
            }
        ]
    )
    tool_manager.register_tool(database_tool)
    print(f"   ✓ Registered: {database_tool.name} (MCP)")
    print(f"     Server: {database_mcp_config.server_name}")
    print(f"     Transport: {database_mcp_config.transport}")
    print(f"     URL: {database_mcp_config.server_url}")
    
    # 4. List all tools
    print("\n4. All Registered Tools:")
    all_tools = tool_manager.list_tools()
    for tool in all_tools:
        tool_type_display = "📞 Direct" if tool.type == ToolType.FUNCTION else "🔌 MCP"
        print(f"   {tool_type_display} {tool.name} ({tool.tool_id})")
    
    # 5. Create agent with mixed tools
    print("\n5. Creating Agent with Mixed Tools...")
    agent_config = AgentConfig(
        agent_id="mixed_agent",
        name="Mixed Tools Agent",
        description="Agent using both direct and MCP tools",
        model_name="llama3.1",
        tools=["weather", "calculator", "mcp_read_file"]  # Mix of direct and MCP
    )
    agent = await agent_manager.deploy_agent(agent_config)
    print(f"   ✓ Deployed: {agent.config.name}")
    print(f"     Tools: {len(agent.config.tools)}")
    
    # 6. Execute direct function tool
    print("\n6. Testing Direct Function Tool...")
    try:
        result = await tool_manager.execute_tool(
            tool_id="weather",
            parameters={"location": "San Francisco"},
            agent_id="mixed_agent"
        )
        if result.success:
            print(f"   ✓ Success: {result.result}")
            print(f"     Execution time: {result.execution_time_ms:.2f}ms")
        else:
            print(f"   ✗ Failed: {result.error}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 7. Execute MCP tool (note: requires actual MCP server running)
    print("\n7. Testing MCP Tool...")
    print("   Note: This requires an actual MCP server to be running.")
    print("   For demonstration, showing how it would be called:")
    print("   ")
    print("   result = await tool_manager.execute_tool(")
    print("       tool_id='mcp_read_file',")
    print("       parameters={'path': '/tmp/test.txt'},")
    print("       agent_id='mixed_agent'")
    print("   )")
    
    # 8. Show MCP vs Direct comparison
    print("\n8. MCP vs Direct Function Tools:")
    print("   ")
    print("   DIRECT FUNCTION TOOLS:")
    print("   ✓ Fast - no network overhead")
    print("   ✓ Simple - just Python functions")
    print("   ✓ Secure - runs in same process")
    print("   ✗ Limited to Python ecosystem")
    print("   ✗ No standardized interface")
    print("   ")
    print("   MCP TOOLS:")
    print("   ✓ Standardized protocol")
    print("   ✓ Language agnostic")
    print("   ✓ Can connect to remote services")
    print("   ✓ Ecosystem of pre-built servers")
    print("   ✗ Slightly more overhead")
    print("   ✗ Requires MCP server running")
    
    # 9. Show use cases
    print("\n9. When to Use Each Type:")
    print("   ")
    print("   Use DIRECT FUNCTIONS for:")
    print("   • Simple calculations or transformations")
    print("   • Python-specific operations")
    print("   • High-performance requirements")
    print("   • Embedded/local-only tools")
    print("   ")
    print("   Use MCP TOOLS for:")
    print("   • File system operations")
    print("   • Database access")
    print("   • External API integrations")
    print("   • Cross-language tool sharing")
    print("   • Pre-built tool servers (npm packages, etc.)")
    
    # Cleanup
    print("\n10. Cleanup...")
    await tool_manager.cleanup()
    print("   ✓ MCP clients disconnected")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
