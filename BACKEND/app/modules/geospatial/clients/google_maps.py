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
        # We prefer the Settings API KEY
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        
        if self.api_key:
            logger.info("Initializing Google Maps Client with API Key.")
            try:
                # For basic Routing V2 via REST (HTTP/1.1) when using ONLY API Key (not Service Account)
                # The python client library strictly prefers ADC (Application Default Credentials).
                # To use API Key directly, we might need to rely on direct HTTP requests 
                # OR configure the client options carefully.
                # For stability in this hybrid env, we will use a direct HTTP wrapper if API Key is present,
                # effectively bypassing the library's strict auth requirements if they fail.
                self.client = None # We will use direct requests in compute_route
            except Exception as e:
                logger.warning(f"Failed to init Google Maps: {e}")
                self.client = self._create_mock_client()
        else:
            logger.warning("No Google Maps API Key found. Using Mock Client.")
            self.client = self._create_mock_client()

    def _create_mock_client(self):
        # ... validation mock ...
        pass

    @circuit_breaker
    async def compute_route(self, origin: Dict[str, float], destination: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Computes route using Google Maps Routes API.
        """
        if not self.api_key:
            # Fallback to internal or returns None
            return None
            
        import httpx
        
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-Field-Mask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
        }
        
        body = {
            "origin": {
                "location": {
                    "latLng": {"latitude": origin["lat"], "longitude": origin["lon"]}
                }
            },
            "destination": {
                "location": {
                    "latLng": {"latitude": destination["lat"], "longitude": destination["lon"]}
                }
            },
            "travelMode": "DRIVE"
        }
        
        try:
             async with httpx.AsyncClient() as client:
                response = await client.post(url, json=body, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if "routes" in data and data["routes"]:
                        route = data["routes"][0]
                        return {
                            "duration": route.get("duration"),
                            "distanceMeters": route.get("distanceMeters"),
                            "polyline": route.get("polyline", {}).get("encodedPolyline")
                        }
                else:
                    logger.error(f"Google Maps API Error: {response.status_code} {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Google Maps Request Failed: {e}")
            raise e
        
        return None

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
