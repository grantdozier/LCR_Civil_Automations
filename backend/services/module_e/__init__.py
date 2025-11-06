"""
Module E - Proposal & Document Automation

This module provides automated generation of professional proposals, cover letters,
and submittal documents for LCR & Company's civil engineering clients.

Purpose:
Automates creation of client proposals, submittal letters, and internal summaries
based on pre-approved LCR templates for civil engineering services.

Components:
- Proposal Generator: Auto-generate branded proposals for civil engineering services
- Cover Letter Generator: Professional cover letters for drainage submittals
- Document Templates: Reusable LCR-branded templates
- Branding Manager: LCR & Company branding assets

Features:
- Automated pricing calculation for civil engineering services
- Timeline estimation from service scope
- Professional formatting with LCR branding
- Customizable templates for different service types
- Integration with project metadata and technical inputs (C-values, rainfall data)

Service Types:
- Drainage Impact Analysis (DIA)
- Grading Plan Review & Design
- Detention Pond Design
- Stormwater Management Plans
- Plan Review & QA Services
- Survey Coordination
- Construction Observation
- Custom service combinations
"""

from services.module_e.proposal_generator import (
    ProposalGenerator,
    ProposalData,
    PricingCalculator,
)
from services.module_e.cover_letter_generator import (
    CoverLetterGenerator,
    SubmittalPackage,
    SubmittalDocument,
)
from services.module_e.document_templates import (
    TemplateManager,
    BrandingAssets,
)

__all__ = [
    "ProposalGenerator",
    "ProposalData",
    "PricingCalculator",
    "CoverLetterGenerator",
    "SubmittalPackage",
    "SubmittalDocument",
    "TemplateManager",
    "BrandingAssets",
]
