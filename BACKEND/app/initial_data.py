
import asyncio
import logging
from sqlalchemy import text
from app.core.config import settings
from app.modules.iam.security import get_password_hash
from sqlalchemy.ext.asyncio import create_async_engine
from seed_network import seed_network

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_admin(engine):
    async with engine.begin() as conn:
        # Check if admin exists
        result = await conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "admin@nexus.ai"})
        if result.scalar():
            logger.info("Admin user already exists.")
            return

        logger.info("Creating admin user...")
        hashed_pw = get_password_hash("NexusSecureStart2026!")
        await conn.execute(text("""
            INSERT INTO users (email, hashed_password, is_active, is_superuser)
            VALUES (:email, :pw, TRUE, TRUE)
        """), {"email": "admin@nexus.ai", "pw": hashed_pw})
        logger.info("Admin user created.")

async def init_db():
    logger.info("Creating initial data")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    try:
        # 1. Create Admin User
        await create_admin(engine)
        
        # 2. Seed Network Data
        # seed_network() function from seed_network.py self-manages its engine/session
        # but we can call it here.
        await seed_network()
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        # Don't raise, just log. We don't want to crash the container loop if seed fails due to constraints.
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
