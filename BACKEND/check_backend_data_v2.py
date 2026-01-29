import requests
import json

def check_api():
    print("Checking Backend API...")
    url = "http://localhost:8000/api/v1/routing/network"
    
    # 1. Login to get token
    login_url = "http://localhost:8000/api/v1/iam/login/access-token"
    # Note: Use the password we reset earlier.
    data = {"username": "admin@nexus.ai", "password": "NexusSecureStart2026!"}
    
    print(f"Logging in to {login_url}...")
    try:
        resp = requests.post(login_url, data=data)
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            return
        token_data = resp.json()
        token = token_data["access_token"]
        print("Login successful.")
    except Exception as e:
        print(f"Login exception: {e}")
        return

    # 2. Fetch Network
    print(f"Fetching network from {url}...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Network fetch failed: {resp.status_code} {resp.text}")
            return
        
        data = resp.json()
        routes = data.get("routes", [])
        print(f"Received {len(routes)} routes.")
        
        # Check specific routes
        if routes:
            r = routes[0]
            print(f"Sample Route ID: {r.get('id')}")
            print(f"Sample Route Name: {r.get('name')}")
            coords = r.get('coordinates', [])
            print(f"Sample Route Coords count: {len(coords)}")
            if coords:
                print(f"Sample Route Coords[0]: {coords[0]}")
        else:
            print("No routes found in response.")
            
    except Exception as e:
        print(f"Fetch network exception: {e}")

if __name__ == "__main__":
    check_api()
