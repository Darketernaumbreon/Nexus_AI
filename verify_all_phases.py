import asyncio
import sys
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("verification")

async def verify_phases():
    print(">>> Starting Verification for Phases 1-4 <<<")

    # Phase 1: Core
    try:
        print("[Phase 1] Checking Core Imports...")
        from app.db.session import engine
        from app.modules.iam.models import User
        from app.modules.iam.security import create_access_token
        print("   - DB Engine: OK")
        print("   - User Model: OK")
        print("   - Security Utils: OK")
    except Exception as e:
        print(f"!!! Phase 1 Failed: {e}")
        sys.exit(1)

    # Phase 2: Geospatial
    try:
        print("[Phase 2] Checking Geospatial Models...")
        from app.modules.geospatial.models import NavNode, NavEdge, EdgeDynamicWeight
        print("   - NavNode/NavEdge: OK")
    except Exception as e:
        print(f"!!! Phase 2 Failed: {e}")
        sys.exit(1)

    # Phase 3: Security
    try:
        print("[Phase 3] Checking Security Architecture...")
        from app.core.limiter import limiter
        if settings.ALGORITHM != "RS256":
            raise ValueError(f"Algorithm must be RS256, got {settings.ALGORITHM}")
        # Verify keys are loaded
        if not settings.PRIVATE_KEY or not settings.PUBLIC_KEY:
             raise ValueError("RSA Keys not loaded in settings!")
        print("   - Rate Limiter: OK")
        print("   - RS256 Config: OK")
    except Exception as e:
        print(f"!!! Phase 3 Failed: {e}")
        sys.exit(1)

    # Phase 4: Integrations
    try:
        print("[Phase 4] Checking External Integrations...")
        from app.modules.geospatial.clients.google_maps import GoogleMapsRoutingClient
        client = GoogleMapsRoutingClient()
        print("   - Google Maps Client Instantiation: OK")
        
        from app.modules.environmental.tasks.etl import etl_imd_weather_data
        print("   - IMD ETL Task Import: OK")
    except Exception as e:
        print(f"!!! Phase 4 Failed: {e}")
        sys.exit(1)

    print("\n>>> ALL PHASES VERIFIED SUCCESSFULLY <<<")

if __name__ == "__main__":
    asyncio.run(verify_phases())
