import json
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from agents.orchestrator import OrchestratorAgent
from agents.general_md import GeneralMDAgent
from agents.heart_specialist import HeartSpecialistAgent
from agents.pathologist import PathologistAgent

# Load LLM configuration
config_list = config_list_from_json("config/ollama_config.json")

# Initialize agents
orchestrator = OrchestratorAgent(
    name="Orchestrator",
    llm_config={"config_list": config_list},
    system_message="You are an orchestrator that routes medical queries to the one or more appropriate agent: General MD, Heart Specialist, or Pathologist/Radiologist."
)

general_md = GeneralMDAgent(
    name="GeneralMD",
    llm_config={"config_list": config_list},
)

heart_specialist = HeartSpecialistAgent(
    name="HeartSpecialist",
    llm_config={"config_list": config_list},
)

pathologist = PathologistAgent(
    name="Pathologist",
    llm_config={"config_list": config_list},
)

# Register specialized agents with the orchestrator
orchestrator.register_agents(general_md, heart_specialist, pathologist)

# Initialize user proxy
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=0,
    llm_config=False,
    code_execution_config={"use_docker": False}
)

# Function to start the interaction
def start_interaction(query):
    user_proxy.initiate_chat(orchestrator, message=query)

if __name__ == "__main__":
    print("Welcome to the Medical Agent System! Enter your medical question (or 'quit' to exit).")
    while True:
        query = input("Your question: ")
        if query.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break
        start_interaction(query)