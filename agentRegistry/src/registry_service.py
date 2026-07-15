import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from models import AgentMetadata
from registry import get_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("registry_service")

# Initialize FastAPI app
app = FastAPI(
    title="Agent Registry API",
    description="API service for querying AI Agent metadata and capabilities",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Service health check"""
    return {"status": "active", "service": "registry-api"}

@app.get("/agents", response_model=List[AgentMetadata])
async def list_agents():
    """
    Get a list of all registered agents.
    """
    try:
        registry = get_registry()
        agents = registry.get_all_agents()
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/agents/{agent_id}", response_model=AgentMetadata)
async def get_agent_details(agent_id: str):
    """
    Get detailed metadata for a specific agent by ID.
    """
    registry = get_registry()
    agent = registry.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID '{agent_id}' not found")
    
    return agent

@app.get("/search", response_model=List[AgentMetadata])
async def search_agents(q: str = Query(..., description="Search query string (e.g. 'coding agent', 'web search')")):
    """
    Semantic search for agents based on name, description, capability, or tags.
    """
    try:
        registry = get_registry()
        results = registry.search_agents(q)
        return results
    except Exception as e:
        logger.error(f"Error searching agents: {e}")
        raise HTTPException(status_code=500, detail="Search operation failed")

if __name__ == "__main__":
    # Run on port 9001 to avoid conflict with agent server (8000) and streamlit (8501)
    uvicorn.run(app, host="127.0.0.1", port=9001)
