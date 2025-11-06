"""
Module A - Area Calculation API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import logging

from core import get_db, settings
from models import Project, Drawing, DrainageArea
from services.module_a import (
    SurveyCSVParser,
    AreaCalculator,
    WeightedCValueCalculator,
    TOCExcelUpdater,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================


class PolygonCoordinates(BaseModel):
    """Polygon coordinates for area calculation"""
    coordinates: List[List[float]] = Field(..., description="List of [x, y] coordinates")


class LandUseArea(BaseModel):
    """Land use type and area"""
    land_use: str = Field(..., description="Land use type (e.g., 'pavement', 'grass_flat', 'roof')")
    area: float = Field(..., description="Area in square feet or percentage")


class AreaCalculationRequest(BaseModel):
    """Request to calculate drainage area"""
    project_id: str = Field(..., description="Project UUID")
    drawing_id: Optional[str] = Field(None, description="Drawing UUID (optional)")
    area_label: str = Field(..., description="Drainage area label (e.g., 'E-DA1')")
    total_polygon: PolygonCoordinates
    impervious_polygons: Optional[List[PolygonCoordinates]] = None
    land_use_breakdown: List[LandUseArea] = Field(..., description="Land use breakdown for C-value calculation")


class AreaCalculationResponse(BaseModel):
    """Response with calculated area and C-value"""
    area_label: str
    total_area_sqft: float
    total_area_acres: float
    impervious_area_sqft: float
    impervious_area_acres: float
    pervious_area_sqft: float
    pervious_area_acres: float
    impervious_percentage: float
    weighted_c_value: float
    c_value_breakdown: Dict
    centroid_x: float
    centroid_y: float


class WeightedCRequest(BaseModel):
    """Request to calculate weighted C-value"""
    land_use_areas: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping land use to area",
        example={"pavement": 100000, "grass_flat": 50000, "roof": 25000}
    )


class WeightedCResponse(BaseModel):
    """Response with weighted C-value"""
    weighted_c_value: float
    total_area: float
    breakdown: Dict


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/calculate", response_model=AreaCalculationResponse)
async def calculate_drainage_area(
    request: AreaCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate drainage area, impervious/pervious split, and weighted C-value.

    This endpoint:
    1. Calculates total drainage area from polygon coordinates
    2. Calculates impervious vs pervious areas
    3. Computes weighted runoff coefficient (C-value)
    4. Saves results to database
    5. Returns complete calculation summary

    **Accuracy:**
    - Area calculations: ±0.5%
    - Weighted C-values: Exact to 3 decimal places
    """
    try:
        # Initialize calculators
        area_calc = AreaCalculator(precision=settings.AREA_CALCULATION_PRECISION)
        c_calc = WeightedCValueCalculator()

        # Calculate areas
        impervious_coords = [poly.coordinates for poly in request.impervious_polygons] if request.impervious_polygons else None

        area_result = area_calc.calculate_split_areas(
            total_polygon=request.total_polygon.coordinates,
            impervious_polygons=impervious_coords
        )

        # Calculate weighted C-value
        land_use_dict = {item.land_use: item.area for item in request.land_use_breakdown}
        c_result = c_calc.calculate_weighted_c(land_use_dict)

        # Get centroid
        centroid = area_calc.calculate_polygon_area(request.total_polygon.coordinates)

        # Save to database
        drainage_area = DrainageArea(
            project_id=request.project_id,
            drawing_id=request.drawing_id,
            area_label=request.area_label,
            total_area_sqft=area_result["total_area_sqft"],
            total_area_acres=area_result["total_area_acres"],
            impervious_area_sqft=area_result["impervious_area_sqft"],
            impervious_area_acres=area_result["impervious_area_acres"],
            pervious_area_sqft=area_result["pervious_area_sqft"],
            pervious_area_acres=area_result["pervious_area_acres"],
            weighted_c_value=c_result["weighted_c_value"],
            land_use_breakdown=land_use_dict,
        )

        db.add(drainage_area)
        db.commit()
        db.refresh(drainage_area)

        logger.info(f"Calculated drainage area {request.area_label}: {area_result['total_area_acres']} ac, C={c_result['weighted_c_value']}")

        return AreaCalculationResponse(
            area_label=request.area_label,
            total_area_sqft=area_result["total_area_sqft"],
            total_area_acres=area_result["total_area_acres"],
            impervious_area_sqft=area_result["impervious_area_sqft"],
            impervious_area_acres=area_result["impervious_area_acres"],
            pervious_area_sqft=area_result["pervious_area_sqft"],
            pervious_area_acres=area_result["pervious_area_acres"],
            impervious_percentage=area_result["impervious_percentage"],
            weighted_c_value=c_result["weighted_c_value"],
            c_value_breakdown=c_result["breakdown"],
            centroid_x=centroid["centroid_x"],
            centroid_y=centroid["centroid_y"],
        )

    except Exception as e:
        logger.error(f"Error calculating drainage area: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/weighted-c", response_model=WeightedCResponse)
