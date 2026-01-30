import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from geoalchemy2.elements import WKTElement

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.geospatial.models import NavNode, NavEdge

from app.core.config import settings

# Use settings for DB connection (handles Docker vs Local via .env)
DATABASE_URL = settings.DATABASE_URL

async def seed_network():
    # Only seed if tables exist (usually run after alembic upgrade)
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            print("Seeding road network...")
            
            # Create Nodes (North East Only - Guwahati Hub)
            # Node definitions
            # 1: Guwahati (Hub)
            # 2-5: Key Cities in NE
            
            nodes = [
                # Guwahati (Gateway to NE) - Centre
                NavNode(id=1, geom=WKTElement('POINT(91.7362 26.1445)', srid=4326)), 
                # Shillong (South of Guwahati)
                NavNode(id=2, geom=WKTElement('POINT(91.8933 25.5788)', srid=4326)), 
                # Dispur (Close to Guwahati)
                NavNode(id=3, geom=WKTElement('POINT(91.7900 26.1400)', srid=4326)),
                # Nagaon (East)
                NavNode(id=4, geom=WKTElement('POINT(92.6800 26.3400)', srid=4326)),
                # Tezpur (North East)
                NavNode(id=5, geom=WKTElement('POINT(92.7900 26.6500)', srid=4326)),
            ]
            
            # Definitions for wider North East
            ne_locations = [
                {"id": 10, "name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
                {"id": 20, "name": "Shillong", "lat": 25.5788, "lon": 91.8933},
                {"id": 30, "name": "Imphal", "lat": 24.8170, "lon": 93.9368},
                {"id": 40, "name": "Kohima", "lat": 25.6701, "lon": 94.1077},
                {"id": 50, "name": "Itanagar", "lat": 27.0844, "lon": 93.6053},
                {"id": 60, "name": "Aizawl", "lat": 23.7271, "lon": 92.7176},
                {"id": 70, "name": "Agartala", "lat": 23.8315, "lon": 91.2868},
                {"id": 80, "name": "Gangtok", "lat": 27.3389, "lon": 88.6065},
                {"id": 90, "name": "Tawang", "lat": 27.5861, "lon": 91.8594}, 
                {"id": 100, "name": "Cherrapunji", "lat": 25.2702, "lon": 91.7323}
            ]
            
            # Create/Merge Core Nodes
            for n in nodes:
                await session.merge(n)

            # Create Nodes from definitions
            for loc in ne_locations:
                geom = f"POINT({loc['lon']} {loc['lat']})"
                node = NavNode(id=loc['id'], geom=WKTElement(geom, srid=4326))
                await session.merge(node)

            # Generate intermediate "Village" nodes for density
            village_id_start = 200
            villages = []
            import random
            random.seed(42)  
            
            # Generate village nodes bounded by NE coordinates roughly
            for i in range(25):
                lat = random.uniform(25.0, 27.0) # Tighter lat/lon for visible density
                lon = random.uniform(91.0, 93.0)
                vid = village_id_start + i
                villages.append({"id": vid, "lat": lat, "lon": lon, "name": f"Village-{i+1}"})
                node = NavNode(id=vid, geom=WKTElement(f"POINT({lon} {lat})", srid=4326))
                await session.merge(node)
            
            # Create Edges (Inter-city Highways) - Corrected logic
            edges = []
            
            # Main Corridors (Guwahati to others)
            # Use IDs from ne_locations (10=Guwahati)
            
            # Route 1: Guwahati (10) to Shillong (20) - NH-6
            edges.append(NavEdge(
                id=101, source_node=10, target_node=20,
                geom=WKTElement('LINESTRING(91.7362 26.1445, 91.8933 25.5788)', srid=4326),
                base_cost=15.0, capacity=2000, surface_type="asphalt",
                name="NH-6 (Guwahati-Shillong)"
            ))

            # Route 2: Guwahati (10) to Dispur (3) to Nagaon (4)
            edges.append(NavEdge(
                id=102, source_node=10, target_node=3,
                geom=WKTElement('LINESTRING(91.7362 26.1445, 91.7900 26.1400)', srid=4326),
                base_cost=2.0, capacity=1500, surface_type="asphalt",
                name="GS Road"
            ))
            edges.append(NavEdge(
                id=103, source_node=3, target_node=4,
                geom=WKTElement('LINESTRING(91.7900 26.1400, 92.6800 26.3400)', srid=4326),
                base_cost=30.0, capacity=1200, surface_type="asphalt",
                name="NH-27"
            ))

            edge_id = 500
            
            # Connect Villages to nearest Capital (Feeder Roads)
            for v in villages:
                # Find nearest capital
                nearest = min(ne_locations, key=lambda c: (c['lat']-v['lat'])**2 + (c['lon']-v['lon'])**2)
                edge_id += 1
                
                # Check line string validity - simple straight line
                is_remote = random.choice([True, False])
                surface = "gravel" if is_remote else "asphalt"
                capacity = 500 if is_remote else 1000
                road_name = f"PMGSY Rd {v['id']}" if is_remote else f"State Hwy {v['id']}"
                
                edges.append(NavEdge(
                    id=edge_id, source_node=nearest['id'], target_node=v['id'],
                    geom=WKTElement(f"LINESTRING({nearest['lon']} {nearest['lat']}, {v['lon']} {v['lat']})", srid=4326),
                    base_cost=random.uniform(20, 80), capacity=capacity, surface_type=surface,
                    name=road_name
                ))

            for edge in edges:
                await session.merge(edge)
                
            print(f"Seeded {len(edges)} edges (North East Focused).")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_network())
