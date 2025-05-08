"""
Streamlit dashboard for visualizing API test results.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from matplotlib import pyplot as plt

# Local imports
from config import settings

# Define API URL
API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

# Page configuration
st.set_page_config(
    page_title="API Test Coverage Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Function to fetch data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_summary_stats(days: int = 7) -> Dict[str, Any]:
    """Fetch summary statistics from the API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/stats/summary?days={days}"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching summary stats: {str(e)}")
        return {}

@st.cache_data(ttl=300)
def fetch_endpoint_stats() -> List[Dict[str, Any]]:
    """Fetch endpoint statistics from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats/endpoints")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching endpoint stats: {str(e)}")
        return []

@st.cache_data(ttl=300)
def fetch_timeline_stats(days: int = 30) -> List[Dict[str, Any]]:
    """Fetch timeline data from the API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/stats/timeline?days={days}"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching timeline stats: {str(e)}")
        return []

@st.cache_data(ttl=300)
def fetch_latest_test_run() -> Dict[str, Any]:
    """Fetch the latest test run data"""
    # In a real app, we'd need an endpoint for this
    # For now, mock the data
    return {
        "run_id": "run-20230607-123456",
        "spec_file": "petstore-openapi.yaml",
        "start_time": "2023-06-07T12:34:56",
        "end_time": "2023-06-07T12:36:12",
        "total_tests": 25,
        "passed_tests": 22,
        "failed_tests": 2,
        "error_tests": 1,
        "skipped_tests": 0,
        "total_endpoints": 10,
        "covered_endpoints": 8,
        "summary": {
            "duration_seconds": 76.5,
            "coverage_percentage": 80.0,
            "success_rate": 88.0,
            "average_response_time": 45.2,
        }
    }

# Sidebar
with st.sidebar:
    st.title("API Test Coverage")
    
    # Filter options
    st.header("Filters")
    time_period = st.selectbox(
        "Time Period",
        options=[7, 14, 30, 90],
        format_func=lambda x: f"Last {x} days",
        index=0,
    )
    
    # Actions
    st.header("Actions")
    if st.button("Run Tests Now", type="primary"):
        # In a real app, this would trigger a test run
        with st.spinner("Running tests..."):
            # Mock a delay
            time.sleep(2)
            st.success("Test run completed!")
    
    # Show API info
    st.header("API Info")
    st.markdown("**Server:** " + settings.API_HOST)
    st.markdown("**API Spec:** " + os.path.basename(settings.DEFAULT_SPEC_PATH))
    
    # Refresh button
    if st.button("Refresh Data"):
        # Clear cached data
        fetch_summary_stats.clear()
        fetch_endpoint_stats.clear()
        fetch_timeline_stats.clear()
        fetch_latest_test_run.clear()
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption("API Test Coverage Dashboard v0.1.0")
    st.caption("© 2023 Acme Corp")

# Main area
st.title("API Test Coverage Dashboard")

# Fetch data
summary_stats = fetch_summary_stats(time_period)
endpoint_stats = fetch_endpoint_stats()
timeline_data = fetch_timeline_stats(time_period)
latest_run = fetch_latest_test_run()

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Test Success Rate",
        f"{summary_stats.get('success_rate', 0):.1f}%",
        delta="+2.1%" if summary_stats else None,
    )

with col2:
    st.metric(
        "API Coverage",
        f"{summary_stats.get('coverage_rate', 0):.1f}%",
        delta="+5.3%" if summary_stats else None,
    )

with col3:
    st.metric(
        "Total Tests Run",
        f"{summary_stats.get('total_tests', 0):,}",
    )

with col4:
    st.metric(
        "Avg Response Time",
        f"{summary_stats.get('average_response_time', 0):.1f} ms",
        delta="-12.3 ms" if summary_stats else None,
        delta_color="inverse",
    )

# Timeline charts
st.header("Test Results Over Time")

