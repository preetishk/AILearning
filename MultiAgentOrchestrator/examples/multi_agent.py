"""
Multi-Agent Example - Multiple agents working together
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from MultiAgentOrchestrator.main import AgentFramework
from MultiAgentOrchestrator.models import AgentConfig, AgentCapabilities, AgentBehavior


async def main():
    """Run multi-agent example"""
    print("=" * 60)
    print("Multi-Agent Example - Collaborative Agents")
    print("=" * 60)
    
    # Initialize framework
    print("\n1. Initializing framework...")
    framework = AgentFramework()
    
    # Create multiple specialized agents
    print("\n2. Creating specialized agents...\n")
    
    # Agent 1: Research Agent
    research_config = AgentConfig(
        agent_name="research_agent",
        agent_description="Specializes in research and information gathering",
        capabilities=AgentCapabilities(
            prompts=["research_assistant"],
            tools=["echo"],
            max_iterations=5
        ),
        behavior=AgentBehavior(
            model="llama3.1",
            temperature=0.3,  # Lower temperature for factual responses
            max_tokens=1024
        )
    )
    research_agent = await framework.create_and_deploy_agent(research_config)
    print(f"   ✓ Deployed: {research_agent.config.agent_name}")
    
    # Agent 2: Customer Support Agent
    support_config = AgentConfig(
        agent_name="support_agent",
        agent_description="Handles customer inquiries with empathy",
        capabilities=AgentCapabilities(
            prompts=["customer_support"],
            tools=["echo", "calculator"],
            max_iterations=5
        ),
        behavior=AgentBehavior(
            model="llama3.1",
            temperature=0.7,  # Balanced for friendly responses
            max_tokens=512
        )
    )
    support_agent = await framework.create_and_deploy_agent(support_config)
    print(f"   ✓ Deployed: {support_agent.config.agent_name}")
    
    # Agent 3: Technical Agent
    technical_config = AgentConfig(
        agent_name="technical_agent",
        agent_description="Provides technical assistance and calculations",
        capabilities=AgentCapabilities(
            prompts=["general_assistant"],
            tools=["calculator", "echo"],
            max_iterations=5
        ),
        behavior=AgentBehavior(
            model="llama3.1",
            temperature=0.2,  # Very low for precise technical responses
            max_tokens=512
        )
    )
    technical_agent = await framework.create_and_deploy_agent(technical_config)
    print(f"   ✓ Deployed: {technical_agent.config.agent_name}")
    
    # Test each agent with specialized tasks
    print("\n3. Testing specialized agents...\n")
    
    tasks = [
        {
            "agent": research_agent,
            "name": "Research Agent",
            "query": "Explain the concept of machine learning in simple terms"
        },
        {
            "agent": support_agent,
            "name": "Support Agent",
            "query": "I'm having trouble understanding how to use your service"
        },
        {
            "agent": technical_agent,
            "name": "Technical Agent",
            "query": "Calculate the sum of 123 and 456"
        }
    ]
    
    for task in tasks:
        print(f"   {task['name']}:")
        print(f"   Query: {task['query']}")
        print("   " + "-" * 50)
        
        try:
            response = await task['agent'].execute(task['query'])
            print(f"   Response: {response[:200]}...")  # Truncate for display
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
    
    # Show all agents status
    print("\n4. All Agents Status:")
    print("   " + "-" * 50)
    
    all_agents = framework.list_agents()
    for agent_config in all_agents:
        status = framework.get_agent_status(agent_config.agent_id)
        print(f"\n   Agent: {status['agent_name']}")
        print(f"   Status: {status['status']}")
        print(f"   Interactions: {status.get('total_interactions', 0)}")
        print(f"   Tokens Used: {status.get('total_tokens_used', 0)}")
    
    # Demonstrate agent collaboration (simplified)
    print("\n5. Agent Collaboration Example:")
    print("   " + "-" * 50)
    print("   Simulating multi-step task requiring multiple agents...\n")
    
    # Step 1: Research gathers information
    print("   Step 1: Research Agent gathers information")
    research_response = await research_agent.execute(
        "What are the key benefits of AI?"
    )
    print(f"   Research: {research_response[:150]}...")
    
    # Step 2: Technical agent processes data
    print("\n   Step 2: Technical Agent validates findings")
    tech_response = await technical_agent.execute(
        "Verify that AI can process data faster than humans"
    )
    print(f"   Technical: {tech_response[:150]}...")
    
    # Step 3: Support agent creates user-friendly summary
    print("\n   Step 3: Support Agent creates friendly explanation")
    support_response = await support_agent.execute(
        f"Explain to a customer: {research_response[:100]}"
    )
    print(f"   Support: {support_response[:150]}...")
    
    print("\n" + "=" * 60)
    print("Multi-Agent Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
