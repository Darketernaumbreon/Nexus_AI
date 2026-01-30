
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

PASSWORD = "deb172006"
DATABASE_URL = f"postgresql+asyncpg://postgres:{PASSWORD}@localhost:5432/nexus_ai"

async def manual_create():
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.begin() as conn:
            print("Creating users table manually...")
            await conn.execute(text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR NOT NULL UNIQUE,
                    hashed_password VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_superuser BOOLEAN DEFAULT FALSE
                )
            """))
            print("Table users created successfully!")
            
            # Seed user
            print("Seeding admin user...")
            # We need to hash the password properly, but for this test I'll just insert a dummy or use the hasher if I can import it.
            # I'll just insert a raw string and we'll fix it with create_admin later if this works.
            # actually better to use the real hasher if possible.
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(manual_create())
