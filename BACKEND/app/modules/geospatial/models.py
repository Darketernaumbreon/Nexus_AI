from sqlalchemy import Column, Integer, String, Float, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSTZRANGE
from geoalchemy2 import Geometry

from app.db.base import Base

class NavNode(Base):
    __tablename__ = "nav_nodes"

    id = Column(BigInteger, primary_key=True, index=True)
    # SRID 4326 = WGS 84 (GPS coordinates)
    # spatial_index=True creates a GIST index automatically
    geom = Column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)

class NavEdge(Base):
    __tablename__ = "nav_edges"

    id = Column(BigInteger, primary_key=True, index=True)
    source_node = Column(BigInteger, ForeignKey("nav_nodes.id"), nullable=False, index=True)
    target_node = Column(BigInteger, ForeignKey("nav_nodes.id"), nullable=False, index=True)
    
    # Support for complex routing visualization and calculation
    geom = Column(Geometry("LINESTRING", srid=4326, spatial_index=True), nullable=False)
    
    # Navigation attributes
    name = Column(String, nullable=True, comment="Road name (e.g., NH-27)")
    base_cost = Column(Float, nullable=False, comment="Base traversal cost (e.g., length/speed)")
    capacity = Column(Float, nullable=True, comment="Vehicle capacity per hour")
    surface_type = Column(String, nullable=True, comment="e.g., asphalt, dirt, gravel")

    # Relationships
    source = relationship("NavNode", foreign_keys=[source_node])
    target = relationship("NavNode", foreign_keys=[target_node])

class EdgeDynamicWeight(Base):
    __tablename__ = "edge_dynamic_weights"

    id = Column(BigInteger, primary_key=True, index=True)
    edge_id = Column(BigInteger, ForeignKey("nav_edges.id"), nullable=False, index=True)
    
    # Time-variant Data
    # TSTZRANGE handles inclusive/exclusive bounds: '[2023-01-01 10:00, 2023-01-01 11:00)'
    timestamp_window = Column(TSTZRANGE, nullable=False, index=True)
    
    # Dynamic Factors
    weather_penalty_factor = Column(Float, default=1.0, nullable=False)
    traffic_speed = Column(Float, nullable=True, comment="Observed speed in km/h")

    edge = relationship("NavEdge")
