
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Hardcoded URL that matches docker-compose
DATABASE_URL = "postgresql+asyncpg://postgres:deb172006@localhost:5432/nexus_ai"

async def check_db():
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.connect() as conn:
            print("Successfully connected to the database!")
            
            # Check if users table exists
            try:
                result = await conn.execute(text("SELECT email FROM users"))
                users = result.fetchall()
                print(f"Found {len(users)} users:")
                for user in users:
                    print(f" - {user[0]}")
            except Exception as table_e:
                print(f"Could not query users table: {table_e}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
