#!/usr/bin/env python3
"""
Command-line interface for running API tests.
"""
import os
import sys
import json
import logging
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Local imports
from tests.test_generator import TestGenerator
from tests.test_executor import TestExecutor
from utils.openapi_parser import OpenAPIParser
from config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE),
    ],
)
logger = logging.getLogger(__name__)


async def run_tests(args):
    """Run API tests based on command-line arguments"""
    try:
        # Load the OpenAPI spec
        spec_path = args.spec or settings.DEFAULT_SPEC_PATH
        logger.info(f"Loading OpenAPI spec from {spec_path}")
        
        # Generate test cases
        generator = TestGenerator(spec_path)
        if not generator.load_spec():
            logger.error("Failed to load OpenAPI spec")
            return 1
        
        # Generate test cases
        if args.generate_only:
            # Just generate test cases and save to file
            test_cases = generator.generate_test_cases()
            output_path = args.output or Path(settings.DATA_DIR) / "generated_tests.json"
            if generator.export_test_cases(output_path):
                logger.info(f"Exported {len(test_cases)} test cases to {output_path}")
                return 0
            else:
                logger.error("Failed to export test cases")
                return 1
                
        # Generate and execute test cases
        test_cases = generator.generate_test_cases()
        logger.info(f"Generated {len(test_cases)} test cases")
        
        # If a test case file was specified, load from there instead
        if args.tests:
            try:
                with open(args.tests, "r") as f:
                    test_cases = json.load(f)
                logger.info(f"Loaded {len(test_cases)} test cases from {args.tests}")
            except Exception as e:
                logger.error(f"Failed to load test cases from {args.tests}: {str(e)}")
                return 1
        
        # Limit test cases if specified
        if args.limit and args.limit > 0:
            test_cases = test_cases[:args.limit]
            logger.info(f"Limited to {len(test_cases)} test cases")
        
        # Export test cases if requested
        if args.export_tests:
            output_path = args.output or Path(settings.DATA_DIR) / "generated_tests.json"
            if generator.export_test_cases(output_path):
                logger.info(f"Exported {len(test_cases)} test cases to {output_path}")
        
        # Execute test cases
        base_url = args.url or "http://localhost:8000"
        logger.info(f"Executing tests against {base_url}")
        
        executor = TestExecutor(base_url, test_cases)
        results = await executor.execute_tests()
        
        # Export results if requested
        if args.export_results:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            output_path = args.output or Path(settings.TEST_RESULTS_DIR) / f"test_results_{timestamp}.json"
            if executor.export_results(output_path):
                logger.info(f"Exported test results to {output_path}")
        
        # Print summary
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        errors = sum(1 for r in results if r.status == "error")
        skipped = sum(1 for r in results if r.status == "skipped")
        
        logger.info("Test execution complete")
        logger.info(f"Total tests: {len(results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Skipped: {skipped}")
        
        # Export to Postman collection if requested
        if args.export_postman:
            postman_path = args.postman_output or Path(settings.DATA_DIR) / "postman_collection.json"
            parser = OpenAPIParser(spec_path)
            if parser.load_spec() and parser.export_to_postman(postman_path):
                logger.info(f"Exported Postman collection to {postman_path}")
        
        # Return non-zero exit code if there were failures
        return 0 if failed == 0 and errors == 0 else 1
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        return 1


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Run API tests based on OpenAPI spec")
    
    # Basic options
    parser.add_argument(
        "--spec", "-s",
        help="Path to OpenAPI spec file",
    )
    parser.add_argument(
        "--url", "-u",
        help="Base URL for the API",
    )
    parser.add_argument(
        "--tests", "-t",
        help="Path to JSON file with test cases",
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to output file for test cases or results",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit the number of tests to run",
    )
    
    # Export options
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only generate test cases, don't execute them",
    )
    parser.add_argument(
        "--export-tests",
        action="store_true",
        help="Export generated test cases to file",
    )
    parser.add_argument(
        "--export-results",
        action="store_true",
        help="Export test results to file",
    )
    parser.add_argument(
        "--export-postman",
        action="store_true",
        help="Export OpenAPI spec to Postman collection",
    )
    parser.add_argument(
        "--postman-output",
        help="Path to output file for Postman collection",
    )
    
    # Logging options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output except for errors",
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Run tests
    exit_code = asyncio.run(run_tests(args))
    sys.exit(exit_code) 