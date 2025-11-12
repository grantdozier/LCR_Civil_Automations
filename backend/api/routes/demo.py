"""
DEMO Module - Demonstration API Endpoints

This module provides a simple demonstration of the complete DIA workflow
with pre-populated sample data and one-click execution.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging

from core import get_db
from services.demo import DemoService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class DemoProjectResponse(BaseModel):
    """Response from demo project creation"""
    project_id: str
    project_number: str
    project_name: str
    drainage_areas: int
    drainage_area_ids: List[str]
    total_area_acres: float
    message: str


class DemoRunRequest(BaseModel):
    """Request to run DIA demo"""
    project_id: str = Field(..., description="Demo project UUID")
    storm_events: Optional[List[str]] = Field(
        ["10-year", "25-year"],
        description="Storm events to analyze"
    )
    tc_method: str = Field("nrcs", description="Tc calculation method: nrcs, kirpich, faa")


class DemoRunResponse(BaseModel):
    """Response from demo run"""
    run_id: str
    project_id: str
    status: str
    results_summary: Dict[str, Any]
    total_results: int
    message: str


class DemoStatusResponse(BaseModel):
    """Response for demo status"""
    run_id: str
    project_id: str
    status: str
    run_type: str
    storm_events: List[str]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results_count: int
    results_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/setup", response_model=DemoProjectResponse)
async def setup_demo_project(db: Session = Depends(get_db)):
    """
    **Step 1: Setup Demo Project**

    Creates a demonstration project with sample drainage areas.

    This endpoint:
    - Creates a new project: "Acadian Village Parking Expansion - DEMO"
    - Populates 3 sample drainage areas with realistic data:
        - E-DA1: Mixed-use parking lot (0.574 acres, C=0.744)
        - E-DA2: Secondary parking (0.413 acres, C=0.625)
        - E-DA3: Building entrance (0.287 acres, C=0.680)
    - Each area includes land use breakdown and impervious/pervious calculations

    **Returns:**
    - project_id: UUID of created project
    - drainage_area_ids: List of created drainage area UUIDs
    - total_area_acres: Sum of all drainage areas
    """
    try:
        demo_service = DemoService(db)
        result = demo_service.create_demo_project()

        logger.info(f"Demo project created: {result['project_id']}")

        return DemoProjectResponse(**result)

    except Exception as e:
        logger.error(f"Error creating demo project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create demo project: {str(e)}")


@router.post("/run-dia", response_model=DemoRunResponse)
async def run_dia_demonstration(
    request: DemoRunRequest,
    db: Session = Depends(get_db)
):
    """
    **Step 2: Run DIA Generation**

    Executes the complete DIA workflow for the demo project.

    This endpoint:
    - Calculates Time of Concentration (Tc) for each drainage area
    - Queries NOAA Atlas 14 rainfall intensities
    - Calculates peak flow using Rational Method (Q = C × i × A)
    - Generates results for specified storm events (default: 10-year, 25-year)
    - Creates DIA report with exhibits

    **Process Flow:**
    ```
    For each storm event:
        For each drainage area:
            1. Calculate Tc using selected method (NRCS, Kirpich, FAA)
            2. Query rainfall intensity for Tc duration and return period
            3. Calculate Q = C × i × A
            4. Store results in database
    ```

    **Parameters:**
    - project_id: UUID of the demo project (from /setup)
    - storm_events: List of storm events (default: ["10-year", "25-year"])
    - tc_method: Calculation method (default: "nrcs")

    **Returns:**
    - run_id: UUID of the analysis run
    - results_summary: Complete breakdown of all calculations
    - report_paths: Paths to generated documents
    """
    try:
        demo_service = DemoService(db)
        result = demo_service.run_dia_demo(
            project_id=request.project_id,
            storm_events=request.storm_events,
            tc_method=request.tc_method
        )

        logger.info(f"Demo DIA run completed: {result['run_id']}")

        return DemoRunResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error in demo run: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error running demo DIA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run demo DIA: {str(e)}")


@router.get("/status/{run_id}", response_model=DemoStatusResponse)
async def get_demo_run_status(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    **Get Demo Run Status**

    Retrieves the status and results of a demo DIA run.

    **Parameters:**
    - run_id: UUID of the run (from /run-dia)

    **Returns:**
    - status: Run status (pending, processing, completed, failed)
    - results_count: Number of results generated
    - results_summary: Detailed breakdown of all calculations
    """
    try:
        demo_service = DemoService(db)
        result = demo_service.get_demo_status(run_id)

        return DemoStatusResponse(**result)

    except ValueError as e:
        logger.error(f"Demo run not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting demo status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get demo status: {str(e)}")


