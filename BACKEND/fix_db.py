
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

# Correct Docker Configuration
USER = "postgres"
PASSWORD = "password"
HOST = "localhost"
PORT = "5435"
DB_NAME = "nexus_ai"

# Password Hashing
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto",
    argon2__rounds=1, 
    argon2__memory_cost=65536,
    argon2__parallelism=4
)

async def fix_db():
    # 1. Create Database if not exists
    print("--- Checking Database ---")
    sys_url = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/postgres"
    sys_engine = create_async_engine(sys_url, isolation_level="AUTOCOMMIT")
    async with sys_engine.connect() as conn:
        result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
        if not result.scalar():
            print(f"Creating database {DB_NAME}...")
            await conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
        else:
            print(f"Database {DB_NAME} already exists.")
    await sys_engine.dispose()

    # 2. Setup Tables and Seed
    app_url = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    print(f"Connecting to {app_url}...")
    engine = create_async_engine(app_url)
    
    async with engine.begin() as conn:
        print("--- Enabling PostGIS ---")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

        print("--- Creating Tables ---")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR NOT NULL UNIQUE,
                hashed_password VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_superuser BOOLEAN DEFAULT FALSE
            );
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nav_nodes (
                id BIGSERIAL PRIMARY KEY,
                geom GEOMETRY(POINT, 4326) NOT NULL
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nav_edges (
                id BIGSERIAL PRIMARY KEY,
                source_node BIGINT NOT NULL REFERENCES nav_nodes(id),
                target_node BIGINT NOT NULL REFERENCES nav_nodes(id),
                geom GEOMETRY(LINESTRING, 4326) NOT NULL,
                base_cost FLOAT NOT NULL,
                capacity FLOAT,
                surface_type VARCHAR
            );
        """))

        print("--- Seeding Admin ---")
        admin_email = "admin@nexus.ai"
        existing = await conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email})
        if not existing.scalar():
            hashed_pw = pwd_context.hash("NexusSecureStart2026!")
            await conn.execute(text("""
                INSERT INTO users (email, hashed_password, is_active, is_superuser)
                VALUES (:email, :pw, TRUE, TRUE)
            """), {"email": admin_email, "pw": hashed_pw})
            print(f"Admin user {admin_email} created.")
        else:
            print("Admin user already exists.")

    await engine.dispose()
    print("✅ Fix complete!")

if __name__ == "__main__":
    asyncio.run(fix_db())
