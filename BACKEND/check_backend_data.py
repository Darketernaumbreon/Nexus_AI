import asyncio
import aiohttp
import json

async def check_api():
    print("Checking Backend API...")
    url = "http://localhost:8000/api/v1/routing/network"
    # Assuming explicit login not needed for this public-ish endpoint or using default settings
    # But wait, it might be protected. The verify_login script showed how to get a token.
    # Let's try unauthorized first, then authorized if needed.
    
    async with aiohttp.ClientSession() as session:
        # 1. Login to get token
        login_url = "http://localhost:8000/api/v1/iam/login/access-token"
        data = {"username": "admin@nexus.ai", "password": "NexusSecureStart2026!"}
        print(f"Logging in to {login_url}...")
        async with session.post(login_url, data=data) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status} {await resp.text()}")
                return
            token_data = await resp.json()
            token = token_data["access_token"]
            print("Login successful.")

        # 2. Fetch Network
        print(f"Fetching network from {url}...")
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"Network fetch failed: {resp.status} {await resp.text()}")
                return
            
            data = await resp.json()
            routes = data.get("routes", [])
            print(f"Received {len(routes)} routes.")
            if routes:
                r = routes[0]
                print(f"Sample Route ID: {r.get('id')}")
                print(f"Sample Route Name: {r.get('name')}")
                coords = r.get('coordinates', [])
                print(f"Sample Route Coords count: {len(coords)}")
                print(f"Sample Route Coords[0]: {coords[0] if coords else 'None'}")
            else:
                print("No routes found in response.")

if __name__ == "__main__":
    asyncio.run(check_api())
