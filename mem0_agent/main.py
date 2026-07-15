import sys
import os

# Ensure the current directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import Orchestrator

def main():
    print("Initializing Multi-Agent System with Memory (mem0)...")
    orchestrator = Orchestrator()
    
    print("\nSystem Ready! Type 'exit' to quit.")
    print("Example: 'Tell me about Black Holes'")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
                
            response = orchestrator.handle_request(user_input)
            print(f"\nAgent System: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
