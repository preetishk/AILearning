import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import Orchestrator

def test_run():
    print("Initializing Orchestrator...")
    orch = Orchestrator()
    
    topic = "Artificial Intelligence in Healthcare"
    print(f"\n--- Test 1: Researching '{topic}' ---")
    response1 = orch.handle_request(f"Tell me about {topic}")
    print(f"\nFinal Output 1:\n{response1}")
    
    print(f"\n--- Test 2: Memory Recall ---")
    # Ask a follow-up that requires memory
    follow_up = "What are the risks associated with it?"
    print(f"User Input: {follow_up}")
    response2 = orch.handle_request(follow_up)
    print(f"\nFinal Output 2:\n{response2}")

if __name__ == "__main__":
    test_run()
