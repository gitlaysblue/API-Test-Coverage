"""
Application settings and configuration.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEST_RESULTS_DIR = DATA_DIR / "test_results"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TEST_RESULTS_DIR.mkdir(exist_ok=True)

# API server settings
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_RELOAD = os.environ.get("API_RELOAD", "true").lower() == "true"
API_DEBUG = os.environ.get("API_DEBUG", "true").lower() == "true"

# Dashboard settings
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8501"))

# Database settings
# Currently using file-based storage, but could switch to MongoDB
USE_MONGODB = os.environ.get("USE_MONGODB", "false").lower() == "true"
MONGODB_URI = os.environ.get(
    "MONGODB_URI", "mongodb://localhost:27017/api_test_coverage"
)

# API Testing settings
DEFAULT_SPEC_PATH = os.environ.get("DEFAULT_SPEC_PATH", str(DATA_DIR / "api-spec.yaml"))
DEFAULT_POSTMAN_COLLECTION = os.environ.get(
    "DEFAULT_POSTMAN_COLLECTION", str(DATA_DIR / "postman_collection.json")
)

# Number of tests to generate per endpoint (by default)
TESTS_PER_ENDPOINT = int(os.environ.get("TESTS_PER_ENDPOINT", "3"))

# Test timeout in seconds
TEST_TIMEOUT = float(os.environ.get("TEST_TIMEOUT", "10.0"))

# Whether to validate response schemas
VALIDATE_SCHEMAS = os.environ.get("VALIDATE_SCHEMAS", "true").lower() == "true"

# Whether to save response bodies (can get large)
SAVE_RESPONSE_BODIES = os.environ.get("SAVE_RESPONSE_BODIES", "false").lower() == "true"

# Test report settings
REPORT_FORMAT = os.environ.get("REPORT_FORMAT", "json")  # json, html, or both
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# GitHub integration for CI/CD
GITHUB_ENABLED = os.environ.get("GITHUB_ENABLED", "false").lower() == "true"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")

# Logging settings
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.environ.get("LOG_FILE", str(BASE_DIR / "api_test_coverage.log"))

# Notification settings
ENABLE_NOTIFICATIONS = os.environ.get("ENABLE_NOTIFICATIONS", "false").lower() == "true"
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Authentication settings
AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "false").lower() == "true"
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "dev-token-1234")

# Load default test data if available
DEFAULT_TEST_DATA = {}
default_data_path = DATA_DIR / "default_test_data.json"
if default_data_path.exists():
    try:
        with open(default_data_path, "r") as f:
            DEFAULT_TEST_DATA = json.load(f)
    except json.JSONDecodeError:
        logging.warning(f"Failed to parse default test data: {default_data_path}")
    except Exception as e:
        logging.warning(f"Error loading default test data: {str(e)}")

# Load a local settings file if it exists
try:
    from .local_settings import *  # noqa
except ImportError:
    pass  # No local settings 