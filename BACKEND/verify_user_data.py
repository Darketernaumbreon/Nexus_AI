
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

# Setup Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Config
PASSWORD = "deb172006"
DATABASE_URL = f"postgresql+asyncpg://postgres:{PASSWORD}@localhost:5432/nexus_ai"

# Match app/modules/iam/security.py
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto",
    argon2__rounds=1, 
    argon2__memory_cost=65536,
    argon2__parallelism=4
)

async def verify_user():
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            print(f"Checking database...")
            
            # 1. Check if user exists
            result = await conn.execute(text("SELECT email, hashed_password, is_active, is_superuser FROM users WHERE email = 'admin@nexus.ai'"))
            user = result.fetchone()
            
            if not user:
                print("❌ User 'admin@nexus.ai' NOT FOUND in database!")
                return
            
            print(f"✅ User found: {user[0]}")
            print(f"   Stored Hash: {user[1]}")
            
            # 2. Verify Password
            input_pw = "NexusSecureStart2026!"
            try:
                is_valid = pwd_context.verify(input_pw, user[1])
                if is_valid:
                    print("✅ Password verification SUCCESS!")
                else:
                    print("❌ Password verification FAILED!")
            except Exception as e:
                print(f"❌ Verification Error: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_user())
