
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

# Force using port 5435 if running locally to match our recent fix
# But we should rely on settings if possible.
# Let's trust the settings loaded from ENV or defaults.
DATABASE_URL = settings.DATABASE_URL

async def force_refresh():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Cleaning up old network data...")
        await conn.execute(text("TRUNCATE TABLE nav_edges CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE nav_nodes CASCADE;"))
        print("Old data deleted.")
        
    await engine.dispose()
    
    print("Re-running seed script...")
    from seed_network import seed_network
    await seed_network()
    
    print("Ensuring Admin User Exists...")
    from app.modules.iam.security import get_password_hash
    
    # Re-connect for user operations
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Create Admin User if missing
    async with engine.begin() as conn:
        # Check if admin exists
        result = await conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "admin@nexus.ai"})
        if not result.scalar():
             print("Creating admin user...")
             hashed_pw = get_password_hash("password123") # Reset to simple default
             await conn.execute(text("""
                INSERT INTO users (email, hashed_password, is_active, is_superuser)
                VALUES (:email, :pw, TRUE, TRUE)
            """), {"email": "admin@nexus.ai", "pw": hashed_pw})
             print("Admin user created (admin@nexus.ai / password123)")
        else:
             print("Admin user already exists. Resetting password to default...")
             hashed_pw = get_password_hash("password123")
             await conn.execute(text("""
                UPDATE users SET hashed_password = :pw WHERE email = :email
             """), {"email": "admin@nexus.ai", "pw": hashed_pw})
    
    await engine.dispose()
             
    print("Refresh Complete!")

if __name__ == "__main__":
    # Ensure current dir is in path for imports
    sys.path.append(os.getcwd())
    asyncio.run(force_refresh())
