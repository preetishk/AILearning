from .base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self, memory_client=None):
        super().__init__(name="Researcher", memory_client=memory_client)

    def research(self, topic):
        prompt = f"Please provide a detailed research summary about: {topic}. Include key facts and recent developments if known."
        return self.process(topic, system_prompt="You are a Research Agent. Your goal is to provide detailed, factual information on the given topic.")

class SummarizerAgent(BaseAgent):
    def __init__(self, memory_client=None):
        super().__init__(name="Summarizer", memory_client=memory_client)

    def summarize(self, text):
        prompt = f"Please summarize the following text into key points:\n\n{text}"
        return self.process(prompt, system_prompt="You are a Summarizer Agent. Your goal is to condense information into clear, concise bullet points.")

class HumanizeAgent(BaseAgent):
    def __init__(self, memory_client=None):
        super().__init__(name="Humanizer", memory_client=memory_client)

    def humanize(self, text):
        prompt = f"Please rewrite the following summary to be more conversational, friendly, and easy to understand for a general audience:\n\n{text}"
        return self.process(prompt, system_prompt="You are a Humanize Agent. Your goal is to make technical or dry text sound friendly and accessible.")