@router.get("/info")
async def get_demo_info():
    """
    **Demo Module Information**

    Returns information about the DEMO module and what it demonstrates.

    **What This Demo Shows:**
    1. **Complete DIA Workflow**: End-to-end drainage impact analysis
    2. **Realistic Data**: Sample project based on actual Lafayette, LA specifications
    3. **Multiple Drainage Areas**: 3 different land use scenarios
    4. **Storm Event Analysis**: Calculations for multiple return periods
    5. **Professional Output**: DIA reports and exhibits

    **Sample Data Included:**
    - Project: Acadian Village Parking Expansion
    - Total Area: 1.274 acres
    - Drainage Areas: 3 (E-DA1, E-DA2, E-DA3)
    - Land Uses: Pavement, Grass, Concrete, Gravel, Roof
    - Storm Events: 10-year, 25-year (configurable)

    **Calculations Performed:**
    - Time of Concentration (Tc) - NRCS, Kirpich, or FAA method
    - Rainfall Intensity - NOAA Atlas 14 for Lafayette, LA
    - Peak Flow - Rational Method (Q = C × i × A)

    **Time to Complete:**
    - Setup: < 1 second
    - DIA Generation: < 5 seconds
    - Total Demo: ~6 seconds

    **Comparison to Manual Process:**
    - Manual: 2-3 hours of calculations
    - Automated: 6 seconds
    - Time Saved: 99%+
    """
    return {
        "module": "DEMO",
        "title": "Drainage Impact Analysis - Complete Demonstration",
        "version": "1.0.0",
        "description": "One-click demonstration of the complete DIA workflow",
        "steps": [
            {
                "step": 1,
                "endpoint": "POST /api/v1/demo/setup",
                "action": "Create demo project with sample drainage areas",
                "time": "< 1 second"
            },
            {
                "step": 2,
                "endpoint": "POST /api/v1/demo/run-dia",
                "action": "Execute complete DIA workflow and generate reports",
                "time": "< 5 seconds"
            },
            {
                "step": 3,
                "endpoint": "GET /api/v1/demo/status/{run_id}",
                "action": "View results and download reports",
                "time": "< 0.1 seconds"
            }
        ],
        "sample_data": {
            "project": "Acadian Village Parking Expansion - DEMO",
            "location": "Lafayette, LA",
            "total_area_acres": 1.274,
            "drainage_areas": 3,
            "storm_events": ["10-year", "25-year"],
            "land_uses": [
                "Pavement (C=0.90)",
                "Grass - Flat (C=0.15)",
                "Grass - Average (C=0.25)",
                "Concrete Sidewalk (C=0.85)",
                "Gravel (C=0.20)",
                "Roof (C=0.85)"
            ]
        },
        "outputs": {
            "main_report": "DIA Report (DOCX)",
            "exhibits": "Technical Exhibits 3A-3D",
            "noaa_appendix": "NOAA Atlas 14 Rainfall Data",
            "database_records": "All calculations stored in database"
        },
        "time_savings": {
            "manual_process": "2-3 hours",
            "automated_process": "6 seconds",
            "efficiency_gain": "99%+"
        }
    }
