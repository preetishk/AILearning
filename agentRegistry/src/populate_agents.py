import asyncio
from models import AgentMetadata, AgentType, CapabilityDefinition, ParameterDefinition, AgentStatus
from registry import get_registry

async def populate():
    registry = get_registry()
    
    # 1. Python Coder Agent
    coder = AgentMetadata(
        name="Llama Coder",
        version="1.0.0",
        description="An AI agent powered by Llama 3.1 specialized in writing, debugging, and explaining Python code.",
        owner="Engineering Team",
        status=AgentStatus.ACTIVE,
        agent_type=AgentType.LLM,
        tags=["python", "coding", "llama3.1", "development"],
        capabilities=[
            CapabilityDefinition(
                name="Write Code",
                description="Generates Python code based on natural language description.",
                category="Development",
                parameters=[
                    ParameterDefinition(name="prompt", type="string", description="Description of the code to write")
                ]
            ),
            CapabilityDefinition(
                name="Debug Code",
                description="Analyzes code for errors and suggests fixes.",
                category="Development",
                parameters=[
                    ParameterDefinition(name="code", type="string", description="The source code to debug")
                ]
            )
        ]
    )
    
    # 2. Technical Writer Agent
    writer = AgentMetadata(
        name="Tech Writer",
        version="1.0.0",
        description="A documentation specialist agent using Llama 3.1 to create clear technical documentation.",
        owner="Docs Team",
        status=AgentStatus.ACTIVE,
        agent_type=AgentType.LLM,
        tags=["writing", "documentation", "llama3.1", "technical"],
        capabilities=[
            CapabilityDefinition(
                name="Generate Documentation",
                description="Creates markdown documentation for code or systems.",
                category="Documentation",
                parameters=[
                    ParameterDefinition(name="topic", type="string", description="The topic to document")
                ]
            )
        ]
    )
    
    # 3. Planner Agent
    planner = AgentMetadata(
        name="Task Planner",
        version="0.5.0",
        description="A strategic agent that breaks down complex goals into actionable steps.",
        owner="Product Team",
        status=AgentStatus.ACTIVE,
        agent_type=AgentType.MULTI_AGENT,
        tags=["planning", "strategy", "orchestration"],
        capabilities=[
            CapabilityDefinition(
                name="Create Plan",
                description="Decomposes a high-level goal into a list of tasks.",
                category="Planning",
                parameters=[
                    ParameterDefinition(name="goal", type="string", description="The main objective")
                ]
            )
        ]
    )

    print("Registering agents...")
    
    # Register agents (this will trigger embedding generation in background if loop is running)
    # Since we are in an async function, we can try to ensure it runs.
    # The registry.register_agent is sync wrapper.
    
    id1 = registry.register_agent(coder)
    print(f"Registered {coder.name} with ID: {id1}")
    
    id2 = registry.register_agent(writer)
    print(f"Registered {writer.name} with ID: {id2}")
    
    id3 = registry.register_agent(planner)
    print(f"Registered {planner.name} with ID: {id3}")
    
    # Wait a bit for embeddings to be generated (since they are fire-and-forget in registry)
    print("Waiting for embeddings to be generated...")
    await asyncio.sleep(5)
    
    print("Done! Agents populated.")

if __name__ == "__main__":
    asyncio.run(populate())
