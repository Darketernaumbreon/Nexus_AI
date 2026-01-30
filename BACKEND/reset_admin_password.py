
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.modules.iam.security import get_password_hash, verify_password

# Ensure we use the correct DB URL
DATABASE_URL = settings.DATABASE_URL
print(f"Target DB: {DATABASE_URL}")

async def reset_admin():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    target_email = "admin@nexus.ai"
    new_password = "password123"
    
    try:
        async with engine.begin() as conn:
            # 1. Check if user exists
            result = await conn.execute(
                text("SELECT id, hashed_password FROM users WHERE email = :email"), 
                {"email": target_email}
            )
            row = result.first()
            
            if not row:
                print(f"User {target_email} NOT FOUND. Creating...")
                hashed_pw = get_password_hash(new_password)
                await conn.execute(text("""
                    INSERT INTO users (email, hashed_password, is_active, is_superuser, full_name)
                    VALUES (:email, :pw, TRUE, TRUE, 'System Admin')
                """), {"email": target_email, "pw": hashed_pw})
                print("User created.")
            else:
                print(f"User {target_email} found. Resetting password...")
                hashed_pw = get_password_hash(new_password)
                await conn.execute(text("""
                    UPDATE users SET hashed_password = :pw, is_active = TRUE WHERE email = :email
                """), {"email": target_email, "pw": hashed_pw})
                print("Password updated.")
                
            # Verification Step
            print("Verifying login capability...")
            result = await conn.execute(
                text("SELECT hashed_password FROM users WHERE email = :email"), 
                {"email": target_email}
            )
            stored_hash = result.scalar()
            
            if verify_password(new_password, stored_hash):
                print("✅ STRICT VERIFICATION SUCCESS: Password hash matches.")
            else:
                print("❌ CRITICAL: Hash verification failed immediately after write!")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    # Loop policy for Windows (prevent RuntimeErrors)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_admin())
