import os
# Disable mem0 telemetry to avoid SSL and Permission errors
os.environ["MEM0_TELEMETRY"] = "False"

from mem0 import Memory
from openai import OpenAI
from . import config

class BaseAgent:
    def __init__(self, name, user_id="user_1", memory_client=None):
        self.name = name
        self.user_id = user_id
        
        if memory_client:
            self.memory = memory_client
        else:
            mem_config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "path": f"./db/{name}",
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
        
        # Initialize LLM Client (Ollama-compatible OpenAI endpoint)
        self.client = OpenAI(
            base_url=f"{config.OLLAMA_HOST}/v1",
            api_key="ollama",  # required by the client library, but unused
        )
        self.model = config.CHAT_MODEL

    def add_memory(self, text):
        """Add context to agent's memory."""
        self.memory.add(text, user_id=self.user_id)

    def get_memory(self, query):
        """Retrieve relevant context from memory."""
        memories = self.memory.search(query, user_id=self.user_id)
        # mem0 can return different structures depending on version
        context = ""
        if memories:
            for mem in memories:
                # Handle both dict and string responses
                if isinstance(mem, dict):
                    context += f"- {mem.get('memory', mem.get('text', str(mem)))}\n"
                else:
                    context += f"- {str(mem)}\n"
        return context

    def process(self, input_text, system_prompt=None):
        """Process input with memory context."""
        # 1. Retrieve relevant memory
        context = self.get_memory(input_text)
        
        # 2. Construct Prompt
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        user_content = f"Context from previous interactions:\n{context}\n\nCurrent Input: {input_text}"
        messages.append({"role": "user", "content": user_content})

        # 3. Call LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        result = response.choices[0].message.content

        # 4. Store the interaction in memory
        # We store the user input and the agent's response to maintain conversation history
        self.add_memory(f"User: {input_text}\nAgent {self.name}: {result}")
        
        return result
