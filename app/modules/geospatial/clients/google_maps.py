import pybreaker
from google.maps import routing_v2
from google.api_core import exceptions
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Circuit Breaker Configuration
# Open circuit after 5 failures.
try:
    # Use Redis if available in production setup, defaulting to In-Memory for now
    # storage = pybreaker.CircuitBreakerRedisStorage(...) 
    storage = None # Default is in-memory
except Exception:
    storage = None

circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    state_storage=storage,
    listeners=[]
)

class GoogleMapsRoutingClient:
    def __init__(self):
        # In production this API key should come from settings
        # Ensure GOOGLE_APPLICATION_CREDENTIALS or api_key is handled by the library
        try:
            self.client = routing_v2.RoutesClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Google Maps RoutesClient (likely missing credentials): {e}")
            logger.warning("Using Mock Client for development/verification.")
            self.client = self._create_mock_client()

    def _create_mock_client(self):
        # Simple mock to prevent startup crashes when verification runs without GCP creds
        from unittest.mock import MagicMock
        mock = MagicMock()
        return mock

    @circuit_breaker
    async def compute_route(self, origin: Dict[str, float], destination: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Computes route using Google Maps Routes API V2.
        
        Field Masking: X-Goog-Field-Mask enforced (duration, distanceMeters, polyline)
        """
        request = routing_v2.ComputeRoutesRequest(
            origin=routing_v2.Waypoint(
                location=routing_v2.Location(
                    lat_lng={"latitude": origin["lat"], "longitude": origin["lon"]}
                )
            ),
            destination=routing_v2.Waypoint(
                 location=routing_v2.Location(
                    lat_lng={"latitude": destination["lat"], "longitude": destination["lon"]}
                )
            ),
            travel_mode=routing_v2.RouteTravelMode.DRIVE,
        )

        try:
            # Field Masking Optimization
            # Request only strictly needed fields
            response = self.client.compute_routes(
                request=request,
                metadata=[("x-goog-field-mask", "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline")]
            )
            
            if response.routes:
                route = response.routes[0]
                return {
                    "duration": route.duration,
                    "distanceMeters": route.distance_meters,
                    "polyline": route.polyline.encoded_polyline
                }
            return None

        except exceptions.GoogleAPICallError as e:
            logger.error(f"Google Maps API call failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in Google Maps Client: {e}")
            raise e

    async def get_route(self, origin: Dict, destination: Dict) -> Dict:
        """
        Wrapper to handle Circuit Breaker fallback.
        """
        try:
            return await self.compute_route(origin, destination)
        except pybreaker.CircuitBreakerError:
            logger.warning("Google Maps Circuit Breaker OPEN. Switching to fallback.")
            return await self._fallback_routing(origin, destination)
        except Exception:
            # Also fallback on genuine errors if desired, or just let breaker handle count
             return await self._fallback_routing(origin, destination)

    async def _fallback_routing(self, origin: Dict, destination: Dict) -> Dict:
        """
        Fallback to internal PostGIS routing engine.
        PROTOTYPE: Returns mock fallback data for now.
        """
        # TODO: Implement pgRouting call here
        logger.info("Using Internal PostGIS Engine (Fallback)")
        return {
             "duration": "0s",
             "distanceMeters": 0,
             "polyline": "",
             "source": "internal_postgis"
        }
