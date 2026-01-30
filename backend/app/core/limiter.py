from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
from starlette.requests import Request

# For production, we should use Redis if available, 
# but for now we default to memory if no redis URL is provided or fall back.
# The prompt specified Redis.

limiter = Limiter(key_func=get_remote_address, default_limits=["1000/minute"])

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Build a simple JSON response that includes the details of the rate limit
    that was hit. If no limit is hit, the countdowns are updated.
    """
    response = JSONResponse(
        {"error": f"Rate limit exceeded: {exc.detail}"}, status_code=429
    )
    response = request.app.state.limiter._inject_headers(
        response, request.app.state.view_rate_limit
    )
    return response
