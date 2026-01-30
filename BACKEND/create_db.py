
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Confirmed working credentials
PASSWORD = "deb172006"

async def create_db():
    print(f"Connecting to 'postgres' db to check/create 'nexus_ai'...")
    url = f"postgresql+asyncpg://postgres:{PASSWORD}@localhost:5432/postgres" 
    try:
        engine = create_async_engine(url, echo=False, isolation_level="AUTOCOMMIT")
        async with engine.connect() as conn:
            # Check if nexus_ai exists
            result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'nexus_ai'"))
            if result.scalar():
                print("Database 'nexus_ai' already exists.")
            else:
                print("Database 'nexus_ai' does not exist. Creating it...")
                await conn.execute(text("CREATE DATABASE nexus_ai"))
                print("Database 'nexus_ai' created successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_db())
