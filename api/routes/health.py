"""
Health check endpoints for monitoring API status.
"""
import logging
import time
from typing import Dict

from fastapi import APIRouter, Response, status

router = APIRouter()
logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_start_time = time.time()


@router.get("/ping")
async def ping():
    """Simple health check endpoint that returns pong"""
    return {"status": "ok", "message": "pong"}


@router.get("/status")
async def health_status():
    """
    Detailed health check with system status
    """
    try:
        # Calculate uptime in seconds
        uptime = time.time() - _start_time
        
        # In a real app, we'd check DB connection, etc.
        # This is just a mock
        db_status = "connected"
        
        return {
            "status": "ok",
            "uptime_seconds": uptime,
            "version": "0.1.0",
            "components": {
                "database": db_status,
                "api": "healthy",
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        ) 