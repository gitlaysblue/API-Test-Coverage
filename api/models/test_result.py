"""
Models for test results and related data.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator


class TestStatus(str, Enum):
    """Possible statuses for a test case"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    
    
class EndpointMethod(str, Enum):
    """HTTP methods for API endpoints"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class TestResult(BaseModel):
    """Model for individual test results"""
    id: Optional[str] = Field(None, description="Test result ID (auto-generated)")
    test_id: str = Field(..., description="Unique identifier for the test case")
    endpoint: str = Field(..., description="API endpoint that was tested")
    method: EndpointMethod = Field(..., description="HTTP method used for the test")
    status: TestStatus = Field(..., description="Status of the test execution")
    status_code: int = Field(..., description="HTTP status code returned")
    expected_status_code: int = Field(..., description="Expected HTTP status code")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    request_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the request was made"
    )
    request_body: Optional[Dict[str, Any]] = Field(
        None, description="Request body sent (if applicable)"
    )
    request_headers: Optional[Dict[str, str]] = Field(
        None, description="Request headers sent"
    )
    response_body: Optional[Union[Dict[str, Any], List[Any], str]] = Field(
        None, description="Response body received"
    )
    validation_errors: Optional[List[str]] = Field(
        None, description="Validation errors found"
    )
    schema_validated: bool = Field(
        False, description="Whether the response schema was validated"
    )
    schema_validation_passed: Optional[bool] = Field(
        None, description="Whether schema validation passed"
    )
    
    @validator("status")
    def validate_status(cls, v, values):
        """Ensure status matches status_code expectation"""
        if "status_code" in values and "expected_status_code" in values:
            status_code = values["status_code"]
            expected = values["expected_status_code"]
            
            # If status codes match but status is failed, this is likely a schema validation error
            if status_code == expected and v == TestStatus.FAILED:
                return v
            
            # If status codes don't match but status is passed, this is inconsistent
            if status_code != expected and v == TestStatus.PASSED:
                raise ValueError("Status cannot be PASSED when status codes don't match")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "get-users-01",
                "endpoint": "/api/users",
                "method": "GET",
                "status": "passed",
                "status_code": 200,
                "expected_status_code": 200,
                "response_time_ms": 45.2,
                "request_timestamp": "2023-06-07T12:34:56",
                "request_headers": {"Authorization": "Bearer ***"},
                "schema_validated": True,
                "schema_validation_passed": True,
            }
        }


class TestRun(BaseModel):
    """Model for a collection of test results from a single run"""
    id: Optional[str] = Field(None, description="Test run ID (auto-generated)")
    run_id: str = Field(..., description="Unique identifier for this test run")
    spec_file: str = Field(..., description="API spec file used for testing")
    start_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the test run started"
    )
    end_time: Optional[datetime] = Field(
        None, description="When the test run completed"
    )
    total_tests: int = Field(..., description="Total number of tests in this run")
    passed_tests: int = Field(0, description="Number of tests that passed")
    failed_tests: int = Field(0, description="Number of tests that failed")
    error_tests: int = Field(0, description="Number of tests with errors")
    skipped_tests: int = Field(0, description="Number of tests skipped")
    total_endpoints: int = Field(..., description="Total endpoints in API spec")
    covered_endpoints: int = Field(
        0, description="Number of endpoints covered in tests"
    )
    test_results: Optional[List[str]] = Field(
        None, description="IDs of the test results in this run"
    )
    summary: Optional[Dict[str, Any]] = Field(
        None, description="Summary statistics for this test run"
    )
    
    @validator("end_time")
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time"""
        if v and "start_time" in values and values["start_time"]:
            if v < values["start_time"]:
                raise ValueError("End time must be after start time")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "run_id": "run-20230607-123456",
                "spec_file": "api-spec.yaml",
                "start_time": "2023-06-07T12:34:56",
                "end_time": "2023-06-07T12:36:12",
                "total_tests": 25,
                "passed_tests": 22,
                "failed_tests": 2,
                "error_tests": 1,
                "skipped_tests": 0,
                "total_endpoints": 10,
                "covered_endpoints": 8
            }
        } 