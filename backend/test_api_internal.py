import requests
import sys

try:
    print("Testing API health endpoint...")
    response = requests.get("http://127.0.0.1:8000/api/v1/predict/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    
    if response.status_code == 200:
        print("SUCCESS: Endpoint is reachable.")
        sys.exit(0)
    else:
        print("FAILURE: Endpoint returned non-200 status.")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Could not connect. {e}")
    sys.exit(1)
