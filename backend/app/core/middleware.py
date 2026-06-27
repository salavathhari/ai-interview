import time
from fastapi import Request
from app.core.logging import logger
import json

async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Extract request info
    client_host = request.client.host
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # ms
        
        status_code = response.status_code
        
        # Log successful requests
        log_msg = f"{client_host} - {method} {path} - {status_code} - {process_time:.2f}ms"
        
        if status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
            
        return response
        
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        # Detailed error logging for failed requests
        logger.error(
            f"FAILED REQUEST: {method} {path} | Error: {str(e)} | Time: {process_time:.2f}ms",
            exc_info=True
        )
        raise e
