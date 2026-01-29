import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/nexus_ai"

async def reset_db():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        print("Dropping all tables...")
        # Cascade drop to remove dependent keys
        await conn.execute(text("DROP TABLE IF EXISTS edge_dynamic_weights CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS nav_edges CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS nav_nodes CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
        print("All tables dropped.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
