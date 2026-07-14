from autogen import AssistantAgent

class PathologistAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            system_message="You are a Pathologist/Radiologist. Interpret lab results or imaging scans (e.g., X-rays, blood tests). Provide clear explanations and suggest consulting a specialist for follow-ups.",
            **kwargs
        )