import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent dir to path so we can import app settings (though checks are manual here)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Hardcode URL for reliability in this script matching .env
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/nexus_ai"

async def enable_postgis():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Enabling PostGIS extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        print("PostGIS enabled successfully!")
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(enable_postgis())
    except Exception as e:
        print(f"Error: {e}")
