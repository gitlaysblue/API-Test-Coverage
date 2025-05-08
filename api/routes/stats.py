"""
API routes for test statistics and analytics.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Path, status

# Local imports
from api.models.test_result import TestStatus
from api.routes.results import test_results_db, test_runs_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary")
async def get_summary_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
):
    """Get summary statistics for the last X days"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Filter test runs within date range
        recent_runs = [
            run for run in test_runs_db 
            if run.start_time >= start_date and run.start_time <= end_date
        ]
        
        # Aggregate stats
        # In a real app, this would be a database aggregation
        total_runs = len(recent_runs)
        total_tests = sum(run.total_tests for run in recent_runs if run.total_tests)
        passed_tests = sum(run.passed_tests for run in recent_runs)
        failed_tests = sum(run.failed_tests for run in recent_runs)
        error_tests = sum(run.error_tests for run in recent_runs)
        
        # Calculate average success rate
        success_rate = 0
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            
        # Calculate average coverage
        coverage_rate = 0
        if total_runs > 0:
            total_coverage = sum(
                run.covered_endpoints / run.total_endpoints * 100
                for run in recent_runs
                if run.total_endpoints > 0
            )
            coverage_rate = total_coverage / total_runs
            
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_runs": total_runs,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": success_rate,
            "coverage_rate": coverage_rate,
        }
    except Exception as e:
        logger.error(f"Error generating summary stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary stats: {str(e)}"
        )


@router.get("/endpoints")
async def get_endpoint_stats():
    """Get statistics grouped by endpoint"""
    try:
        # Group results by endpoint
        endpoints = {}
        
        for result in test_results_db:
            key = f"{result.method}:{result.endpoint}"
            
            if key not in endpoints:
                endpoints[key] = {
                    "endpoint": result.endpoint,
                    "method": result.method,
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "error_tests": 0,
                    "avg_response_time": 0,
                }
            
            # Update stats
            stat = endpoints[key]
            stat["total_tests"] += 1
            
            if result.status == TestStatus.PASSED:
                stat["passed_tests"] += 1
            elif result.status == TestStatus.FAILED:
                stat["failed_tests"] += 1
            elif result.status == TestStatus.ERROR:
                stat["error_tests"] += 1
                
            # Update average response time
            # This is a simple moving average calculation
            old_avg = stat["avg_response_time"]
            stat["avg_response_time"] = old_avg + (result.response_time_ms - old_avg) / stat["total_tests"]
            
        # Convert to list for response
        return list(endpoints.values())
    except Exception as e:
        logger.error(f"Error generating endpoint stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate endpoint stats: {str(e)}"
        )


@router.get("/timeline")
async def get_timeline_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    interval: str = Query("day", description="Interval for grouping (day, week, month)"),
):
    """Get timeline data for charting test results over time"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Group by day (simplified implementation)
        # In a real app, this would be a database aggregation with proper time bucketing
        timeline = []
        
        # Mock data for demonstration
        # In a real app, we'd iterate through actual dates and aggregate real data
        current_date = start_date
        while current_date <= end_date:
            # Create a datapoint for each day
            next_date = current_date + timedelta(days=1)
            
            # Mock values that look like real data with some randomness
            import random
            total = random.randint(50, 200)
            pass_rate = random.uniform(0.85, 0.98)
            passed = int(total * pass_rate)
            failed = total - passed
            
            timeline.append({
                "date": current_date.isoformat(),
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": failed,
                "success_rate": pass_rate * 100,
                "coverage_rate": random.uniform(75, 95),
            })
            
            current_date = next_date
            
        return timeline
    except Exception as e:
        logger.error(f"Error generating timeline stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate timeline stats: {str(e)}"
        ) 