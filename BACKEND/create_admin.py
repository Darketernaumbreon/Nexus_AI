import asyncio
import sys
import os

# Add parent dir to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.modules.iam.models import User
from app.modules.iam.security import get_password_hash
from sqlalchemy import select

async def create_superuser():
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.email == "admin@nexus.ai"))
        user = result.scalars().first()
        
        if user:
            print("User admin@nexus.ai already exists.")
            return

        print("Creating superuser admin@nexus.ai...")
        # Use a stronger password to avoid browser security warnings
        hashed_pw = get_password_hash("NexusSecureStart2026!")
        new_user = User(
            email="admin@nexus.ai",
            hashed_password=hashed_pw,
            is_active=True,
            is_superuser=True
        )
        session.add(new_user)
        await session.commit()
        print("Superuser created successfully!")

if __name__ == "__main__":
    asyncio.run(create_superuser())
