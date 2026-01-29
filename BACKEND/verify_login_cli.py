import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.modules.iam.security import verify_password, get_password_hash

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/nexus_ai"

async def diagnose_login():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        print("\n--- DIAGNOSTIC START ---")
        
        # 1. Fetch User
        print("1. Fetching user 'admin@nexus.ai'...")
        result = await conn.execute(
            text("SELECT id, email, hashed_password, is_active FROM users WHERE email = 'admin@nexus.ai'")
        )
        user = result.fetchone()
        
        if not user:
            print("❌ ERROR: User 'admin@nexus.ai' NOT FOUND in database!")
            return

        print(f"[OK] User found: ID={user.id}, Active={user.is_active}")
        
        # 2. Verify Password
        test_password = "NexusSecureStart2026!"
        print(f"2. Testing password: '{test_password}'...")
        
        is_valid = verify_password(test_password, user.hashed_password)
        
        if is_valid:
            print("[SUCCESS] Password matches database hash.")
        else:
            print(f"[FAIL] Password verification failed.")
            print(f"   Stored Hash: {user.hashed_password[:10]}...")
            
            # 3. Create New Hash Comparison
            print("3. Generating fresh hash for comparison...")
            fresh_hash = get_password_hash(test_password)
            print(f"   Fresh Hash:  {fresh_hash[:10]}...")
            print("   (Note: Argon2 hashes are randomized, so they won't look identical, but verification should pass)")

        print("--- DIAGNOSTIC END ---\n")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diagnose_login())
