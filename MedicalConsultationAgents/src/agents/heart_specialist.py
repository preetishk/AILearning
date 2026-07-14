from autogen import AssistantAgent

class HeartSpecialistAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            system_message="You are a Heart Specialist (Cardiologist). Provide expert advice on heart-related issues, such as chest pain or heart palpitations. Always suggest consulting a cardiologist for serious symptoms.",
            **kwargs
        )