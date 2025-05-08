"""
Test case generator for API endpoints based on OpenAPI specifications.
"""
import os
import json
import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

# Local imports
from utils.openapi_parser import OpenAPIParser
from config import settings

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generator for API test cases"""
    
    def __init__(self, spec_path: str):
        """
        Initialize the test generator
        
        Args:
            spec_path: Path to the OpenAPI spec
        """
        self.spec_path = spec_path
        self.parser = OpenAPIParser(spec_path)
        self.endpoints = []
        self.test_cases = []
        
    def load_spec(self) -> bool:
        """
        Load the API specification
        
        Returns:
            bool: Whether the spec was loaded successfully
        """
        result = self.parser.load_spec()
        if result:
            self.endpoints = self.parser.get_endpoints()
        return result
    
    def generate_test_cases(self) -> List[Dict[str, Any]]:
        """
        Generate test cases for all endpoints
        
        Returns:
            List of test case definitions
        """
        self.test_cases = []
        
        for endpoint in self.endpoints:
            # Generate multiple test cases per endpoint
            endpoint_tests = self._generate_tests_for_endpoint(endpoint)
            self.test_cases.extend(endpoint_tests)
            
        logger.info(f"Generated {len(self.test_cases)} test cases")
        return self.test_cases
    
    def _generate_tests_for_endpoint(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate test cases for a single endpoint
        
        Args:
            endpoint: Endpoint information
            
        Returns:
            List of test cases for this endpoint
        """
        test_cases = []
        method = endpoint["method"]
        path = endpoint["path"]
        operation_id = endpoint["operation_id"]
        
        # Get a base test case template
        base_template = self.parser.generate_test_case_template(endpoint)
        
        # Always include a happy path test
        happy_path = base_template.copy()
        happy_path["name"] = f"{operation_id}_happy_path"
        happy_path["description"] = f"Test {method} {path} with valid inputs"
        happy_path["tags"] = ["happy_path"] + endpoint.get("tags", [])
        
        # Add test case specific data
        self._populate_test_parameters(happy_path, base_template)
        test_cases.append(happy_path)
        
        # If endpoint has required parameters, add a test case with missing params
        required_params = self._get_required_parameters(endpoint)
        if required_params:
            missing_params_test = base_template.copy()
            missing_params_test["name"] = f"{operation_id}_missing_params"
            missing_params_test["description"] = f"Test {method} {path} with missing required parameters"
            missing_params_test["expected_status_code"] = 400  # Bad Request
            missing_params_test["tags"] = ["negative", "validation"] + endpoint.get("tags", [])
            
            # Deliberately omit a required parameter
            omitted = random.choice(required_params)
            missing_params_test["omitted_parameter"] = omitted
            
            # Add test case specific data, skipping the omitted parameter
            self._populate_test_parameters(missing_params_test, base_template, skip_param=omitted)
            test_cases.append(missing_params_test)
        
        # If endpoint accepts request body, add a test with invalid body
        if "requestBody" in endpoint:
            invalid_body_test = base_template.copy()
            invalid_body_test["name"] = f"{operation_id}_invalid_body"
            invalid_body_test["description"] = f"Test {method} {path} with invalid request body"
            invalid_body_test["expected_status_code"] = 400  # Bad Request
            invalid_body_test["tags"] = ["negative", "validation"] + endpoint.get("tags", [])
            
            # Create an invalid body (just an empty object for simplicity)
            invalid_body_test["request_body_override"] = {}
            
            # Add test case specific data
            self._populate_test_parameters(invalid_body_test, base_template)
            test_cases.append(invalid_body_test)
        
        # Add more test cases as needed for specific endpoints
        # This could be expanded based on endpoint types, authentication requirements, etc.
        
        return test_cases
    
    def _get_required_parameters(self, endpoint: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get a list of required parameters
        
        Args:
            endpoint: Endpoint information
            
        Returns:
            List of required parameter info: [{name, in}, ...]
        """
        required = []
        
        # Check standard parameters
        for param in endpoint.get("parameters", []):
            if param.get("required", False):
                required.append({
                    "name": param.get("name", ""),
                    "in": param.get("in", ""),
                })
        
        # Check request body if present
        if "requestBody" in endpoint:
            req_body = endpoint["requestBody"]
            if req_body.get("required", False):
                required.append({
                    "name": "requestBody",
                    "in": "body",
                })
                
        return required
    
    def _populate_test_parameters(self, test_case: Dict[str, Any], template: Dict[str, Any], skip_param: Dict[str, str] = None) -> None:
        """
        Populate test parameters with values
        
        Args:
            test_case: Test case to populate
            template: Base template with defaults
            skip_param: Parameter to skip (for negative testing)
        """
        # Clone the params structure
        params = {
            "path": template["params"]["path"].copy(),
            "query": template["params"]["query"].copy(),
            "header": template["params"]["header"].copy(),
            "cookie": template["params"]["cookie"].copy(),
        }
        
        # If we're skipping a parameter, remove it
        if skip_param:
            param_name = skip_param["name"]
            param_in = skip_param["in"]
            
            if param_in in params and param_name in params[param_in]:
                del params[param_in][param_name]
        
        # Generate values for parameters without examples
        for param_type, param_dict in params.items():
            for name, info in param_dict.items():
                if info["example"] is None:
                    # Generate a value based on schema
                    schema = info.get("schema", {})
                    info["example"] = self._generate_value_from_schema(schema)
        
        # Handle request body
        request_body = None
        if template["request_body"]:
            # Check if there's an override (for negative testing)
            if "request_body_override" in test_case:
                request_body = test_case["request_body_override"]
                del test_case["request_body_override"]
            else:
                # Use example if available
                request_body = template["request_body"].get("example", None)
                
                # Generate if no example
                if not request_body:
                    schema = template["request_body"].get("schema", {})
                    request_body = self._generate_value_from_schema(schema)
        
        # Update the test case
        test_case["params"] = params
        if request_body is not None:
            test_case["request_body_value"] = request_body
    
    def _generate_value_from_schema(self, schema: Dict[str, Any]) -> Any:
        """
        Generate a value based on JSON schema
        
        Args:
            schema: JSON schema
            
        Returns:
            Generated value
        """
        # Get the type
        schema_type = schema.get("type", "string")
        
        if schema_type == "string":
            # Check format
            fmt = schema.get("format", "")
            if fmt == "date-time":
                return datetime.utcnow().isoformat()
            elif fmt == "date":
                return datetime.utcnow().date().isoformat()
            elif fmt == "email":
                return "test@example.com"
            elif fmt == "uuid":
                import uuid
                return str(uuid.uuid4())
            else:
                # Check enum
                if "enum" in schema:
                    return random.choice(schema["enum"])
                # Generate a random string
                length = min(10, schema.get("maxLength", 10))
                return ''.join(random.choices(string.ascii_letters, k=length))
                
        elif schema_type == "number" or schema_type == "integer":
            minimum = schema.get("minimum", 0)
            maximum = schema.get("maximum", 100)
            if schema_type == "integer":
                return random.randint(minimum, maximum)
            else:
                return random.uniform(minimum, maximum)
                
        elif schema_type == "boolean":
            return random.choice([True, False])
            
        elif schema_type == "array":
            # Generate a small array of items
            items_schema = schema.get("items", {})
            min_items = schema.get("minItems", 1)
            max_items = min(5, schema.get("maxItems", 5))
            count = random.randint(min_items, max_items)
            
            return [self._generate_value_from_schema(items_schema) for _ in range(count)]
            
        elif schema_type == "object":
            # Generate object with required properties
            result = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for name, prop_schema in properties.items():
                if name in required or random.random() > 0.5:  # Include non-required properties 50% of the time
                    result[name] = self._generate_value_from_schema(prop_schema)
                    
            return result
            
        # Default case
        return None
        
    def export_test_cases(self, output_path: str) -> bool:
        """
        Export test cases to JSON file
        
        Args:
            output_path: Path to save test cases
            
        Returns:
            bool: Whether export was successful
        """
        try:
            with open(output_path, "w") as f:
                json.dump(self.test_cases, f, indent=2)
                
            logger.info(f"Exported {len(self.test_cases)} test cases to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting test cases: {str(e)}")
            return False 