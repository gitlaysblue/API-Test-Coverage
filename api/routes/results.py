"""
API routes for managing test results.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from fastapi import APIRouter, HTTPException, Query, Path, Body, status, Depends
from pydantic import BaseModel

# Local imports
from api.models.test_result import TestResult, TestRun, TestStatus

# TODO: Replace with actual DB implementation
# For now, we'll use in-memory storage
test_results_db = []
test_runs_db = []

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper functions
def _generate_id(prefix="res"):
    """Generate a simple ID for database entries"""
    from uuid import uuid4
    return f"{prefix}-{str(uuid4())[:8]}"

def _get_test_result(result_id: str) -> Optional[TestResult]:
    """Get a test result by ID"""
    for result in test_results_db:
        if result.id == result_id:
            return result
    return None

def _get_test_run(run_id: str) -> Optional[TestRun]:
    """Get a test run by ID"""
    for run in test_runs_db:
        if run.run_id == run_id:
            return run
    return None


@router.post("/", response_model=TestResult, status_code=status.HTTP_201_CREATED)
async def create_test_result(result: TestResult):
    """Create a new test result"""
    try:
        # Set ID if not provided
        if not result.id:
            result.id = _generate_id()
            
        # Validate test result
        # (Pydantic validation happens automatically)
        
        # Store in database
        test_results_db.append(result)
        logger.info(f"Created test result: {result.id}")
        
        return result
    except Exception as e:
        logger.error(f"Error creating test result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test result: {str(e)}"
        )


@router.get("/", response_model=List[TestResult])
async def get_test_results(
    run_id: Optional[str] = Query(None, description="Filter by test run ID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    status: Optional[TestStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Get test results with optional filtering"""
    try:
        results = test_results_db
        
        # Apply filters
        if endpoint:
            results = [r for r in results if r.endpoint == endpoint]
        if status:
            results = [r for r in results if r.status == status]
            
        # Apply pagination
        results = results[offset:offset + limit]
        
        return results
    except Exception as e:
        logger.error(f"Error getting test results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test results: {str(e)}"
        )


@router.get("/{result_id}", response_model=TestResult)
async def get_test_result(
    result_id: str = Path(..., description="Test result ID"),
):
    """Get a specific test result by ID"""
    try:
        result = _get_test_result(result_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test result with ID {result_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test result {result_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test result: {str(e)}"
        )


@router.post("/run", response_model=TestRun, status_code=status.HTTP_201_CREATED)
async def create_test_run(run: TestRun):
    """Create a new test run record"""
    try:
        # Set ID if not provided
        if not run.id:
            run.id = _generate_id("run")
        
        # Store in database
        test_runs_db.append(run)
        logger.info(f"Created test run: {run.run_id}")
        
        return run
    except Exception as e:
        logger.error(f"Error creating test run: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test run: {str(e)}"
        )


@router.get("/run/{run_id}", response_model=TestRun)
async def get_test_run(
    run_id: str = Path(..., description="Test run ID"),
):
    """Get a specific test run by ID"""
    try:
        run = _get_test_run(run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test run with ID {run_id} not found"
            )
        return run
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test run {run_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test run: {str(e)}"
        )


@router.put("/run/{run_id}/complete", response_model=TestRun)
async def complete_test_run(
    run_id: str = Path(..., description="Test run ID"),
):
    """Mark a test run as complete and update stats"""
    try:
        run = _get_test_run(run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test run with ID {run_id} not found"
            )
        
        # Update end time
        run.end_time = datetime.utcnow()
        
        # Update test stats (in a real app, this would query the DB)
        # Just a mock implementation for now
        run.passed_tests = 15
        run.failed_tests = 3
        run.error_tests = 1
        run.skipped_tests = 2
        run.total_tests = 21
        run.covered_endpoints = 7
        
        # Generate a summary
        run.summary = {
            "duration_seconds": (run.end_time - run.start_time).total_seconds(),
            "success_rate": run.passed_tests / run.total_tests * 100,
            "coverage_rate": run.covered_endpoints / run.total_endpoints * 100,
        }
        
        logger.info(f"Completed test run: {run_id}")
        return run
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing test run {run_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete test run: {str(e)}"
        ) 