"""
Module E - Proposal & Document Automation API Endpoints
Generates proposals for LCR & Company's civil engineering services
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
    """Request for civil engineering services pricing calculation"""
    services: List[str] = Field(
        ...,
        description="List of service IDs (e.g., ['DIA', 'GRADING', 'REVIEW'])"
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
    """Response from civil engineering services pricing calculation"""
    subtotal: float
    package_discount_percent: float
    total_discount_percent: float
    discount_amount: float
    discounted_subtotal: float
    rush_fee_amount: float
    total: float
    estimated_days: int
    estimated_completion: str
    services: List[Dict]


class ProposalRequest(BaseModel):
    """Request to generate civil engineering services proposal"""
    client_name: str = Field(..., description="Client organization name")
    client_contact: str = Field(..., description="Primary contact person")
    client_email: str = Field(..., description="Contact email")
    project_name: str = Field(..., description="Project name")
    project_location: str = Field(..., description="Project location")
    project_description: str = Field(..., description="Brief project description")
    jurisdiction: str = Field("Lafayette UDC", description="Regulatory jurisdiction")
    project_type: str = Field("Commercial", description="Project type")
    services_requested: List[str] = Field(..., description="Service IDs to include")
    project_area_acres: Optional[float] = Field(None, description="Project area in acres")
    num_plan_sheets: Optional[int] = Field(None, description="Number of plan sheets")
    custom_scope: List[str] = Field(default=[], description="Custom scope items")
    discount_percent: float = Field(0, ge=0, le=100)
    rush_fee_percent: float = Field(0, ge=0, le=100)
    proposal_valid_days: int = Field(30, description="Days proposal is valid")
    prepared_by: str = Field("Grant Dozier, PE")
    company: str = Field("LCR", description="LCR & Company")


class ProposalResponse(BaseModel):
    """Response from civil engineering proposal generation"""
    proposal_id: str
    proposal_path: str
    total_price: float
    estimated_days: int
    services_included: List[str]
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
    Calculate pricing for civil engineering services combination.

    **Standard Service Pricing:**
    - DIA: $4,500 - Drainage Impact Analysis Report
    - GRADING: $3,500 - Grading Plan Review & Design
    - DETENTION: $5,000 - Detention Pond Design & Analysis
    - TOC: $1,500 - Time of Concentration Analysis
    - REVIEW: $2,500 - Plan Review & QA Services
    - SURVEY: $2,000 - Survey Coordination & Review
    - SUBMITTAL: $1,200 - Submittal Package Preparation
    - CONSTRUCTION: $1,800 - Construction Observation Services
    - STORMWATER: $3,800 - Stormwater Management Plan

    **Package Discounts:**
    - 3+ services: 5% discount
    - 5+ services: 10% discount
    - 7+ services: 15% discount

    **Custom Discounts:**
    - Additional discounts can be applied for repeat clients or special circumstances

    **Rush Fees:**
    - Optional rush fee for expedited delivery

    **Example:**
    ```json
    {
      "services": ["DIA", "GRADING"],
      "discount_percent": 0,
      "rush_fee_percent": 0
    }
    ```

    **Result:**
    ```json
    {
      "subtotal": 8000.00,
      "total": 8000.00,
      "estimated_days": 18,
      "estimated_completion": "December 15, 2024"
    }
    ```
    """
    try:
        logger.info(f"Calculating pricing for services: {request.services}")

        calculator = PricingCalculator()
        result = calculator.calculate_total(
            services=request.services,
            discount_percent=Decimal(str(request.discount_percent)),
            rush_fee_percent=Decimal(str(request.rush_fee_percent))
        )

        # Convert service objects to dicts for response
        services_dict = [
            {
                "service_id": s.service_id,
                "service_name": s.service_name,
                "description": s.description,
                "base_price": float(s.base_price),
                "time_estimate_days": s.time_estimate_days,
                "deliverables": s.deliverables,
                "unit": s.unit,
            }
            for s in result["services"]
        ]

        return PricingResponse(
            subtotal=result["subtotal"],
            package_discount_percent=result["package_discount_percent"],
            total_discount_percent=result["total_discount_percent"],
            discount_amount=result["discount_amount"],
            discounted_subtotal=result["discounted_subtotal"],
            rush_fee_amount=result["rush_fee_amount"],
            total=result["total"],
            estimated_days=result["estimated_days"],
            estimated_completion=result["estimated_completion"],
            services=services_dict,
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
    Generate professional civil engineering services proposal document.

    **Proposal Includes:**
    1. **Cover Page**: LCR & Company branding, project info, validity dates
    2. **Project Overview**: Description, jurisdiction, project type
    3. **Scope of Services**: Detailed service descriptions and deliverables
    4. **Professional Fee Estimate**: Itemized pricing with discounts and totals
    5. **Project Timeline**: Estimated duration and milestones
    6. **Terms & Conditions**: Standard terms for professional engineering services
    7. **Signature Page**: Client acceptance signatures

    **Output Format:**
    - Word (.docx) - Editable, professional formatting
    - Client-ready for immediate delivery

    **Use Cases:**
    - Drainage engineering service proposals
    - Plan review service quotes
    - Multi-service project packages

    **Example:**
    ```json
    {
      "client_name": "Lafayette Parish School Board",
      "client_contact": "John Smith",
      "client_email": "john@lpss.edu",
      "project_name": "L.J. Alleman Middle School Drainage Improvements",
      "project_location": "Lafayette, LA",
      "project_description": "Comprehensive drainage analysis and grading plan review",
      "jurisdiction": "Lafayette UDC",
      "project_type": "Educational",
      "services_requested": ["DIA", "GRADING", "REVIEW"]
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
            jurisdiction=request.jurisdiction,
            project_type=request.project_type,
            services_requested=request.services_requested,
            project_area_acres=Decimal(str(request.project_area_acres)) if request.project_area_acres else None,
            num_plan_sheets=request.num_plan_sheets,
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
            services=request.services_requested,
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
                "services": request.services_requested,
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
            services_included=request.services_requested,
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


@router.get("/services/pricing")
async def get_service_pricing():
    """
    Get pricing information for all civil engineering services.

    Returns detailed information about each service including:
    - Service ID and name
    - Description
    - Base price
    - Estimated time
    - Deliverables list
    - Pricing unit

    **Use For:**
    - Building custom pricing calculators
    - Displaying service options to clients
    - Creating custom proposals
    """
    try:
        calculator = PricingCalculator()

        services = [
            {
                "service_id": s.service_id,
                "service_name": s.service_name,
                "description": s.description,
                "base_price": float(s.base_price),
                "time_estimate_days": s.time_estimate_days,
                "deliverables": s.deliverables,
                "unit": s.unit,
            }
            for s in calculator.SERVICE_PRICING.values()
        ]

        return {
            "services": services,
            "package_discounts": {
                "3_services": "5%",
                "5_services": "10%",
                "7_services": "15%",
            },
            "total_services": len(services),
        }

    except Exception as e:
        logger.error(f"Error getting service pricing: {e}")
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
