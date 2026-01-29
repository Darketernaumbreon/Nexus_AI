import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/nexus_ai"

async def add_column():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Adding 'name' column to nav_edges...")
        try:
            await conn.execute(text("ALTER TABLE nav_edges ADD COLUMN IF NOT EXISTS name VARCHAR"))
            print("Column added successfully.")
        except Exception as e:
            print(f"Error: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_column())
