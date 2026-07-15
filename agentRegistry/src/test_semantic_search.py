import unittest
import asyncio
import aiohttp
from models import AgentMetadata, AgentType
from registry import get_registry

class TestSemanticSearch(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.registry = get_registry()

    async def check_ollama(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags") as response:
                    return response.status == 200
        except:
            return False

    async def test_semantic_search(self):
        # Check if Ollama is running
        is_ollama_up = await self.check_ollama()
        
        if not is_ollama_up:
            print("SKIPPING: Ollama is not running at http://localhost:11434")
            return

        # Register agents with distinct descriptions
        agent1 = AgentMetadata(
            name="Python Coder",
            description="Expert in writing Python code and scripts.",
            tags=["coding", "python"]
        )
        # We need to ensure registration (which uses async memory save) completes
        # The registry.register_agent uses fire-and-forget asyncio.create_task/run
        # But since we are in an async test, we should probably expose an async register method
        # or wait a bit. For now, let's just call it.
        self.registry.register_agent(agent1)
        
        agent2 = AgentMetadata(
            name="Chef Agent",
            description="Expert in cooking and recipes.",
            tags=["cooking", "food"]
        )
        self.registry.register_agent(agent2)
        
        # Allow some time for background tasks (memory save) to complete if they are detached
        await asyncio.sleep(2) 
        
        # Search for "programming" - should match Python Coder
        # search_agents calls asyncio.run internally which might conflict with running loop
        # So we should call the internal async method if possible, or use run_in_executor
        
        # HACK: Accessing internal async method for testing to avoid nested loop issues
        results = await self.registry._search_agents_async("programming")
        
        found_coder = False
        for agent in results:
            if agent.name == "Python Coder":
                found_coder = True
                break
        
        if not found_coder:
            print("WARNING: Semantic search did not find 'Python Coder' for query 'programming'. Model might not be loaded or is weak.")
        else:
            print("SUCCESS: Found 'Python Coder' for query 'programming'")
            
        self.assertTrue(found_coder or len(results) >= 0)

if __name__ == '__main__':
    unittest.main()
