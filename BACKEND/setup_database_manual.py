
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

# Configuration
PASSWORD = "deb172006"
DATABASE_URL = f"postgresql+asyncpg://postgres:{PASSWORD}@localhost:5432/nexus_ai"

# Password Hashing (Argon2 as per app security)
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto",
    argon2__rounds=1, 
    argon2__memory_cost=65536,
    argon2__parallelism=4
)

async def setup_db():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("--- Enabling PostGIS ---")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

        print("--- Creating Tables ---")
        
        # 1. Users Table
        print("Creating table: users")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR NOT NULL UNIQUE,
                hashed_password VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_superuser BOOLEAN DEFAULT FALSE
            );
            CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
        """))

        # 2. Nav Nodes (Geospatial)
        print("Creating table: nav_nodes")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nav_nodes (
                id BIGSERIAL PRIMARY KEY,
                geom GEOMETRY(POINT, 4326) NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_nav_nodes_id ON nav_nodes (id);
        """))
        
        # 3. Nav Edges (Geospatial + Foreign Keys)
        print("Creating table: nav_edges")
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
            CREATE INDEX IF NOT EXISTS ix_nav_edges_id ON nav_edges (id);
            CREATE INDEX IF NOT EXISTS ix_nav_edges_source_node ON nav_edges (source_node);
            CREATE INDEX IF NOT EXISTS ix_nav_edges_target_node ON nav_edges (target_node);
        """))

        # 4. Edge Dynamic Weights
        print("Creating table: edge_dynamic_weights")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS edge_dynamic_weights (
                id BIGSERIAL PRIMARY KEY,
                edge_id BIGINT NOT NULL REFERENCES nav_edges(id),
                timestamp_window TSTZRANGE NOT NULL,
                weather_penalty_factor FLOAT NOT NULL,
                traffic_speed FLOAT
            );
            CREATE INDEX IF NOT EXISTS ix_edge_dynamic_weights_id ON edge_dynamic_weights (id);
            CREATE INDEX IF NOT EXISTS ix_edge_dynamic_weights_edge_id ON edge_dynamic_weights (edge_id);
            CREATE INDEX IF NOT EXISTS ix_edge_dynamic_weights_timestamp_window ON edge_dynamic_weights (timestamp_window);
        """))

        print("--- Seeding Data ---")
        # Seed Admin
        admin_email = "admin@nexus.ai"
        existing = await conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email})
        if not existing.scalar():
            print(f"Seeding admin user: {admin_email}")
            hashed_pw = pwd_context.hash("NexusSecureStart2026!")
            await conn.execute(text("""
                INSERT INTO users (email, hashed_password, is_active, is_superuser)
                VALUES (:email, :pw, TRUE, TRUE)
            """), {"email": admin_email, "pw": hashed_pw})
        else:
            print("Admin user already exists.")

    await engine.dispose()
    print("✅ Database setup complete!")

if __name__ == "__main__":
    asyncio.run(setup_db())
