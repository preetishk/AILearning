import asyncio
import httpx
import logging
from datetime import datetime
from models import AgentStatus
from registry import get_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.registry = get_registry()
        self.agent_server_url = "http://localhost:8000"
        
    async def check_health(self):
        """Check health of agent server"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.agent_server_url}/health")
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False, None
    
    async def update_agent_status(self, agent_id: str, is_healthy: bool):
        """Update agent status in registry"""
        agent = self.registry.get_agent(agent_id)
        if agent:
            new_status = AgentStatus.ACTIVE if is_healthy else AgentStatus.INACTIVE
            if agent.status != new_status:
                agent.status = new_status
                agent.updated_at = datetime.utcnow()
                self.registry.register_agent(agent)  # Re-register to save
                logger.info(f"Updated {agent.name} status to {new_status.value}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting health monitor (checking every {self.check_interval}s)")
        
        # Agent IDs to monitor (these are registered by agents.py on startup)
        monitored_agents = [
            "llama-coder-live",
            "tech-writer-live",
            "task-planner-live"
        ]
        
        while True:
            try:
                is_healthy, health_data = await self.check_health()
                
                if is_healthy:
                    logger.info(f"Health check passed: {health_data}")
                    for agent_id in monitored_agents:
                        await self.update_agent_status(agent_id, True)
                else:
                    logger.warning("Health check failed - marking agents as inactive")
                    for agent_id in monitored_agents:
                        await self.update_agent_status(agent_id, False)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(self.check_interval)

async def main():
    monitor = HealthMonitor(check_interval=60)
    await monitor.monitor_loop()

if __name__ == "__main__":
    asyncio.run(main())
