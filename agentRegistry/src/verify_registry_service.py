import subprocess
import time
import requests
import sys
import os
import signal

def run_verification():
    print("Starting Registry API Service...")
    # Start the service in the background
    process = subprocess.Popen(
        [sys.executable, "registry_service.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    try:
        # Wait for service to start
        print("Waiting for service to initialize...")
        time.sleep(5)
        
        base_url = "http://localhost:9001"
        
        # 1. Test Health
        try:
            resp = requests.get(f"{base_url}/health")
            if resp.status_code == 200:
                print("PASS: Health check")
            else:
                print(f"FAIL: Health check (Status: {resp.status_code})")
        except Exception as e:
            print(f"FAIL: Could not connect to service: {e}")
            return

        # 2. Test Get All Agents
        resp = requests.get(f"{base_url}/agents")
        if resp.status_code == 200:
            agents = resp.json()
            print(f"PASS: List agents (Found {len(agents)})")
        else:
            print(f"FAIL: List agents (Status: {resp.status_code})")

        # 3. Test Search (assuming some agents exist from previous steps)
        # We'll search for 'python' which should match the coder agent
        resp = requests.get(f"{base_url}/search", params={"q": "python code"})
        if resp.status_code == 200:
            results = resp.json()
            if len(results) > 0:
                print(f"PASS: Search agents (Found {len(results)} matches for 'python code')")
                first_match = results[0]
                print(f"      Match: {first_match['name']}")
                
                # 4. Test Get Specific Agent
                agent_id = first_match['id']
                resp_detail = requests.get(f"{base_url}/agents/{agent_id}")
                if resp_detail.status_code == 200:
                     print(f"PASS: Get agent details for {agent_id}")
                else:
                     print(f"FAIL: Get agent details (Status: {resp_detail.status_code})")
            else:
                print("WARN: Search returned 0 results (might be expected if DB empty)")
        else:
            print(f"FAIL: Search agents (Status: {resp.status_code})")

    finally:
        print("Stopping service...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    run_verification()
