
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Confirmed working credentials
PASSWORD = "deb172006"
DATABASE_URL = f"postgresql+asyncpg://postgres:{PASSWORD}@localhost:5432/nexus_ai"

async def reset_alembic():
    try:
        engine = create_async_engine(DATABASE_URL, echo=False, isolation_level="AUTOCOMMIT")
        async with engine.connect() as conn:
            print(f"Dropping alembic_version table...")
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            print("Dropped.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(reset_alembic())
