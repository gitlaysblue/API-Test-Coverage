"""
FastAPI server for storing and retrieving test results.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports
from api.models.test_result import TestResult, TestStatus, TestRun
from api.routes import results, stats, health

# Set up logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="API Test Coverage API",
    description="API for storing and retrieving API test results",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(health.router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "API Test Coverage API",
        "version": "0.1.0",
        "docs_url": "/docs",
    }

def run_api_server():
    """Run the FastAPI server using uvicorn"""
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", 8000))
    
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=os.environ.get("API_RELOAD", "true").lower() == "true",
    )

if __name__ == "__main__":
    run_api_server() 