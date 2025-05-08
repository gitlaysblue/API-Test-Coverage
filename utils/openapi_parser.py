"""
Utilities for parsing OpenAPI (Swagger) specifications.
"""
import os
import json
import yaml
import logging
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

import requests
from openapi_spec_validator import validate

logger = logging.getLogger(__name__)


class OpenAPIParser:
    """Parser for OpenAPI specifications"""
    
    def __init__(self, spec_path_or_url: str):
        """
        Initialize the parser with a spec path or URL
        
        Args:
            spec_path_or_url: Path to spec file or URL
        """
        self.spec_path = spec_path_or_url
        self.spec_data = {}
        self.endpoints = []
        
    def load_spec(self) -> bool:
        """
        Load and validate the OpenAPI spec
        
        Returns:
            bool: Whether the spec was loaded successfully
        """
        try:
            # Determine if path or URL
            if self.spec_path.startswith(("http://", "https://")):
                return self._load_from_url()
            else:
                return self._load_from_file()
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec: {str(e)}")
            return False
    
    def _load_from_file(self) -> bool:
        """Load spec from a local file"""
        try:
            path = Path(self.spec_path)
            if not path.exists():
                logger.error(f"Spec file not found: {self.spec_path}")
                return False
                
            with open(path, "r") as f:
                if self.spec_path.endswith((".yaml", ".yml")):
                    self.spec_data = yaml.safe_load(f)
                else:
                    self.spec_data = json.load(f)
                    
            # Validate spec
            validate(self.spec_data)
            
            # Parse endpoints
            self._parse_endpoints()
            return True
        except Exception as e:
            logger.error(f"Error loading spec from file: {str(e)}")
            return False
    
    def _load_from_url(self) -> bool:
        """Load spec from a URL"""
        try:
            response = requests.get(self.spec_path)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            if "yaml" in content_type or self.spec_path.endswith((".yaml", ".yml")):
                self.spec_data = yaml.safe_load(response.text)
            else:
                self.spec_data = response.json()
                
            # Validate spec
            validate(self.spec_data)
            
            # Parse endpoints
            self._parse_endpoints()
            return True
        except Exception as e:
            logger.error(f"Error loading spec from URL: {str(e)}")
            return False
    
    def _parse_endpoints(self) -> None:
        """Parse endpoints from the loaded spec"""
        try:
            # Reset endpoints
            self.endpoints = []
            
            # Get the base path (OpenAPI 2.0 vs 3.0.x)
            base_path = self.spec_data.get("basePath", "")
            
            # Get paths
            paths = self.spec_data.get("paths", {})
            
            for path, path_item in paths.items():
                # Skip parameters at path level
                if path == "parameters":
                    continue
                
                # Build full path
                full_path = f"{base_path}{path}"
                
                # Process HTTP methods
                for method, operation in path_item.items():
                    # Skip non-HTTP methods (like parameters)
                    if method not in ["get", "post", "put", "delete", "patch", "head", "options"]:
                        continue
                    
                    # Add endpoint info
                    self.endpoints.append({
                        "path": full_path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId", f"{method}_{path}"),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": operation.get("parameters", []),
                        "responses": operation.get("responses", {}),
                        "request_body": operation.get("requestBody", None),
                        "security": operation.get("security", []),
                        "tags": operation.get("tags", []),
                    })
            
            logger.info(f"Parsed {len(self.endpoints)} endpoints from spec")
        except Exception as e:
            logger.error(f"Error parsing endpoints: {str(e)}")
            self.endpoints = []
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get the list of parsed endpoints
        
        Returns:
            List of endpoint dictionaries
        """
        return self.endpoints
    
    def get_endpoint_count(self) -> int:
        """
        Get the total number of endpoints
        
        Returns:
            int: Number of endpoints
        """
        return len(self.endpoints)
    
    def get_endpoints_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get endpoints filtered by tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of matching endpoints
        """
        return [e for e in self.endpoints if tag in e.get("tags", [])]
    
    def get_endpoint_details(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific endpoint
        
        Args:
            path: Path of the endpoint
            method: HTTP method
            
        Returns:
            Endpoint details or None if not found
        """
        method = method.upper()
        for endpoint in self.endpoints:
            if endpoint["path"] == path and endpoint["method"] == method:
                return endpoint
        return None
    
    def get_spec_info(self) -> Dict[str, Any]:
        """
        Get basic info about the API
        
        Returns:
            Dict with API info
        """
        info = self.spec_data.get("info", {})
        return {
            "title": info.get("title", "Unknown API"),
            "version": info.get("version", "Unknown"),
            "description": info.get("description", ""),
            "contact": info.get("contact", {}),
            "license": info.get("license", {}),
            "endpoint_count": len(self.endpoints),
        }
    
    def generate_test_case_template(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a template for a test case
        
        Args:
            endpoint: Endpoint info
            
        Returns:
            Test case template
        """
        # Get success response code (prefer 200, 201, etc.)
        success_code = "200"
        for code in endpoint.get("responses", {}).keys():
            if code.startswith("2"):
                success_code = code
                break
        
        # Get parameters
        params = {
            "path": {},
            "query": {},
            "header": {},
            "cookie": {},
        }
        
        for param in endpoint.get("parameters", []):
            param_in = param.get("in", "")
            if param_in in params:
                name = param.get("name", "")
                required = param.get("required", False)
                schema = param.get("schema", {})
                
                # Extract example or default value
                example = param.get("example", None)
                if not example and schema:
                    example = schema.get("example", None)
                    
                if not example and schema:
                    default = schema.get("default", None)
                    if default:
                        example = default
                
                params[param_in][name] = {
                    "required": required,
                    "example": example,
                    "schema": schema,
                }
        
        # Build request body if present
        request_body = None
        if "requestBody" in endpoint:
            req_body = endpoint["requestBody"]
            content = req_body.get("content", {})
            
            # Prefer JSON content
            for content_type in ["application/json", "text/json", "*/*"]:
                if content_type in content:
                    media = content[content_type]
                    schema = media.get("schema", {})
                    example = media.get("example", None)
                    
                    if not example and schema:
                        example = schema.get("example", None)
                    
                    request_body = {
                        "content_type": content_type,
                        "required": req_body.get("required", False),
                        "schema": schema,
                        "example": example,
                    }
                    break
        
        # Return the template
        return {
            "name": f"Test {endpoint['operation_id']}",
            "endpoint": endpoint["path"],
            "method": endpoint["method"],
            "operation_id": endpoint["operation_id"],
            "expected_status_code": int(success_code),
            "params": params,
            "request_body": request_body,
            "expected_response": endpoint.get("responses", {}).get(success_code, {}),
        }
        
    def export_to_postman(self, output_path: str) -> bool:
        """
        Export spec to Postman collection format
        
        Args:
            output_path: Path to save the collection
            
        Returns:
            bool: Whether export was successful
        """
        try:
            info = self.spec_data.get("info", {})
            
            # Create collection structure
            collection = {
                "info": {
                    "name": info.get("title", "API Collection"),
                    "description": info.get("description", ""),
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                },
                "item": [],
            }
            
            # Group by tags
            tag_groups = {}
            for endpoint in self.endpoints:
                tags = endpoint.get("tags", ["No Tag"])
                tag = tags[0] if tags else "No Tag"
                
                if tag not in tag_groups:
                    tag_groups[tag] = []
                    
                tag_groups[tag].append(endpoint)
            
            # Build items
            for tag, endpoints in tag_groups.items():
                folder = {
                    "name": tag,
                    "item": [],
                }
                
                for endpoint in endpoints:
                    test_template = self.generate_test_case_template(endpoint)
                    
                    # Build item
                    item = {
                        "name": endpoint.get("summary", endpoint["operation_id"]),
                        "request": {
                            "method": endpoint["method"],
                            "header": [],
                            "url": {
                                "raw": "{{baseUrl}}" + endpoint["path"],
                                "host": ["{{baseUrl}}"],
                                "path": endpoint["path"].strip("/").split("/"),
                                "variable": [],
                            },
                            "description": endpoint.get("description", ""),
                        },
                        "response": [],
                    }
                    
                    # Add to folder
                    folder["item"].append(item)
                
                # Add folder to collection
                collection["item"].append(folder)
                
            # Write collection to file
            with open(output_path, "w") as f:
                json.dump(collection, f, indent=2)
                
            logger.info(f"Exported Postman collection to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to Postman: {str(e)}")
            return False 