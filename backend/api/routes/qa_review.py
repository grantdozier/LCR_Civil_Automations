"""
Module D - Plan Review & QA Automation API Endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import logging
import uuid
import shutil

from core import get_db, settings
from models import Project, Run
from services.module_d import (
    PlanExtractor,
    SheetMetadata,
    ComplianceChecker,
    ComplianceResult,
    QAReportGenerator,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class SheetMetadataResponse(BaseModel):
    """Response model for sheet metadata"""
    sheet_number: str
    sheet_title: str
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    date: Optional[str] = None
    scale: Optional[str] = None
    notes_text: str
    confidence_score: float
    errors: List[str] = []


class ExtractRequest(BaseModel):
    """Request to extract sheets from PDF"""
    pdf_path: str = Field(..., description="Path to PDF plan set")
    sheet_numbers: Optional[List[str]] = Field(
        None,
        description="Specific sheets to extract (e.g., ['C-7', 'C-9'])"
    )
    use_ocr: bool = Field(True, description="Whether to use OCR")


class ExtractResponse(BaseModel):
    """Response from sheet extraction"""
    sheets_found: int
    sheets: List[SheetMetadataResponse]
    extraction_time: float


class ComplianceCheckRequest(BaseModel):
    """Request for compliance check"""
    project_id: Optional[str] = Field(None, description="Optional project ID")
    pdf_path: str = Field(..., description="Path to PDF plan set")
    sheet_numbers: Optional[List[str]] = Field(None, description="Specific sheets to check")
    custom_rules: Optional[List[Dict]] = Field(None, description="Custom validation rules")


class ComplianceResultResponse(BaseModel):
    """Response model for single compliance result"""
    rule_id: str
    passed: bool
    sheet_number: str
    message: str
    severity: str
    found_text: Optional[str] = None
    suggestions: List[str] = []


class ComplianceSummaryResponse(BaseModel):
    """Response model for compliance summary"""
    total_checks: int
    passed: int
    failed: int
    pass_rate: float
    critical_failures: int
    warnings: int
    info: int
    overall_status: str
    by_category: Dict[str, Dict[str, int]]


class ComplianceCheckResponse(BaseModel):
    """Response from compliance check"""
    run_id: str
    project_id: Optional[str] = None
    sheets_checked: int
    summary: ComplianceSummaryResponse
    results: List[ComplianceResultResponse]
    report_path: Optional[str] = None


class QAReportRequest(BaseModel):
    """Request to generate QA report"""
    project_id: Optional[str] = Field(None, description="Project UUID")
    pdf_path: str = Field(..., description="Path to PDF plan set")
    include_detailed_results: bool = Field(True, description="Include detailed compliance results")
    output_format: str = Field("docx", description="Output format: docx or pdf")


class QAReportResponse(BaseModel):
    """Response from QA report generation"""
    run_id: str
    project_id: Optional[str] = None
    report_path: str
    sheets_reviewed: int
    compliance_status: str
    critical_failures: int
    total_checks: int
    pass_rate: float


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/extract-sheets", response_model=ExtractResponse)
async def extract_sheets_from_pdf(request: ExtractRequest):
    """
    Extract plan sheet metadata from PDF using OCR.

    **Functionality:**
    - Extracts text and metadata from civil plan sheets
    - Identifies sheet numbers (C-1, C-2, etc.) and titles
    - Extracts notes sections for compliance checking
    - Returns confidence scores for OCR quality

    **Supported Sheet Types:**
    - C-1: Cover Sheet / Sheet Index
    - C-2: General Notes
    - C-3: Existing Conditions
    - C-7: Drainage Plan
    - C-9: Erosion Control Plan
    - And more (C-1 through C-18)

    **Example:**
    ```json
    {
      "pdf_path": "/app/uploads/project_plans.pdf",
      "sheet_numbers": ["C-7", "C-9"],
      "use_ocr": true
    }
    ```
    """
    try:
        logger.info(f"Extracting sheets from: {request.pdf_path}")
        start_time = datetime.now()

        extractor = PlanExtractor(use_ocr=request.use_ocr)
        sheets = extractor.extract_from_pdf(
            pdf_path=request.pdf_path,
            sheet_numbers=request.sheet_numbers
        )

        extraction_time = (datetime.now() - start_time).total_seconds()

        # Convert to response model
        sheet_responses = [
            SheetMetadataResponse(
                sheet_number=s.sheet_number,
                sheet_title=s.sheet_title,
                project_name=s.project_name,
                project_number=s.project_number,
                date=s.date,
                scale=s.scale,
                notes_text=s.notes_text,
                confidence_score=s.confidence_score,
                errors=s.errors,
            )
            for s in sheets
        ]

        logger.info(f"Extracted {len(sheets)} sheets in {extraction_time:.2f}s")

        return ExtractResponse(
            sheets_found=len(sheets),
            sheets=sheet_responses,
            extraction_time=extraction_time,
        )

    except FileNotFoundError as e:
        logger.error(f"PDF not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting sheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-compliance", response_model=ComplianceCheckResponse)
async def check_plan_compliance(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check plan sheets for compliance with 25+ standard requirements.

    **Checks Include:**
    - **LPDES**: Louisiana Pollutant Discharge requirements
    - **LUS**: Lafayette Utilities coordination
    - **DOTD**: State transportation/drainage standards
    - **ASTM**: Materials testing specifications
    - **Erosion Control**: SWPPP, BMP requirements
    - **Drainage Design**: NOAA Atlas 14, Rational Method, UDC
    - **And 19+ more requirements**

    **Returns:**
    - Summary: Pass/fail status, counts by severity
    - Detailed results: Each rule checked with pass/fail
    - Suggestions: How to fix failed requirements

    **Example:**
    ```json
    {
      "project_id": "123e4567-e89b-12d3-a456-426614174000",
      "pdf_path": "/app/uploads/plans.pdf",
      "sheet_numbers": ["C-2", "C-7", "C-9"]
    }
    ```
    """
    try:
        logger.info(f"Checking compliance for: {request.pdf_path}")

        # Extract sheets
        extractor = PlanExtractor(use_ocr=True)
        sheets = extractor.extract_from_pdf(
            pdf_path=request.pdf_path,
            sheet_numbers=request.sheet_numbers
        )

        if not sheets:
            raise HTTPException(
                status_code=400,
                detail="No sheets found in PDF. Check file path and sheet numbers."
            )

        # Run compliance checks
        checker = ComplianceChecker()
        results = checker.check_compliance(sheets)

        # Generate summary
        summary_dict = checker.generate_summary(results)

        # Create run record if project_id provided
        run_id = str(uuid.uuid4())
        if request.project_id:
            run = Run(
                id=run_id,
                project_id=request.project_id,
                run_type="qa_review",
                status="completed",
                parameters={
                    "pdf_path": request.pdf_path,
                    "sheet_numbers": request.sheet_numbers,
                },
                results_summary={
                    "sheets_checked": len(sheets),
                    "compliance_summary": summary_dict,
                }
            )
            db.add(run)
            db.commit()

        # Convert to response models
        result_responses = [
            ComplianceResultResponse(
                rule_id=r.rule_id,
                passed=r.passed,
                sheet_number=r.sheet_number,
                message=r.message,
                severity=r.severity.value,
                found_text=r.found_text,
                suggestions=r.suggestions,
            )
            for r in results
        ]

        summary_response = ComplianceSummaryResponse(**summary_dict)

        logger.info(
            f"Compliance check complete: {summary_dict['passed']}/{summary_dict['total_checks']} passed"
        )

        return ComplianceCheckResponse(
            run_id=run_id,
            project_id=request.project_id,
            sheets_checked=len(sheets),
            summary=summary_response,
            results=result_responses,
            report_path=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking compliance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-qa-report", response_model=QAReportResponse)
async def generate_qa_report(
    request: QAReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate complete Quality Assurance (QA) report for plan review.

    **Report Includes:**
    1. **Cover Page**: Professional cover with project details
    2. **Executive Summary**: Overall pass/fail status, statistics
    3. **Detailed Results**: All compliance checks by category
    4. **Sheet-by-Sheet Review**: Individual sheet analysis
    5. **Recommendations**: Prioritized list of corrections needed
    6. **Appendix**: Reference guide for all requirements

    **Output Formats:**
    - Word (.docx) - Editable, client-ready
    - PDF (.pdf) - Final, non-editable [coming soon]

    **Use Case:**
    Upload plan set → Run compliance check → Generate professional QA report
    → Send to client or use for internal review

    **Processing Time:**
    - Typical: 10-30 seconds for complete analysis + report

    **Example:**
    ```json
    {
      "project_id": "123e4567-e89b-12d3-a456-426614174000",
      "pdf_path": "/app/uploads/acadiana_high_plans.pdf",
      "include_detailed_results": true,
      "output_format": "docx"
    }
    ```
    """
    try:
        logger.info(f"Generating QA report for: {request.pdf_path}")

        # Get project data if project_id provided
        project_data = {}
        if request.project_id:
            project = db.query(Project).filter(Project.id == request.project_id).first()
            if project:
                project_data = {
                    "project_name": project.name,
                    "project_number": project.project_number or "N/A",
                    "client_name": project.client_name or "Client",
                    "location": project.location or "Lafayette, LA",
                }
            else:
                logger.warning(f"Project not found: {request.project_id}")

        # Default project data if not found
        if not project_data:
            project_data = {
                "project_name": "Plan Review Project",
                "project_number": datetime.now().strftime("%Y-%m-%d"),
                "client_name": "Client",
                "location": "Lafayette, LA",
            }

        # Extract sheets
        extractor = PlanExtractor(use_ocr=True)
        sheets = extractor.extract_from_pdf(pdf_path=request.pdf_path)

        if not sheets:
            raise HTTPException(
                status_code=400,
                detail="No sheets found in PDF"
            )

        # Run compliance checks
        checker = ComplianceChecker()
        compliance_results = checker.check_compliance(sheets)
        summary = checker.generate_summary(compliance_results)

        # Generate report
        report_gen = QAReportGenerator(output_dir=settings.OUTPUT_DIR)

        if request.output_format.lower() == "pdf":
            # PDF generation not yet implemented
            raise HTTPException(
                status_code=501,
                detail="PDF output format not yet implemented. Use 'docx' format."
            )

        report_path = report_gen.generate_report(
            project_data=project_data,
            sheets=sheets,
            compliance_results=compliance_results,
        )

        # Create run record
        run_id = str(uuid.uuid4())
        run = Run(
            id=run_id,
            project_id=request.project_id,
            run_type="qa_report",
            status="completed",
            parameters={
                "pdf_path": request.pdf_path,
                "output_format": request.output_format,
            },
            results_summary={
                "sheets_reviewed": len(sheets),
                "compliance_status": summary["overall_status"],
                "critical_failures": summary["critical_failures"],
                "total_checks": summary["total_checks"],
                "pass_rate": summary["pass_rate"],
                "report_path": report_path,
            }
        )
        db.add(run)
        db.commit()

        logger.info(f"QA report generated: {report_path}")

        return QAReportResponse(
            run_id=run_id,
            project_id=request.project_id,
            report_path=report_path,
            sheets_reviewed=len(sheets),
            compliance_status=summary["overall_status"],
            critical_failures=summary["critical_failures"],
            total_checks=summary["total_checks"],
            pass_rate=summary["pass_rate"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QA report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-plan-set")
async def upload_plan_set(
    file: UploadFile = File(...),
    project_id: Optional[str] = None
):
    """
    Upload PDF plan set for review.

    **Accepts:**
    - PDF files up to 50MB
    - Multi-page plan sets

    **Returns:**
    - File path for use in other endpoints
    - File size and page count

    **Example Usage:**
    1. Upload plan set → Get file path
    2. Use file path in /check-compliance or /generate-qa-report
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # Create upload directory
        upload_dir = Path(settings.OUTPUT_DIR) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"planset_{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename

        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size

        logger.info(f"Uploaded plan set: {file_path} ({file_size} bytes)")

        return {
            "filename": safe_filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "project_id": project_id,
            "message": "File uploaded successfully. Use file_path in compliance check.",
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/results")
async def get_qa_run_results(run_id: str, db: Session = Depends(get_db)):
    """
    Get results from a completed QA review run.

    Returns:
    - Run metadata
    - Compliance summary
    - Report file path
    """
    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

        return {
            "run_id": str(run.id),
            "project_id": str(run.project_id) if run.project_id else None,
            "run_type": run.run_type,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "parameters": run.parameters,
            "results_summary": run.results_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
