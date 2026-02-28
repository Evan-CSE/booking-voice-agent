from aiohttp import web
import time
from ..services.logger import get_logger

logger = get_logger("middleware")

@web.middleware
async def logging_middleware(request: web.Request, handler) -> web.Response:
    """
    AIOHTTP middleware to log incoming requests and outgoing responses.
    """
    start_time = time.monotonic()
    
    # Log the incoming request
    logger.info(f"Incoming Request: {request.method} {request.path}")
    
    try:
        response = await handler(request)
        
        # Log the outgoing response
        process_time = (time.monotonic() - start_time) * 1000
        logger.info(
            f"Outgoing Response: {request.method} {request.path} - "
            f"Status: {response.status} - Duration: {process_time:.2f}ms"
        )
        return response
        
    except Exception as e:
        process_time = (time.monotonic() - start_time) * 1000
        logger.error(
            f"Request Failed: {request.method} {request.path} - "
            f"Error: {str(e)} - Duration: {process_time:.2f}ms"
        )
        raise
