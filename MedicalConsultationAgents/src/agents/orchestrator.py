from autogen import AssistantAgent

class OrchestratorAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specialized_agents = {}

    def register_agents(self, general_md, heart_specialist, pathologist):
        self.specialized_agents = {
            "GeneralMD": general_md,
            "HeartSpecialist": heart_specialist,
            "Pathologist": pathologist
        }

    def route_query(self, query):
        query = query.lower()
        
        # Special handling for lung issues - check this FIRST
        if any(term in query for term in ["lung", "breathing", "pulmonary", "breath", "respiratory"]):
            return self.specialized_agents["HeartSpecialist"], "Routing to: Heart Specialist (for lung issues)"
        
        routing_message = "Routing to: "
        
        # Dynamically build agent descriptions based on the actual agents registered
        agent_descriptions = []
        agent_mapping = {}
        
        # Get list of registered specialists and their display names
        specialists = {
            "GeneralMD": "General MD - For general health questions, basic symptoms, common illnesses, preventive care",
            "HeartSpecialist": "Heart Specialist - For questions about the heart, circulatory system, blood pressure, chest pain, cardiovascular health, pulmonary issues, lungs",
            "Pathologist": "Pathologist/Radiologist - For questions about diagnostic tests, lab results, imaging, scans, biopsies"
        }
        
        # Build descriptions only for agents that actually exist in specialized_agents
        for i, (agent_key, display_info) in enumerate(specialists.items(), 1):
            if agent_key in self.specialized_agents:
                agent_descriptions.append(f"{i}. {display_info}")
                # Extract just the display name portion (before the dash)
                display_name = display_info.split(" - ")[0]
                agent_mapping[display_name] = agent_key
        
        # Generate routing decision using the orchestrator's own reasoning capabilities
        routing_question = f"""
        As a medical query router, I need to determine which medical specialist would be best equipped to answer this question:
        
        "{query}"
        
        Based on the following options:
        {chr(10).join(agent_descriptions)}
        
        I should choose ONE of these specialists: {", ".join([f'{name}' for name in agent_mapping.keys()])}
        
        Format your response as:
        SPECIALIST: [specialist name]
        
        Choose only from these exact specialist names: {", ".join([f'{name}' for name in agent_mapping.keys()])}
        """
        
        # Extract the display names from agent_mapping
        valid_display_names = list(agent_mapping.keys())
        
        # Use simple keyword matching for immediate results
        if "heart" in query or "chest" in query or "cardiac" in query:
            specialist_text = "Heart Specialist"
        elif "x-ray" in query or "scan" in query or "test" in query:
            specialist_text = "Pathologist/Radiologist"
        else:
            specialist_text = "General MD"
        
        agent_key = agent_mapping.get(specialist_text, "GeneralMD")
        selected_agent = self.specialized_agents[agent_key]
        routing_message += specialist_text
        return selected_agent, routing_message

def generate_reply(self, messages, sender, config=None):
    # Check if this is a routing self-evaluation
    if sender is None and len(messages) == 1 and "medical query router" in messages[0]["content"]:
        # For routing questions, use the standard reply generation
        try:
            return super().generate_reply(messages=messages, sender=sender)
        except Exception as e:
            # If there's an error, provide a fallback response
            print(f"Error in LLM routing: {e}")
            return "SPECIALIST: General MD"
    
    # Regular user query handling
    query = messages[-1]["content"]
    
    # Special handling for lung-related queries
    if "lung" in query.lower() or "breathing" in query.lower() or "pulmonary" in query.lower():
        # Force route to Heart Specialist for lung issues
        target_agent = self.specialized_agents["HeartSpecialist"]
        routing_message = "Routing to: Heart Specialist (lung specialist)"
    else:
        # Normal routing
        target_agent, routing_message = self.route_query(query)
    
    print(routing_message)
    
    try:
        # Get the specialist agent's response
        specialist_response = target_agent.generate_reply(
            messages=[{"role": "user", "content": query}],
            sender=self
        )
        
        # Return a combined response
        return f"I've routed your question to our {target_agent.name}.\n\n{specialist_response}"
    except Exception as e:
        print(f"Error getting specialist response: {e}")
        return f"I tried to route your question to {target_agent.name}, but encountered an error. Please try a different question."