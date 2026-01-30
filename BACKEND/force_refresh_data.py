
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

# Force using port 5435 if running locally to match our recent fix
# But we should rely on settings if possible.
# Let's trust the settings loaded from ENV or defaults.
DATABASE_URL = settings.DATABASE_URL

async def force_refresh():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Cleaning up old network data...")
        await conn.execute(text("TRUNCATE TABLE nav_edges CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE nav_nodes CASCADE;"))
        print("Old data deleted.")
        
    await engine.dispose()
    
    print("Re-running seed script...")
    from seed_network import seed_network
    await seed_network()
    print("Refresh Complete!")

if __name__ == "__main__":
    # Ensure current dir is in path for imports
    sys.path.append(os.getcwd())
    asyncio.run(force_refresh())
