"""
RAG Agent Example - Agent with knowledge base
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from MultiAgentOrchestrator.main import AgentFramework
from MultiAgentOrchestrator.models import AgentConfig, AgentCapabilities, AgentBehavior


async def main():
    """Run RAG agent example"""
    print("=" * 60)
    print("RAG Agent Example - Agent with Knowledge Base")
    print("=" * 60)
    
    # Initialize framework
    print("\n1. Initializing framework...")
    framework = AgentFramework()
    
    # Add RAG source
    print("\n2. Setting up RAG knowledge base...")
    framework.add_rag_source(
        source_id="company_docs",
        name="Company Documentation",
        collection_name="company_knowledge"
    )
    
    # Add some sample documents
    print("   Adding sample documents...")
    sample_docs = [
        "Our company was founded in 2020 and specializes in AI solutions.",
        "We offer three main products: AutoAgent, SmartChat, and DataMind.",
        "Our customer support is available 24/7 via email and chat.",
        "We have offices in San Francisco, New York, and London.",
        "Our pricing starts at $99/month for the basic plan."
    ]
    
    await framework.add_documents_to_rag(
        source_id="company_docs",
        documents=sample_docs,
        metadatas=[{"type": "company_info"} for _ in sample_docs]
    )
    print(f"   Added {len(sample_docs)} documents to knowledge base")
    
    # Create RAG-enabled agent
    print("\n3. Creating RAG-enabled agent...")
    config = AgentConfig(
        agent_name="company_assistant",
        agent_description="An assistant that knows about our company using RAG",
        capabilities=AgentCapabilities(
            prompts=["customer_support"],
            tools=["echo"],
            rag_sources=["company_docs"],
            max_iterations=5
        ),
        behavior=AgentBehavior(
            model="llama3.1",
            temperature=0.7,
            max_tokens=512
        )
    )
    
    agent = await framework.create_and_deploy_agent(config)
    print(f"   Agent deployed: {agent.config.agent_name}")
    
    # Test RAG-enhanced interactions
    print("\n4. Testing RAG-enhanced interactions...\n")
    
    test_queries = [
        "When was the company founded?",
        "What products do you offer?",
        "How can I contact customer support?",
        "What are your office locations?",
        "How much does the basic plan cost?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        print("   " + "-" * 50)
        
        try:
            response = await agent.execute(query, use_rag=True)
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Show agent statistics
    print("\n5. Agent Statistics:")
    print("   " + "-" * 50)
    state = agent.get_state()
    print(f"   Total interactions: {state.interaction_count}")
    print(f"   Total tokens used: {state.total_tokens_used}")
    
    # Show RAG sources
    print("\n6. Available RAG Sources:")
    print("   " + "-" * 50)
    sources = framework.list_rag_sources()
    for source in sources:
        print(f"   - {source['name']} ({source['source_id']})")
    
    print("\n" + "=" * 60)
    print("RAG Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
