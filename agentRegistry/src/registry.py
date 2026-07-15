from typing import List, Optional, Dict
import logging
import os
from datetime import datetime
from models import AgentMetadata, AgentStatus

logger = logging.getLogger(__name__)

class RegistryStore:
    """Abstract base class for registry storage"""
    def register_agent(self, agent: AgentMetadata) -> str:
        raise NotImplementedError
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        raise NotImplementedError
    
    def get_all_agents(self) -> List[AgentMetadata]:
        raise NotImplementedError
    
    def search_agents(self, query: str) -> List[AgentMetadata]:
        raise NotImplementedError

import sqlite3
import json
import asyncio
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore
from semantic_kernel.connectors.ai.ollama.services.ollama_text_embedding import OllamaTextEmbedding

class SemanticMemoryRegistryStore(RegistryStore):
    """Registry store using Semantic Kernel's SemanticTextMemory and SQLite persistence"""
    
    def __init__(self, persistence_file: str = "agents.db"):
        self.agents: Dict[str, AgentMetadata] = {}
        self.collection_name = "agent_registry"
        
        # Use absolute path relative to this file's directory
        if not os.path.isabs(persistence_file):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.persistence_file = os.path.join(base_dir, persistence_file)
        else:
            self.persistence_file = persistence_file

        self.json_file = os.path.join(os.path.dirname(self.persistence_file), "agents.json")
        
        # Initialize Database
        self._init_db()
        self._migrate_from_json()

        # Initialize Semantic Kernel Memory
        # Use nomic-embed-text which is a proper embedding model
        self.embedding_generator = OllamaTextEmbedding(
            service_id="ollama_embedding",
            ai_model_id="nomic-embed-text",
            host="http://localhost:11434"
        )
        self.memory_store = VolatileMemoryStore()
        self.memory = SemanticTextMemory(storage=self.memory_store, embeddings_generator=self.embedding_generator)
        
        # Load agents from DB to memory
        self._load_agents()
        
    def _get_connection(self):
        return sqlite3.connect(self.persistence_file)

    def _init_db(self):
        """Initialize the SQLite database with required tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agents (
                        id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _migrate_from_json(self):
        """Migrate data from agents.json if database is empty"""
        try:
            if not os.path.exists(self.json_file):
                return

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM agents")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    logger.info("Database empty. Migrating from agents.json...")
                    with open(self.json_file, "r") as f:
                        data = json.load(f)
                        for agent_data in data:
                            try:
                                agent = AgentMetadata(**agent_data)
                                cursor.execute(
                                    "INSERT INTO agents (id, data, updated_at) VALUES (?, ?, ?)",
                                    (agent.id, agent.model_dump_json(), datetime.utcnow())
                                )
                            except Exception as e:
                                logger.error(f"Skipping invalid agent during migration: {e}")
                    conn.commit()
                    logger.info("Migration completed.")
        except Exception as e:
            logger.error(f"Migration failed: {e}")

    def _load_agents(self):
        """Load agents from SQLite database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, data FROM agents")
                rows = cursor.fetchall()
                
                self.agents = {}
                for row in rows:
                    try:
                        agent_data = json.loads(row[1])
                        agent = AgentMetadata(**agent_data)
                        self.agents[agent.id] = agent
                    except Exception as e:
                        logger.error(f"Error loading agent {row[0]}: {e}")
            logger.info(f"Loaded {len(self.agents)} agents from database")
        except Exception as e:
            logger.error(f"Failed to load agents from database: {e}")

    def _upsert_agent(self, agent: AgentMetadata):
        """Upsert agent to SQLite database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO agents (id, data, updated_at) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        data=excluded.data,
                        updated_at=excluded.updated_at
                    """,
                    (agent.id, agent.model_dump_json(), datetime.utcnow())
                )
                conn.commit()
            logger.info(f"Saved agent {agent.id} to database")
        except Exception as e:
            logger.error(f"Failed to save agent to database: {e}")

    async def _register_memory(self, agent: AgentMetadata):
        try:
            # Create a rich description for embedding
            text_to_embed = f"{agent.name}: {agent.description} Tags: {', '.join(agent.tags)} Capabilities: {', '.join([c.name for c in agent.capabilities])}"
            
            await self.memory.save_information(
                collection=self.collection_name,
                id=agent.id,
                text=text_to_embed,
                description=agent.name
            )
        except Exception as e:
            logger.error(f"Failed to register memory for agent {agent.id}: {e}")

    def register_agent(self, agent: AgentMetadata) -> str:
        if agent.id in self.agents:
            logger.info(f"Overwriting existing agent {agent.id}")
        
        self.agents[agent.id] = agent
        self._upsert_agent(agent)
        
        # Safe async execution
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            
            if loop and loop.is_running():
                loop.create_task(self._register_memory(agent))
            else:
                asyncio.run(self._register_memory(agent))
        except Exception as e:
            logger.error(f"Error scheduling memory registration: {e}")
             
        return agent.id
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentMetadata]:
        # Refresh from DB to ensure we have latest data? 
        # For now, rely on in-memory cache being kept in sync via register_agent.
        # If external processes modified DB, we would need to reload. 
        # But assuming single writer or we accept eventual consistency on restart.
        return list(self.agents.values())
    
    def search_agents(self, query: str) -> List[AgentMetadata]:
        """Semantic search using Ollama embeddings"""
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self._search_agents_async(query), loop)
                return future.result()
            else:
                return asyncio.run(self._search_agents_async(query))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def _search_agents_async(self, query: str) -> List[AgentMetadata]:
        try:
            results = await self.memory.search(
                collection=self.collection_name,
                query=query,
                limit=5,
                min_relevance_score=0.5
            )
            
            agent_results = []
            for result in results:
                agent = self.agents.get(result.id)
                if agent:
                    agent_results.append(agent)
            
            return agent_results
        except Exception as e:
            logger.error(f"Async search failed: {e}")
            return []

# Singleton instance for the app
_registry_instance = None

def get_registry(force_reload: bool = False) -> RegistryStore:
    global _registry_instance
    if _registry_instance is None or force_reload:
        _registry_instance = SemanticMemoryRegistryStore()
        # If DB was empty and migration didn't happen (no json), add dummy data
        if not _registry_instance.get_all_agents():
             _add_dummy_data(_registry_instance)
    # No need to explicitly reload from disk on `else` if we trust our in-memory cache,
    # but the original code did `_load_agents` here.
    # To keep behavior similar:
    elif force_reload: 
         _registry_instance._load_agents()
         
    return _registry_instance

def _add_dummy_data(registry: RegistryStore):
    from models import AgentType, CapabilityDefinition
    
    agent1 = AgentMetadata(
        name="Summarizer Agent",
        description="Summarizes long text documents.",
        agent_type=AgentType.LLM,
        tags=["nlp", "summary"],
        capabilities=[
            CapabilityDefinition(name="Summarize", description="Summarize text")
        ]
    )
    registry.register_agent(agent1)
    
    agent2 = AgentMetadata(
        name="Search Agent",
        description="Searches the web for information.",
        agent_type=AgentType.TOOL,
        tags=["search", "web"],
        capabilities=[
            CapabilityDefinition(name="WebSearch", description="Search Google")
        ]
    )
    registry.register_agent(agent2)
