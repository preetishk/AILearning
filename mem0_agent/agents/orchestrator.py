import os
import logging
# Disable mem0 telemetry to avoid SSL and Permission errors
os.environ["MEM0_TELEMETRY"] = "False"

from .worker_agents import ResearchAgent, SummarizerAgent, HumanizeAgent
from mem0 import Memory
from . import config

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        mem_config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "path": config.MEMORY_DB_PATH,
                    "embedding_model_dims": config.EMBED_DIMS,
                }
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": config.EMBED_MODEL
                }
            },
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": config.CHAT_MODEL,
                    "temperature": 0.1,
                    "max_tokens": 2000,
                }
            }
        }
        self.memory = Memory.from_config(mem_config)
        
        self.researcher = ResearchAgent(memory_client=self.memory)
        self.summarizer = SummarizerAgent(memory_client=self.memory)
        self.humanizer = HumanizeAgent(memory_client=self.memory)

    def handle_request(self, user_input):
        print(f"\n[Orchestrator] Received input: {user_input}")
        
        # 1. Research
        print("[Orchestrator] Delegating to Research Agent...")
        try:
            research_result = self.researcher.research(user_input)
            print(f"[Researcher] Output length: {len(research_result)} chars")
        except Exception as e:
            logger.error(f"[Researcher] Failed: {e}")
            return f"Error: Research step failed — {e}"

        # 2. Summarize
        print("[Orchestrator] Delegating to Summarizer Agent...")
        try:
            summary_result = self.summarizer.summarize(research_result)
            print(f"[Summarizer] Output length: {len(summary_result)} chars")
        except Exception as e:
            logger.error(f"[Summarizer] Failed: {e}")
            print("[Orchestrator] Summarizer failed — returning raw research output.")
            summary_result = research_result

        # 3. Humanize
        print("[Orchestrator] Delegating to Humanize Agent...")
        try:
            final_result = self.humanizer.humanize(summary_result)
            print(f"[Humanizer] Output length: {len(final_result)} chars")
        except Exception as e:
            logger.error(f"[Humanizer] Failed: {e}")
            print("[Orchestrator] Humanizer failed — returning summary output.")
            final_result = summary_result

        return final_result
