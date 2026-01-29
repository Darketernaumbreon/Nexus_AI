import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from geoalchemy2.elements import WKTElement

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.geospatial.models import NavNode, NavEdge

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/nexus_ai"

async def seed_network():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            print("Seeding road network...")
            
            # Create Nodes (Around Delhi)
            nodes = [
                NavNode(id=1, geom=WKTElement('POINT(77.2090 28.6139)', srid=4326)), # CP
                NavNode(id=2, geom=WKTElement('POINT(77.2295 28.6129)', srid=4326)), # India Gate
                NavNode(id=3, geom=WKTElement('POINT(77.2060 28.5245)', srid=4326)), # Qutub Minar (South)
                NavNode(id=4, geom=WKTElement('POINT(77.2500 28.5500)', srid=4326)), # Lotus Temple
                NavNode(id=5, geom=WKTElement('POINT(77.1000 28.7000)', srid=4326)), # Rohini (North West)
            ]
            
            # Definitions for North East Capitals & Key Locations
            ne_locations = [
                {"id": 10, "name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
                {"id": 20, "name": "Shillong", "lat": 25.5788, "lon": 91.8933},
                {"id": 30, "name": "Imphal", "lat": 24.8170, "lon": 93.9368},
                {"id": 40, "name": "Kohima", "lat": 25.6701, "lon": 94.1077},
                {"id": 50, "name": "Itanagar", "lat": 27.0844, "lon": 93.6053},
                {"id": 60, "name": "Aizawl", "lat": 23.7271, "lon": 92.7176},
                {"id": 70, "name": "Agartala", "lat": 23.8315, "lon": 91.2868},
                {"id": 80, "name": "Gangtok", "lat": 27.3389, "lon": 88.6065},
                {"id": 90, "name": "Tawang", "lat": 27.5861, "lon": 91.8594}, # Mountainous
                {"id": 100, "name": "Cherrapunji", "lat": 25.2702, "lon": 91.7323} # High Rainfall
            ]
            
            # Create Nodes
            for loc in ne_locations:
                geom = f"POINT({loc['lon']} {loc['lat']})"
                node = NavNode(id=loc['id'], geom=WKTElement(geom, srid=4326))
                await session.merge(node)

            # Generate intermediate "Village" nodes
            village_id_start = 200
            villages = []
            import random
            random.seed(42)  
            
            for i in range(20):
                lat = random.uniform(23.0, 28.0)
                lon = random.uniform(90.0, 95.0)
                vid = village_id_start + i
                villages.append({"id": vid, "lat": lat, "lon": lon, "name": f"Village-{i+1}"})
                node = NavNode(id=vid, geom=WKTElement(f"POINT({lon} {lat})", srid=4326))
                await session.merge(node)

            print("Nodes created (North East Capitals + Villages).")
            
            # Create Edges (Inter-city Highways)
            edges = [
                # CP to India Gate
                NavEdge(
                    id=101, source_node=1, target_node=2,
                    geom=WKTElement('LINESTRING(77.2090 28.6139, 77.2295 28.6129)', srid=4326),
                    base_cost=2.5, capacity=1000, surface_type="asphalt",
                    name="Rajpath"
                ),
                # India Gate to Lotus Temple
                NavEdge(
                    id=102, source_node=2, target_node=4,
                    geom=WKTElement('LINESTRING(77.2295 28.6129, 77.2500 28.5500)', srid=4326),
                    base_cost=8.0, capacity=1500, surface_type="asphalt",
                    name="Mathura Rd"
                ),
                # Lotus to Qutub
                NavEdge(
                    id=103, source_node=4, target_node=3,
                    geom=WKTElement('LINESTRING(77.2500 28.5500, 77.2060 28.5245)', srid=4326),
                    base_cost=6.0, capacity=1200, surface_type="asphalt",
                    name="Outer Ring Rd"
                ),
                # CP to Rohini (Long route)
                NavEdge(
                    id=104, source_node=1, target_node=5,
                    geom=WKTElement('LINESTRING(77.2090 28.6139, 77.1000 28.7000)', srid=4326),
                    base_cost=15.0, capacity=800, surface_type="GRAVEL",
                    name="Rohtak Rd"
                ),
            ]
            edge_id = 500
            
            # Connect Capitals to Guwahati (Hub)
            hub = ne_locations[0] # Guwahati
            for loc in ne_locations[1:]:
                edge_id += 1
                # Assign a proper Highway Name
                hw_name = f"NH-{random.randint(2, 50)}: {hub['name']}-{loc['name']}"
                
                edges.append(NavEdge(
                    id=edge_id, source_node=hub['id'], target_node=loc['id'],
                    geom=WKTElement(f"LINESTRING({hub['lon']} {hub['lat']}, {loc['lon']} {loc['lat']})", srid=4326),
                    base_cost=random.uniform(50, 200), capacity=2000, surface_type="highway",
                    name=hw_name
                ))
            
            # Connect Villages to nearest Capital (Feeder Roads)
            for v in villages:
                # Find nearest capital
                nearest = min(ne_locations, key=lambda c: (c['lat']-v['lat'])**2 + (c['lon']-v['lon'])**2)
                edge_id += 1
                # Mountainous/Remote attribute
                is_remote = random.choice([True, False])
                surface = "gravel" if is_remote else "asphalt"
                capacity = 500 if is_remote else 1000
                road_name = f"Rural Rd {v['id']}" if is_remote else f"State Hwy {v['id']}"
                
                edges.append(NavEdge(
                    id=edge_id, source_node=nearest['id'], target_node=v['id'],
                    geom=WKTElement(f"LINESTRING({nearest['lon']} {nearest['lat']}, {v['lon']} {v['lat']})", srid=4326),
                    base_cost=random.uniform(20, 80), capacity=capacity, surface_type=surface,
                    name=road_name
                ))

            
            for edge in edges:
                await session.merge(edge)
                
            print(f"Seeded {len(edges)} edges.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_network())
