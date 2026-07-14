"""
Quick Start Guide - Simple interactive demo
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from MultiAgentOrchestrator.main import AgentFramework, create_simple_agent


async def main():
    """Quick start demo"""
    print("\n" + "=" * 60)
    print(" AI Agentic Framework - Quick Start Demo")
    print("=" * 60)
    
    # Initialize framework
    print("\n📦 Initializing framework...")
    framework = AgentFramework()
    print("✅ Framework ready!\n")
    
    # Create a simple agent
    print("🤖 Creating your first agent...")
    agent = await create_simple_agent(
        framework=framework,
        name="my_first_agent",
        description="A friendly AI assistant",
        model="llama3.1"
    )
    print(f"✅ Agent '{agent.config.agent_name}' is ready!\n")
    
    # Interactive chat loop
    print("💬 You can now chat with your agent!")
    print("   (Type 'quit' to exit, 'status' for agent info)\n")
    print("-" * 60)
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'status':
                status = framework.get_agent_status(agent.config.agent_id)
                print("\n📊 Agent Status:")
                print(f"   Name: {status['agent_name']}")
                print(f"   Status: {status['status']}")
                print(f"   Interactions: {status.get('total_interactions', 0)}")
                print(f"   Tokens Used: {status.get('total_tokens_used', 0)}")
                continue
            
            # Get agent response
            print("\n🤔 Agent is thinking...")
            response = await agent.execute(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("📈 Session Summary:")
    state = agent.get_state()
    print(f"   Total conversations: {state.interaction_count}")
    print(f"   Total tokens used: {state.total_tokens_used}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n🚀 Starting Quick Start Demo...")
    print("⚠️  Make sure Ollama is running with llama3.1 model!")
    print("   Run: ollama pull llama3.1\n")
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Ollama is installed and running")
        print("2. Pull the llama3.1 model: ollama pull llama3.1")
        print("3. Check that port 11434 is accessible")
