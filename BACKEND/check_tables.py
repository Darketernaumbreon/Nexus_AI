
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Confirmed working credentials
PASSWORD = "deb172006"
DATABASE_URL = f"postgresql+asyncpg://postgres:{PASSWORD}@localhost:5432/nexus_ai"

async def list_tables():
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            print(f"Connected to DB: {DATABASE_URL}")
            
            # List all tables in all schemas
            result = await conn.execute(text(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_schema NOT IN ('information_schema', 'pg_catalog')"
            ))
            tables = result.fetchall()
            print(f"Found {len(tables)} tables:")
            for t in tables:
                print(f" - {t[0]}.{t[1]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tables())
