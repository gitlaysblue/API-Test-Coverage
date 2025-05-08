#!/usr/bin/env python3
"""
API Test Coverage Dashboard
Main entry point for running both the API server and dashboard.
"""
import os
import sys
import argparse
import logging
from multiprocessing import Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Check Python version
if sys.version_info < (3, 8):
    logger.error("This application requires Python 3.8 or higher")
    sys.exit(1)

def start_api_server():
    """Start the FastAPI server for storing test results"""
    try:
        # TODO: Switch to proper daemon mode in production
        from api.server import run_api_server
        logger.info("Starting API server...")
        run_api_server()
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        sys.exit(1)

def start_dashboard():
    """Start the Streamlit dashboard"""
    try:
        # This is a bit hacky but works for now
        import subprocess
        logger.info("Starting Streamlit dashboard...")
        subprocess.run(
            ["streamlit", "run", "dashboard/app.py"],
            check=True,
            # Uncomment below for production deployment
            # env={"STREAMLIT_SERVER_PORT": os.environ.get("DASHBOARD_PORT", "8501")}
        )
    except Exception as e:
        logger.error(f"Failed to start dashboard: {str(e)}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="API Test Coverage Dashboard")
    parser.add_argument(
        "--mode", 
        choices=["api", "dashboard", "all"], 
        default="all",
        help="Component to run (api, dashboard, or all)"
    )
    parser.add_argument(
        "--config", 
        default="config/settings.py",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Load configuration
    if not os.path.exists(args.config):
        logger.warning(f"Config file {args.config} not found, using defaults")
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Run components based on mode
    if args.mode in ["api", "all"]:
        api_process = Process(target=start_api_server)
        api_process.start()
    
    if args.mode in ["dashboard", "all"]:
        if args.mode == "all":
            # Small delay to ensure API is up before dashboard
            import time
            time.sleep(1)
        start_dashboard()
        
    # Keep the process alive if only API is running
    if args.mode == "api":
        try:
            api_process.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            api_process.terminate()
            sys.exit(0) 