async def calculate_weighted_c(request: WeightedCRequest):
    """
    Calculate weighted runoff coefficient (C-value) from land use breakdown.

    Formula: C_weighted = (C1×A1 + C2×A2 + ... + Cn×An) / A_total

    **Accuracy:** Exact to 3 decimal places

    Available land use types:
    - pavement, concrete, asphalt (C = 0.90)
    - roof, sidewalk (C = 0.85)
    - grass_flat (C = 0.10), grass_moderate (C = 0.15), grass_steep (C = 0.20)
    - gravel (C = 0.50), dirt (C = 0.30)
    """
    try:
        c_calc = WeightedCValueCalculator()
        result = c_calc.calculate_weighted_c(request.land_use_areas)

        logger.info(f"Calculated weighted C-value: {result['weighted_c_value']}")

        return WeightedCResponse(
            weighted_c_value=result["weighted_c_value"],
            total_area=result["total_area"],
            breakdown=result["breakdown"],
        )

    except Exception as e:
        logger.error(f"Error calculating weighted C-value: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/parse-survey-csv")
async def parse_survey_csv(
    file: UploadFile = File(...),
    export_geojson: bool = False
):
    """
    Parse survey CSV file and extract point data.

    Accepts CSV files exported from Civil 3D or survey equipment.

    **Required columns:**
    - Point Name
    - Northing
    - Easting
    - Elevation
    - Point Code (optional)

    **Returns:**
    - Survey point statistics
    - Point data (first 100 points)
    - Optional: GeoJSON export
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Parse CSV
        parser = SurveyCSVParser(tmp_path)
        points = parser.parse()
        stats = parser.get_statistics()

        response = {
            "filename": file.filename,
            "total_points": len(points),
            "statistics": stats,
            "points_preview": [
                {
                    "name": p.point_name,
                    "northing": p.northing,
                    "easting": p.easting,
                    "elevation": p.elevation,
                    "code": p.point_code,
                }
                for p in points[:100]  # Return first 100 points
            ],
        }

        # Optional: Export to GeoJSON
        if export_geojson:
            geojson_path = Path(settings.OUTPUT_DIR) / f"{Path(file.filename).stem}.geojson"
            geojson_path.parent.mkdir(parents=True, exist_ok=True)
            parser.export_to_geojson(str(geojson_path))
            response["geojson_path"] = str(geojson_path)

        # Clean up temp file
        Path(tmp_path).unlink()

        logger.info(f"Parsed survey CSV: {file.filename} ({len(points)} points)")

        return response

    except Exception as e:
        logger.error(f"Error parsing survey CSV: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/project/{project_id}/drainage-areas")
async def get_project_drainage_areas(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all drainage areas for a project.

    Returns:
    - List of drainage areas with areas and C-values
    """
    try:
        drainage_areas = (
            db.query(DrainageArea)
            .filter(DrainageArea.project_id == project_id)
            .all()
        )

        return {
            "project_id": project_id,
            "total_areas": len(drainage_areas),
            "drainage_areas": [
                {
                    "id": str(da.id),
                    "area_label": da.area_label,
                    "total_area_acres": float(da.total_area_acres) if da.total_area_acres else 0,
                    "impervious_area_acres": float(da.impervious_area_acres) if da.impervious_area_acres else 0,
                    "pervious_area_acres": float(da.pervious_area_acres) if da.pervious_area_acres else 0,
                    "weighted_c_value": float(da.weighted_c_value) if da.weighted_c_value else 0,
                    "land_use_breakdown": da.land_use_breakdown,
                }
                for da in drainage_areas
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching drainage areas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-excel-toc")
async def update_excel_toc(
    template_file: UploadFile = File(...),
    drainage_areas_json: str = "",
):
    """
    Update Excel TOC (Time of Concentration) workbook with drainage area data.

    **Upload:**
    - template_file: Existing Excel workbook or use new blank workbook
    - drainage_areas_json: JSON string with drainage area data

    **Returns:**
    - Path to updated Excel file
    """
    try:
        import json

        # Parse drainage areas
        drainage_areas = json.loads(drainage_areas_json) if drainage_areas_json else []

        # Save uploaded template
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            content = await template_file.read()
            tmp_file.write(content)
            template_path = tmp_file.name

        # Update Excel
        updater = TOCExcelUpdater()
        updater.load_template(template_path)
        updater.update_drainage_area_data("Drainage Areas", drainage_areas)

        # Save output
        output_path = Path(settings.OUTPUT_DIR) / f"TOC_{Path(template_file.filename).stem}_updated.xlsx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        updater.save(str(output_path))

        # Clean up temp file
        Path(template_path).unlink()

        logger.info(f"Updated Excel TOC workbook: {output_path}")

        return {
            "success": True,
            "output_path": str(output_path),
            "areas_updated": len(drainage_areas),
        }

    except Exception as e:
        logger.error(f"Error updating Excel TOC: {e}")
        raise HTTPException(status_code=400, detail=str(e))
