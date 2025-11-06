"""
Module B - Specification Extraction API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path
import tempfile
import logging

from core import get_db, settings
from models import Spec
from services.module_b import (
    PDFParser,
    SpecificationExtractor,
    NOAAAtlas14Parser,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class SpecResponse(BaseModel):
    """Specification response"""
    id: Optional[str] = None
    jurisdiction: str
    document_name: str
    spec_type: str
    land_use_type: Optional[str] = None
    c_value_recommended: Optional[float] = None
    duration_minutes: Optional[float] = None
    return_period_years: Optional[int] = None
    intensity_in_per_hr: Optional[float] = None
    extraction_confidence: Optional[float] = None
    verified: bool = False


class PDFUploadResponse(BaseModel):
    """PDF upload and extraction response"""
    filename: str
    total_pages: int
    specifications_extracted: int
    specifications: List[Dict]


class RainfallIntensityQuery(BaseModel):
    """Query for rainfall intensity"""
    duration_minutes: float = Field(..., description="Duration in minutes")
    return_period_years: int = Field(..., description="Return period in years (10, 25, 50, 100)")
    jurisdiction: Optional[str] = Field("NOAA Atlas 14", description="Data source jurisdiction")


class RainfallIntensityResponse(BaseModel):
    """Rainfall intensity response"""
    duration_minutes: float
    return_period_years: int
    intensity_in_per_hr: float
    source: str
    interpolated: bool = False


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/extract-from-pdf", response_model=PDFUploadResponse)
async def extract_specifications_from_pdf(
    file: UploadFile = File(...),
    jurisdiction: str = Query("Unknown", description="Jurisdiction name (e.g., Lafayette UDC, DOTD)"),
    document_name: Optional[str] = Query(None, description="Document name (defaults to filename)"),
    use_langchain: bool = Query(False, description="Use LangChain for AI-powered extraction"),
    db: Session = Depends(get_db)
):
    """
    Extract regulatory specifications from uploaded PDF document.

    This endpoint:
    1. Accepts PDF upload (UDC, DOTD, or other regulatory manual)
    2. Parses PDF to extract text and tables
    3. Identifies and extracts:
       - Runoff coefficients (C-values)
       - Rainfall intensity tables
       - Tc limits
       - Detention requirements
    4. Saves specifications to database
    5. Returns extracted specifications

    **Supported document types:**
    - Lafayette Unified Development Code (UDC)
    - DOTD Hydraulic Design Manual
    - NOAA Atlas 14 rainfall data
    - Other drainage-related regulatory documents
    """
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        doc_name = document_name or file.filename

        # Parse PDF
        openai_key = settings.OPENAI_API_KEY if use_langchain else None
        parser = PDFParser(tmp_path, use_langchain=use_langchain, openai_api_key=openai_key)
        parser.extract_text()

        metadata = parser.get_metadata()
        total_pages = metadata.get("total_pages", len(parser.pages))

        # Extract specifications
        extractor = SpecificationExtractor(parser)
        raw_specs = extractor.extract_all(
            jurisdiction=jurisdiction,
            document_name=doc_name
        )

        # Convert to database format
        db_specs = extractor.to_database_format(raw_specs)

        # Save to database
        saved_count = 0
        for spec_data in db_specs:
            spec = Spec(**spec_data)
            db.add(spec)
            saved_count += 1

        db.commit()

        # Clean up temp file
        Path(tmp_path).unlink()

        logger.info(
            f"Extracted {len(raw_specs)} specifications from {file.filename} "
            f"({total_pages} pages, jurisdiction: {jurisdiction})"
        )

        return PDFUploadResponse(
            filename=file.filename,
            total_pages=total_pages,
            specifications_extracted=len(raw_specs),
            specifications=raw_specs,
        )

    except Exception as e:
        logger.error(f"Error extracting specifications from PDF: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=List[SpecResponse])
async def search_specifications(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    spec_type: Optional[str] = Query(None, description="Filter by spec type (runoff_coefficient, rainfall_intensity, etc.)"),
    land_use: Optional[str] = Query(None, description="Filter by land use type"),
    verified_only: bool = Query(False, description="Return only verified specs"),
    db: Session = Depends(get_db)
):
    """
    Search regulatory specifications database.

    **Filter options:**
    - jurisdiction: e.g., "Lafayette UDC", "DOTD", "NOAA Atlas 14"
    - spec_type: e.g., "runoff_coefficient", "rainfall_intensity"
    - land_use: e.g., "pavement", "grass", "roof"
    - verified_only: Return only manually verified specifications

    **Returns:**
    - List of matching specifications
    """
    try:
        query = db.query(Spec)

        # Apply filters
        if jurisdiction:
            query = query.filter(Spec.jurisdiction.ilike(f"%{jurisdiction}%"))

        if spec_type:
            query = query.filter(Spec.spec_type == spec_type)

        if land_use:
            query = query.filter(Spec.land_use_type.ilike(f"%{land_use}%"))

        if verified_only:
            query = query.filter(Spec.verified == True)

        # Execute query
        results = query.all()

        logger.info(f"Found {len(results)} specifications matching filters")

        return [
            SpecResponse(
                id=str(result.id),
                jurisdiction=result.jurisdiction,
                document_name=result.document_name,
                spec_type=result.spec_type,
                land_use_type=result.land_use_type,
                c_value_recommended=float(result.c_value_recommended) if result.c_value_recommended else None,
                duration_minutes=float(result.duration_minutes) if result.duration_minutes else None,
                return_period_years=result.return_period_years,
                intensity_in_per_hr=float(result.intensity_in_per_hr) if result.intensity_in_per_hr else None,
                extraction_confidence=float(result.extraction_confidence) if result.extraction_confidence else None,
                verified=result.verified or False,
            )
            for result in results
        ]

    except Exception as e:
        logger.error(f"Error searching specifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rainfall-intensity", response_model=RainfallIntensityResponse)
async def get_rainfall_intensity(
    query: RainfallIntensityQuery,
    db: Session = Depends(get_db)
):
    """
    Get rainfall intensity for specified duration and return period.

    Uses NOAA Atlas 14 data for Lafayette, LA by default.

    **Parameters:**
    - duration_minutes: Storm duration in minutes (e.g., 5, 10, 15, 30, 60)
    - return_period_years: Return period (10, 25, 50, 100)
    - jurisdiction: Data source (default: "NOAA Atlas 14")

    **Returns:**
    - Rainfall intensity in inches per hour
    - Will interpolate if exact duration not found

    **Example:**
    ```json
    {
      "duration_minutes": 12.5,
      "return_period_years": 10,
      "jurisdiction": "NOAA Atlas 14"
    }
    ```
    """
    try:
        # Try to get from database first
        result = (
            db.query(Spec)
            .filter(
                Spec.spec_type == "rainfall_intensity",
                Spec.duration_minutes == query.duration_minutes,
                Spec.return_period_years == query.return_period_years,
                Spec.jurisdiction.ilike(f"%{query.jurisdiction}%")
            )
            .first()
        )

        if result:
            logger.info(
                f"Found exact rainfall intensity: {query.duration_minutes} min, "
                f"{query.return_period_years} yr = {result.intensity_in_per_hr} in/hr"
            )
            return RainfallIntensityResponse(
                duration_minutes=float(result.duration_minutes),
                return_period_years=result.return_period_years,
                intensity_in_per_hr=float(result.intensity_in_per_hr),
                source=result.jurisdiction,
                interpolated=False,
            )

        # If not found, try interpolation using NOAA parser
        noaa = NOAAAtlas14Parser()
        noaa.load_standard_lafayette_data()

        interpolated_intensity = noaa.interpolate_intensity(
            query.duration_minutes,
            query.return_period_years
        )

        if interpolated_intensity is None:
            raise HTTPException(
                status_code=404,
                detail=f"Rainfall intensity not found for duration={query.duration_minutes} min, "
                       f"return period={query.return_period_years} years"
            )

        logger.info(
            f"Interpolated rainfall intensity: {query.duration_minutes} min, "
            f"{query.return_period_years} yr = {interpolated_intensity} in/hr"
        )

        return RainfallIntensityResponse(
            duration_minutes=query.duration_minutes,
            return_period_years=query.return_period_years,
            intensity_in_per_hr=interpolated_intensity,
            source="NOAA Atlas 14 (Lafayette, LA)",
            interpolated=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rainfall intensity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-noaa-data")
async def load_noaa_atlas_data(db: Session = Depends(get_db)):
    """
    Load standard NOAA Atlas 14 rainfall data for Lafayette, LA into database.

    This endpoint loads hardcoded NOAA Atlas 14 Volume 9 data for Lafayette, LA
    (approximately 30.2° N, 92.0° W).

    **Data includes:**
    - Durations: 5, 10, 15, 30, 60 minutes
    - Return periods: 10, 25, 50, 100 years
    - Rainfall intensities in inches per hour

    **Returns:**
    - Number of records loaded
    """
    try:
        noaa = NOAAAtlas14Parser()
        noaa.load_standard_lafayette_data()

        specs = noaa.export_to_database_format()

        # Check if data already exists
        existing = db.query(Spec).filter(
            Spec.jurisdiction == "NOAA Atlas 14",
            Spec.spec_type == "rainfall_intensity"
        ).count()

        if existing > 0:
            logger.info(f"NOAA Atlas 14 data already loaded ({existing} records)")
            return {
                "message": "NOAA Atlas 14 data already exists in database",
                "existing_records": existing,
                "action": "skipped"
            }

        # Insert into database
        for spec_data in specs:
            spec = Spec(**spec_data)
            db.add(spec)

        db.commit()

        logger.info(f"Loaded {len(specs)} NOAA Atlas 14 records")

        return {
            "message": "NOAA Atlas 14 data loaded successfully",
            "records_loaded": len(specs),
            "action": "inserted"
        }

    except Exception as e:
        logger.error(f"Error loading NOAA data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/c-values")
async def get_c_values(
    land_use: Optional[str] = Query(None, description="Filter by land use type"),
    jurisdiction: str = Query("Lafayette UDC", description="Jurisdiction"),
    db: Session = Depends(get_db)
):
    """
    Get runoff coefficients (C-values) from database.

    **Parameters:**
    - land_use: Land use type (e.g., "pavement", "grass", "roof")
    - jurisdiction: Jurisdiction name (default: "Lafayette UDC")

    **Returns:**
    - List of C-values with land use descriptions
    """
    try:
        query = db.query(Spec).filter(
            Spec.spec_type == "runoff_coefficient",
            Spec.jurisdiction.ilike(f"%{jurisdiction}%")
        )

        if land_use:
            query = query.filter(Spec.land_use_type.ilike(f"%{land_use}%"))

        results = query.all()

        return {
            "jurisdiction": jurisdiction,
            "total_results": len(results),
            "c_values": [
                {
                    "land_use_type": r.land_use_type,
                    "c_value_min": float(r.c_value_min) if r.c_value_min else None,
                    "c_value_max": float(r.c_value_max) if r.c_value_max else None,
                    "c_value_recommended": float(r.c_value_recommended) if r.c_value_recommended else None,
                }
                for r in results
            ],
        }

    except Exception as e:
        logger.error(f"Error getting C-values: {e}")
        raise HTTPException(status_code=500, detail=str(e))
