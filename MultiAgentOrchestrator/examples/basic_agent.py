"""
Basic Agent Example - Simple question-answering agent
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from MultiAgentOrchestrator.main import AgentFramework
from MultiAgentOrchestrator.models import AgentConfig, AgentCapabilities, AgentBehavior


async def main():
    """Run basic agent example"""
    print("=" * 60)
    print("Basic Agent Example - Simple Q&A Agent")
    print("=" * 60)
    
    # Initialize framework
    print("\n1. Initializing framework...")
    framework = AgentFramework()
    
    # Show available prompt templates
    print("\n2. Available Prompt Templates:")
    print("   " + "-" * 50)
    templates = framework.list_prompt_templates()
    for template in templates:
        print(f"   - {template.name} (ID: {template.template_id}, v{template.version})")
        print(f"     Category: {template.category}")
        print(f"     Variables: {', '.join(template.variables)}")
        print()
    
    # Create agent configuration
    print("\n3. Creating agent configuration...")
    print("   Using template: 'general_assistant'")
    config = AgentConfig(
        agent_name="qa_assistant",
        agent_description="A helpful question-answering assistant",
        capabilities=AgentCapabilities(
            prompts=["general_assistant"],  # This references the template by ID
            tools=["calculator", "echo"],
            max_iterations=5
        ),
        behavior=AgentBehavior(
            model="llama3.1",
            temperature=0.7,
            max_tokens=512
        )
    )
    
    # Show template details
    print("\n   Template Details:")
    template = framework.prompt_manager.get_template("general_assistant")
    print(f"   Template ID: {template.template_id}")
    print(f"   Version: {template.version}")
    print(f"   Usage Count: {template.usage_count}")
    print(f"   Performance Score: {template.performance_score:.2f}")
    
    # Create and deploy agent
    print("\n4. Deploying agent...")
    agent = await framework.create_and_deploy_agent(config)
    print(f"   Agent deployed: {agent.config.agent_name}")
    
    # Test interactions
    print("\n5. Testing agent interactions...")
    print("   (Watch how the template is used behind the scenes)\n")
    
    test_queries = [
        "What is the capital of France?",
        "Can you explain what you do?",
        "What is 25 + 37?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        print("   " + "-" * 50)
        
        try:
            response = await agent.execute(query)
            print(f"   Response: {response}")
            
            # Show template usage stats
            template_now = framework.prompt_manager.get_template("general_assistant")
            print(f"   [Template now used {template_now.usage_count} times]")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Show agent status
    print("\n6. Agent Status:")
    print("   " + "-" * 50)
    status = framework.get_agent_status(agent.config.agent_id)
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Show final template statistics
    print("\n7. Template Statistics:")
    print("   " + "-" * 50)
    final_template = framework.prompt_manager.get_template("general_assistant")
    print(f"   Template: {final_template.name}")
    print(f"   Version: {final_template.version}")
    print(f"   Total Usage: {final_template.usage_count} times")
    print(f"   Performance Score: {final_template.performance_score:.2f}")
    print(f"   Last Updated: {final_template.updated_at}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("\n💡 TIP: Run 'prompt_template_demo.py' to see the full")
    print("   template management system with versioning!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