if timeline_data:
    # Convert to DataFrame
    df_timeline = pd.DataFrame(timeline_data)
    df_timeline["date"] = pd.to_datetime(df_timeline["date"])
    
    # Create time series chart
    fig_timeline = go.Figure()
    
    # Add traces
    fig_timeline.add_trace(
        go.Scatter(
            x=df_timeline["date"],
            y=df_timeline["passed_tests"],
            name="Passed",
            line=dict(color="green", width=2),
            stackgroup="one",
        )
    )
    
    fig_timeline.add_trace(
        go.Scatter(
            x=df_timeline["date"],
            y=df_timeline["failed_tests"],
            name="Failed",
            line=dict(color="red", width=2),
            stackgroup="one",
        )
    )
    
    # Update layout
    fig_timeline.update_layout(
        title="Daily Test Results",
        xaxis_title="Date",
        yaxis_title="Number of Tests",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Add success rate chart
    fig_success = px.line(
        df_timeline,
        x="date",
        y="success_rate",
        title="Test Success Rate Over Time",
        labels={"date": "Date", "success_rate": "Success Rate (%)"},
    )
    fig_success.update_traces(line_color="blue", line_width=3)
    
    # Add coverage rate to the same chart
    fig_success.add_scatter(
        x=df_timeline["date"],
        y=df_timeline["coverage_rate"],
        name="Coverage Rate",
        line=dict(color="purple", width=2, dash="dash"),
    )
    
    # Update layout
    fig_success.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    
    st.plotly_chart(fig_success, use_container_width=True)
else:
    st.info("No timeline data available yet.")

# Endpoint coverage
st.header("API Endpoint Coverage")

if endpoint_stats:
    # Convert to DataFrame
    df_endpoints = pd.DataFrame(endpoint_stats)
    
    # Calculate coverage
    df_endpoints["coverage"] = df_endpoints["passed_tests"] / df_endpoints["total_tests"] * 100
    
    # Sort by endpoint
    df_endpoints.sort_values("endpoint", inplace=True)
    
    # Create endpoint coverage chart
    fig_endpoints = px.bar(
        df_endpoints,
        x="endpoint",
        y="total_tests",
        color="method",
        title="Tests by Endpoint",
        labels={"endpoint": "Endpoint", "total_tests": "Number of Tests"},
        hover_data=["passed_tests", "failed_tests", "avg_response_time"],
        color_discrete_map={
            "GET": "#17a2b8",
            "POST": "#28a745",
            "PUT": "#ffc107",
            "DELETE": "#dc3545",
            "PATCH": "#6f42c1",
        },
    )
    
    # Update layout
    fig_endpoints.update_layout(
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
    st.plotly_chart(fig_endpoints, use_container_width=True)
    
    # Create a table with endpoint details
    st.subheader("Endpoint Details")
    
    # Format the DataFrame for display
    display_df = df_endpoints.copy()
    display_df["success_rate"] = display_df["passed_tests"] / display_df["total_tests"] * 100
    display_df["success_rate"] = display_df["success_rate"].round(1).astype(str) + "%"
    display_df["avg_response_time"] = display_df["avg_response_time"].round(1).astype(str) + " ms"
    
    # Reorder columns
    display_df = display_df[["endpoint", "method", "total_tests", "passed_tests", "failed_tests", "success_rate", "avg_response_time"]]
    
    # Rename columns
    display_df.columns = ["Endpoint", "Method", "Total Tests", "Passed", "Failed", "Success Rate", "Avg Response Time"]
    
    # Show table
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No endpoint data available yet.")

# Latest test run details
st.header("Latest Test Run")

if latest_run:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Test result pie chart
        results = {
            "Passed": latest_run["passed_tests"],
            "Failed": latest_run["failed_tests"],
            "Error": latest_run["error_tests"],
            "Skipped": latest_run["skipped_tests"],
        }
        
        # Create pie chart
        fig_results = px.pie(
            values=list(results.values()),
            names=list(results.keys()),
            title="Test Results",
            color_discrete_map={
                "Passed": "#28a745",
                "Failed": "#dc3545",
                "Error": "#ffc107",
                "Skipped": "#6c757d",
            },
        )
        
        # Update layout
        fig_results.update_traces(textposition="inside", textinfo="percent+label")
        
        st.plotly_chart(fig_results, use_container_width=True)
    
    with col2:
        # Test run details
        st.subheader("Run Details")
        
        # Format timestamps
        start_time = datetime.fromisoformat(latest_run["start_time"])
        end_time = datetime.fromisoformat(latest_run["end_time"])
        duration = end_time - start_time
        
        # Create two columns for details
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown(f"**Run ID:** {latest_run['run_id']}")
            st.markdown(f"**Spec File:** {latest_run['spec_file']}")
            st.markdown(f"**Start Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Duration:** {duration.total_seconds():.1f} seconds")
        
        with detail_col2:
            st.markdown(f"**Total Tests:** {latest_run['total_tests']}")
            st.markdown(f"**Coverage:** {latest_run['covered_endpoints']} of {latest_run['total_endpoints']} endpoints")
            st.markdown(f"**Success Rate:** {latest_run['summary']['success_rate']:.1f}%")
            st.markdown(f"**Avg Response Time:** {latest_run['summary']['average_response_time']:.1f} ms")
        
        # Add a progress bar for coverage
        coverage_pct = latest_run["covered_endpoints"] / latest_run["total_endpoints"] * 100
        st.progress(coverage_pct / 100, text=f"Coverage: {coverage_pct:.1f}%")
else:
    st.info("No test run data available yet.")

# Export options
st.header("Export Results")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="Export as JSON",
        data=json.dumps({
            "summary": summary_stats,
            "endpoints": endpoint_stats,
            "timeline": timeline_data,
            "latest_run": latest_run,
        }, indent=2),
        file_name="api_test_results.json",
        mime="application/json",
    )

with col2:
    st.download_button(
        label="Export as CSV",
        data=pd.DataFrame(endpoint_stats).to_csv(index=False),
        file_name="api_endpoint_stats.csv",
        mime="text/csv",
    ) 