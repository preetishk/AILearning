import unittest
from models import AgentMetadata, AgentType, CapabilityDefinition
from registry import InMemoryRegistryStore

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = InMemoryRegistryStore()

    def test_register_and_get_agent(self):
        agent = AgentMetadata(
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.TOOL
        )
        agent_id = self.registry.register_agent(agent)
        self.assertEqual(agent_id, agent.id)
        
        fetched_agent = self.registry.get_agent(agent_id)
        self.assertIsNotNone(fetched_agent)
        self.assertEqual(fetched_agent.name, "Test Agent")

    def test_search_agent(self):
        agent1 = AgentMetadata(
            name="Alpha Agent",
            description="Handles alpha tasks",
            tags=["alpha", "first"]
        )
        self.registry.register_agent(agent1)
        
        agent2 = AgentMetadata(
            name="Beta Agent",
            description="Handles beta tasks",
            tags=["beta", "second"]
        )
        self.registry.register_agent(agent2)
        
        results = self.registry.search_agents("alpha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alpha Agent")
        
        results = self.registry.search_agents("tasks")
        self.assertEqual(len(results), 2)

if __name__ == '__main__':
    unittest.main()
