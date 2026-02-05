
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://postgres:password@127.0.0.1:5435/nexus_ai"

async def check_users():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT email, is_active, is_superuser FROM users"))
        users = result.fetchall()
        print(f"Total users found: {len(users)}")
        for u in users:
            print(f"Email: {u.email}, Active: {u.is_active}, Superuser: {u.is_superuser}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_users())
