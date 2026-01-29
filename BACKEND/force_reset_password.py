import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.modules.iam.security import get_password_hash

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/nexus_ai"

async def force_reset():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Force resetting admin password...")
        new_hash = get_password_hash("NexusSecureStart2026!")
        # Postgres supports specific parameter syntax, but standard params are safer
        await conn.execute(
            text("UPDATE users SET hashed_password = :pw WHERE email = :email"),
            {"pw": new_hash, "email": "admin@nexus.ai"}
        )
        print("Password updated successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(force_reset())
