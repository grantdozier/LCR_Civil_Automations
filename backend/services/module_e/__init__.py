"""
Module E - Proposal & Document Automation

This module provides automated generation of professional proposals, cover letters,
and submittal documents with consistent branding for LCR & Company and Dozier Tech.

Components:
- Proposal Generator: Auto-generate branded proposals with scope, timeline, pricing
- Cover Letter Generator: Professional cover letters for submittals
- Document Templates: Reusable templates for consistent formatting
- Branding Manager: Merge LCR & Dozier Tech branding assets

Features:
- Automated pricing calculation based on module selection
- Timeline estimation from project scope
- Professional formatting with company branding
- Customizable templates for different proposal types
- Bulk document generation for multiple projects

Proposal Types:
- Drainage Analysis Proposals (Module C)
- Full Civil Engineering Services (Modules A-C)
- Plan Review & QA Services (Module D)
- Custom combinations
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
