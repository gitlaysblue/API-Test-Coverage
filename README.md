# API Test Coverage Dashboard

A tool to automatically test APIs, track coverage, and visualize results.

## Overview

This project takes an OpenAPI/Swagger specification and generates test cases to validate API endpoints. 
Results are visualized in a Streamlit dashboard showing coverage metrics, response times, and other analytics.

## Features

- Parse OpenAPI/Swagger specs to discover endpoints
- Auto-generate test cases for endpoints
- Execute tests via requests or Newman (Postman CLI)
- Track test coverage and results over time
- Visualize results in a real-time dashboard
- Export test results as JSON for CI/CD integration

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your API spec in `config/settings.py`
4. Run the dashboard:
   ```
   python main.py
   ```

## Project Structure

```
api-test-coverage/
├── api/               # FastAPI server for storing test results
├── config/            # Configuration files and settings
├── dashboard/         # Streamlit dashboard components
├── tests/             # Test generation and execution logic
└── utils/             # Helper functions and utilities
```

## TODO

- [x] Initial project setup
- [x] OpenAPI parser implementation
- [ ] Test case generator for different endpoint types
- [ ] MongoDB integration for test results
- [ ] Dashboard improvements and additional metrics
- [ ] CI/CD integration with GitHub Actions
- [ ] Add authentication support for APIs requiring auth

## Notes

Still need to fix the MongoDB connection pooling issue when running tests in parallel.
The dashboard currently refreshes every 5 minutes, might need to adjust based on test frequency.

---

Created by Aman 