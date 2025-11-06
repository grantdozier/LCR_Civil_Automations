"""
Module E - Proposal & Document Automation API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import logging
import uuid

from core import get_db, settings
from models import Project, Run
from services.module_e import (
    ProposalGenerator,
    ProposalData,
    PricingCalculator,
    CoverLetterGenerator,
    SubmittalPackage,
    SubmittalDocument,
    TemplateManager,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class PricingRequest(BaseModel):
    """Request for pricing calculation"""
    modules: List[str] = Field(
        ...,
        description="List of module IDs (e.g., ['A', 'C', 'D'])"
    )
    discount_percent: float = Field(
        0,
        description="Custom discount percentage (0-100)",
        ge=0,
        le=100
    )
    rush_fee_percent: float = Field(
        0,
        description="Rush fee percentage (0-100)",
        ge=0,
        le=100
    )


class PricingResponse(BaseModel):
    """Response from pricing calculation"""
    subtotal: float
    bundle_discount_percent: float
    total_discount_percent: float
    discount_amount: float
    discounted_subtotal: float
    rush_fee_amount: float
    total: float
    estimated_days: int
    estimated_completion: str
    modules: List[Dict]


class ProposalRequest(BaseModel):
    """Request to generate proposal"""
    client_name: str = Field(..., description="Client organization name")
    client_contact: str = Field(..., description="Primary contact person")
    client_email: str = Field(..., description="Contact email")
    project_name: str = Field(..., description="Project name")
    project_location: str = Field(..., description="Project location")
    project_description: str = Field(..., description="Brief project description")
    modules_requested: List[str] = Field(..., description="Module IDs to include")
    custom_scope: List[str] = Field(default=[], description="Custom scope items")
    discount_percent: float = Field(0, ge=0, le=100)
    rush_fee_percent: float = Field(0, ge=0, le=100)
    proposal_valid_days: int = Field(30, description="Days proposal is valid")
    prepared_by: str = Field("Grant Dozier, PE")
    company: str = Field("LCR", description="LCR, Dozier, or Both")


class ProposalResponse(BaseModel):
    """Response from proposal generation"""
    proposal_id: str
    proposal_path: str
    total_price: float
    estimated_days: int
    modules_included: List[str]
    client_name: str


class SubmittalDocumentRequest(BaseModel):
    """Document in submittal package"""
    document_type: str
    description: str
    filename: str
    page_count: Optional[int] = None
    revision: Optional[str] = None


class CoverLetterRequest(BaseModel):
    """Request to generate cover letter"""
    project_name: str
    project_number: str
    client_name: str
    client_address: str
    client_contact: str
    subject: str
    documents: List[SubmittalDocumentRequest]
    purpose: str = "Plan Review"
    special_instructions: Optional[str] = None
    prepared_by: str = "Grant Dozier, PE"
    company: str = "LCR"
    letter_type: str = Field("submittal", description="submittal, transmittal, or response")


class CoverLetterResponse(BaseModel):
    """Response from cover letter generation"""
    letter_id: str
    letter_path: str
    project_name: str
    client_name: str
    document_count: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/calculate-pricing", response_model=PricingResponse)
async def calculate_proposal_pricing(request: PricingRequest):
    """
    Calculate pricing for automation module combination.

    **Standard Module Pricing:**
    - Module A: $7,500 - Automated Area Calculation Engine
    - Module B: $8,000 - UDC & DOTD Specification Extraction
    - Module C: $12,000 - DIA Report Generator
    - Module D: $9,500 - Plan Review & QA Automation
    - Module E: $5,000 - Proposal & Document Automation

    **Bundle Discounts:**
    - 3 modules: 5% discount
    - 4 modules: 10% discount
    - All 5 modules: 15% discount

    **Custom Discounts:**
    - Additional discounts can be applied for repeat clients or special circumstances

    **Rush Fees:**
    - Optional rush fee for expedited delivery

    **Example:**
    ```json
    {
      "modules": ["A", "C"],
      "discount_percent": 0,
      "rush_fee_percent": 0
    }
    ```

    **Result:**
    ```json
    {
      "subtotal": 19500.00,
      "total": 19500.00,
      "estimated_days": 25,
      "estimated_completion": "December 15, 2024"
    }
    ```
    """
    try:
        logger.info(f"Calculating pricing for modules: {request.modules}")

        calculator = PricingCalculator()
        result = calculator.calculate_total(
            modules=request.modules,
            discount_percent=Decimal(str(request.discount_percent)),
            rush_fee_percent=Decimal(str(request.rush_fee_percent))
        )

        # Convert module objects to dicts for response
        modules_dict = [
            {
                "module_id": m.module_id,
                "module_name": m.module_name,
                "description": m.description,
                "base_price": float(m.base_price),
                "time_estimate_days": m.time_estimate_days,
                "deliverables": m.deliverables,
            }
            for m in result["modules"]
        ]

        return PricingResponse(
            subtotal=result["subtotal"],
            bundle_discount_percent=result["bundle_discount_percent"],
            total_discount_percent=result["total_discount_percent"],
            discount_amount=result["discount_amount"],
            discounted_subtotal=result["discounted_subtotal"],
            rush_fee_amount=result["rush_fee_amount"],
            total=result["total"],
            estimated_days=result["estimated_days"],
            estimated_completion=result["estimated_completion"],
            modules=modules_dict,
        )

    except Exception as e:
        logger.error(f"Error calculating pricing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-proposal", response_model=ProposalResponse)
async def generate_proposal(
    request: ProposalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate professional branded proposal document.

    **Proposal Includes:**
    1. **Cover Page**: Company branding, project info, validity dates
    2. **Project Overview**: Description and about our services
    3. **Scope of Services**: Detailed module descriptions and deliverables
    4. **Pricing**: Itemized pricing with discounts and totals
    5. **Timeline**: Estimated duration and milestones
    6. **Terms & Conditions**: Standard terms for automation services
    7. **Signature Page**: Acceptance signatures

    **Output Format:**
    - Word (.docx) - Editable, professional formatting
    - Client-ready for immediate delivery

    **Use Cases:**
    - New client proposals
    - Project quotes
    - Service package offerings

    **Example:**
    ```json
    {
      "client_name": "Acadiana High School",
      "client_contact": "John Smith",
      "client_email": "john@school.edu",
      "project_name": "Campus Drainage Improvements",
      "project_location": "Lafayette, LA",
      "project_description": "Comprehensive drainage analysis and plan review",
      "modules_requested": ["A", "C", "D"],
      "company": "LCR"
    }
    ```
    """
    try:
        logger.info(f"Generating proposal for {request.client_name}")

        # Convert request to ProposalData
        proposal_data = ProposalData(
            client_name=request.client_name,
            client_contact=request.client_contact,
            client_email=request.client_email,
            project_name=request.project_name,
            project_location=request.project_location,
            project_description=request.project_description,
            modules_requested=request.modules_requested,
            custom_scope=request.custom_scope,
            discount_percent=Decimal(str(request.discount_percent)),
            rush_fee_percent=Decimal(str(request.rush_fee_percent)),
            proposal_valid_days=request.proposal_valid_days,
            prepared_by=request.prepared_by,
            company=request.company,
        )

        # Generate proposal
        generator = ProposalGenerator(output_dir=settings.OUTPUT_DIR)
        proposal_path = generator.generate_proposal(proposal_data)

        # Calculate pricing for response
        calculator = PricingCalculator()
        pricing = calculator.calculate_total(
            modules=request.modules_requested,
            discount_percent=Decimal(str(request.discount_percent)),
            rush_fee_percent=Decimal(str(request.rush_fee_percent))
        )

        # Create run record
        proposal_id = str(uuid.uuid4())
        run = Run(
            id=proposal_id,
            run_type="proposal_generation",
            status="completed",
            parameters={
                "client_name": request.client_name,
                "modules": request.modules_requested,
                "total_price": pricing["total"],
            },
            results_summary={
                "proposal_path": proposal_path,
                "total_price": pricing["total"],
                "estimated_days": pricing["estimated_days"],
            }
        )
        db.add(run)
        db.commit()

        logger.info(f"Generated proposal: {proposal_path}")

        return ProposalResponse(
            proposal_id=proposal_id,
            proposal_path=proposal_path,
            total_price=pricing["total"],
            estimated_days=pricing["estimated_days"],
            modules_included=request.modules_requested,
            client_name=request.client_name,
        )

    except Exception as e:
        logger.error(f"Error generating proposal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate professional cover letter for submittal package.

    **Letter Types:**
    - **submittal**: Plan submittal cover letter
    - **transmittal**: Document transmittal letter
    - **response**: Response to review comments

    **Letter Includes:**
    - Company letterhead with branding
    - Professional formatting
    - Document list table
    - Signature block
    - Contact information

    **Use Cases:**
    - Plan submittals to regulatory agencies
    - Document transmittals to clients
    - Review comment responses

    **Example:**
    ```json
    {
      "project_name": "Campus Drainage",
      "project_number": "2024-001",
      "client_name": "Lafayette Parish",
      "client_address": "123 Main St\\nLafayette, LA 70508",
      "client_contact": "Jane Doe",
      "subject": "Drainage Impact Analysis Submittal",
      "documents": [
        {
          "document_type": "DIA Report",
          "description": "Complete drainage analysis",
          "filename": "DIA_Report_2024-001.pdf",
          "page_count": 58
        }
      ],
      "letter_type": "submittal"
    }
    ```
    """
    try:
        logger.info(f"Generating {request.letter_type} cover letter for {request.project_name}")

        # Convert documents to SubmittalDocument objects
        documents = [
            SubmittalDocument(
                document_type=d.document_type,
                description=d.description,
                filename=d.filename,
                page_count=d.page_count,
                revision=d.revision,
            )
            for d in request.documents
        ]

        # Create SubmittalPackage
        submittal = SubmittalPackage(
            project_name=request.project_name,
            project_number=request.project_number,
            client_name=request.client_name,
            client_address=request.client_address,
            client_contact=request.client_contact,
            subject=request.subject,
            documents=documents,
            purpose=request.purpose,
            special_instructions=request.special_instructions,
            prepared_by=request.prepared_by,
            company=request.company,
        )

        # Generate cover letter
        generator = CoverLetterGenerator(output_dir=settings.OUTPUT_DIR)
        letter_path = generator.generate_cover_letter(
            submittal=submittal,
            letter_type=request.letter_type
        )

        # Create run record
        letter_id = str(uuid.uuid4())
        run = Run(
            id=letter_id,
            run_type="cover_letter_generation",
            status="completed",
            parameters={
                "project_name": request.project_name,
                "letter_type": request.letter_type,
                "document_count": len(documents),
            },
            results_summary={
                "letter_path": letter_path,
            }
        )
        db.add(run)
        db.commit()

        logger.info(f"Generated cover letter: {letter_path}")

        return CoverLetterResponse(
            letter_id=letter_id,
            letter_path=letter_path,
            project_name=request.project_name,
            client_name=request.client_name,
            document_count=len(documents),
        )

    except Exception as e:
        logger.error(f"Error generating cover letter: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-transmittal-form")
async def generate_transmittal_form(
    request: CoverLetterRequest,
    db: Session = Depends(get_db)
):
    """
    Generate formal document transmittal form.

    **Form Includes:**
    - Project information table
    - Document checklist
    - Transmittal action checkboxes
    - Remarks section
    - Signature block

    **Use For:**
    - Formal plan submittals
    - Multi-document packages
    - Agency submittals requiring transmittal forms
    """
    try:
        logger.info(f"Generating transmittal form for {request.project_name}")

        # Convert documents
        documents = [
            SubmittalDocument(
                document_type=d.document_type,
                description=d.description,
                filename=d.filename,
                page_count=d.page_count,
                revision=d.revision,
            )
            for d in request.documents
        ]

        # Create submittal package
        submittal = SubmittalPackage(
            project_name=request.project_name,
            project_number=request.project_number,
            client_name=request.client_name,
            client_address=request.client_address,
            client_contact=request.client_contact,
            subject=request.subject,
            documents=documents,
            purpose=request.purpose,
            special_instructions=request.special_instructions,
            prepared_by=request.prepared_by,
            company=request.company,
        )

        # Generate transmittal form
        generator = CoverLetterGenerator(output_dir=settings.OUTPUT_DIR)
        form_path = generator.generate_transmittal_form(submittal)

        logger.info(f"Generated transmittal form: {form_path}")

        return {
            "form_path": form_path,
            "project_name": request.project_name,
            "message": "Transmittal form generated successfully",
        }

    except Exception as e:
        logger.error(f"Error generating transmittal form: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/pricing")
async def get_module_pricing():
    """
    Get pricing information for all automation modules.

    Returns detailed information about each module including:
    - Module ID and name
    - Description
    - Base price
    - Estimated time
    - Deliverables list

    **Use For:**
    - Building custom pricing calculators
    - Displaying module options to clients
    - Creating custom proposals
    """
    try:
        calculator = PricingCalculator()

        modules = [
            {
                "module_id": m.module_id,
                "module_name": m.module_name,
                "description": m.description,
                "base_price": float(m.base_price),
                "time_estimate_days": m.time_estimate_days,
                "deliverables": m.deliverables,
            }
            for m in calculator.MODULE_PRICING.values()
        ]

        return {
            "modules": modules,
            "bundle_discounts": {
                "3_modules": "5%",
                "4_modules": "10%",
                "5_modules": "15%",
            },
            "total_modules": len(modules),
        }

    except Exception as e:
        logger.error(f"Error getting module pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/branding/{company}")
async def get_branding_info(company: str):
    """
    Get branding information for specified company.

    Args:
        company: "LCR", "Dozier", or "Both"

    Returns:
        Branding assets including colors, contact info, etc.
    """
    try:
        template_manager = TemplateManager()
        branding = template_manager.get_branding(company)

        return {
            "company_name": branding.company_name,
            "tagline": branding.tagline,
            "address": branding.address,
            "phone": branding.phone,
            "email": branding.email,
            "website": branding.website,
            "primary_color": branding.primary_color,
            "secondary_color": branding.secondary_color,
        }

    except Exception as e:
        logger.error(f"Error getting branding info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
