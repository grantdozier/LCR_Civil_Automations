"""
Module D - Plan Review & QA Automation

This module provides automated plan review and quality assurance for civil engineering
plan sets, focusing on drainage-related plan sheets (C-1 through C-18).

Components:
- Plan Extractor: OCR-based extraction of plan sheet text and metadata
- Compliance Checker: Validation rules engine for 25+ standard note requirements
- QA Report Generator: Professional PDF reports with pass/fail results

Standard Notes Checked:
- LPDES (Louisiana Pollutant Discharge Elimination System)
- LUS (Lafayette Utilities System)
- DOTD (Department of Transportation and Development)
- ASTM (American Society for Testing and Materials)
- And 20+ more civil engineering standard notes

Sheet Types Supported:
- C-1: Cover Sheet
- C-2: General Notes
- C-3: Existing Conditions
- C-4: Demolition Plan
- C-5: Site Layout Plan
- C-6: Grading Plan
- C-7: Drainage Plan
- C-8: Utility Plan
- C-9: Erosion Control Plan
- C-10: Detail Sheets
- C-11 through C-18: Additional detail and profile sheets
"""

from services.module_d.plan_extractor import PlanExtractor, SheetMetadata
from services.module_d.compliance_checker import (
    ComplianceChecker,
    ValidationRule,
    ComplianceResult,
    Severity,
    RequirementCategory,
)
from services.module_d.qa_report_generator import QAReportGenerator

__all__ = [
    "PlanExtractor",
    "SheetMetadata",
    "ComplianceChecker",
    "ValidationRule",
    "ComplianceResult",
    "Severity",
    "RequirementCategory",
    "QAReportGenerator",
]
