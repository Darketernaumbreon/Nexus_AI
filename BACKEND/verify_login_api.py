
import asyncio
import httpx

# Correct Credentials
URL = "http://localhost:8000/api/v1/iam/login/access-token"
USERNAME = "admin@nexus.ai" # Clean email
PASSWORD = "NexusSecureStart2026!"

async def verify_login():
    print(f"Attempting login to {URL}...")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"username": USERNAME, "password": PASSWORD}
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(URL, data=data, headers=headers)
            
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ Login Successful!")
                token = resp.json()
                print(f"Token received: {token['access_token'][:20]}...")
            else:
                print(f"❌ Login Failed: {resp.text}")
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_login())
