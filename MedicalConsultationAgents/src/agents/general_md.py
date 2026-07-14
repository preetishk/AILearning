from autogen import AssistantAgent

class GeneralMDAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            system_message="You are a General Medical Doctor. Provide accurate and simple medical advice for general health issues. Always suggest consulting a real doctor for serious conditions.",
            **kwargs
        )