"""
Module D - Compliance Checker
Validation rules engine for civil engineering plan compliance
"""
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from services.module_d.plan_extractor import SheetMetadata

logger = logging.getLogger(__name__)


class RequirementCategory(Enum):
    """Categories of compliance requirements"""
    LPDES = "Louisiana Pollutant Discharge Elimination System"
    LUS = "Lafayette Utilities System"
    DOTD = "Department of Transportation and Development"
    ASTM = "American Society for Testing and Materials"
    EROSION_CONTROL = "Erosion Control"
    DRAINAGE_DESIGN = "Drainage Design"
    UTILITIES = "Utilities"
    GENERAL = "General Requirements"
    SAFETY = "Safety"
    MATERIALS = "Materials & Specifications"


class Severity(Enum):
    """Severity levels for compliance violations"""
    CRITICAL = "Critical"  # Must fix before approval
    WARNING = "Warning"    # Should fix, but not blocking
    INFO = "Info"          # Informational note


@dataclass
class ValidationRule:
    """
    A single validation rule for plan compliance.

    Attributes:
        rule_id: Unique identifier (e.g., "LPDES-001")
        category: Category of requirement
        description: Human-readable description
        required_text: Text pattern that must be present
        sheet_types: Which sheets this applies to (e.g., ["C-2", "C-9"])
        severity: How critical this requirement is
        regex_pattern: Optional regex pattern for more complex matching
        validation_func: Optional custom validation function
    """
    rule_id: str
    category: RequirementCategory
    description: str
    required_text: List[str]  # Any of these phrases must be present
    sheet_types: List[str]
    severity: Severity = Severity.CRITICAL
    regex_pattern: Optional[str] = None
    validation_func: Optional[Callable] = None


@dataclass
class ComplianceResult:
    """
    Result of a compliance check.

    Attributes:
        rule_id: Which rule was checked
        passed: Whether the check passed
        sheet_number: Which sheet was checked
        message: Description of result
        severity: Severity if failed
        found_text: Actual text found (if passed)
        suggestions: Suggestions for fixing (if failed)
    """
    rule_id: str
    passed: bool
    sheet_number: str
    message: str
    severity: Severity
    found_text: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


class ComplianceChecker:
    """
    Check civil engineering plans for compliance with 25+ standard requirements.

    Validates:
    - LPDES requirements (stormwater discharge)
    - Lafayette Utilities System (LUS) coordination
    - DOTD standards (roads, drainage)
    - ASTM specifications (materials testing)
    - Erosion control BMPs
    - Drainage design standards
    - And 19+ more requirements
    """

    def __init__(self):
        """Initialize compliance checker with standard rules."""
        self.rules = self._load_standard_rules()
        logger.info(f"Loaded {len(self.rules)} validation rules")

    def check_compliance(
        self,
        sheets: List[SheetMetadata],
        custom_rules: Optional[List[ValidationRule]] = None
    ) -> List[ComplianceResult]:
        """
        Check plan sheets for compliance with all rules.

        Args:
            sheets: List of extracted sheet metadata
            custom_rules: Optional additional rules to check

        Returns:
            List of ComplianceResult objects, one per rule checked
        """
        logger.info(f"Checking compliance for {len(sheets)} sheets")

        all_rules = self.rules.copy()
        if custom_rules:
            all_rules.extend(custom_rules)

        results = []

        for rule in all_rules:
            # Check if this rule applies to any of the provided sheets
            applicable_sheets = [
                s for s in sheets
                if s.sheet_number in rule.sheet_types
            ]

            if not applicable_sheets:
                # Rule doesn't apply to these sheets
                continue

            # Check each applicable sheet
            for sheet in applicable_sheets:
                result = self._check_rule(rule, sheet)
                results.append(result)

        # Summary
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        logger.info(
            f"Compliance check complete: {passed} passed, {failed} failed"
        )

        return results

    def _check_rule(
        self,
        rule: ValidationRule,
        sheet: SheetMetadata
    ) -> ComplianceResult:
        """
        Check a single rule against a single sheet.

        Args:
            rule: The validation rule to check
            sheet: The sheet metadata to check against

        Returns:
            ComplianceResult indicating pass/fail
        """
        # Use custom validation function if provided
        if rule.validation_func:
            return rule.validation_func(sheet)

        # Use regex pattern if provided
        if rule.regex_pattern:
            return self._check_regex(rule, sheet)

        # Default: simple text search
        return self._check_text_present(rule, sheet)

    def _check_text_present(
        self,
        rule: ValidationRule,
        sheet: SheetMetadata
    ) -> ComplianceResult:
        """
        Check if required text is present in sheet.

        Args:
            rule: Validation rule with required_text list
            sheet: Sheet to check

        Returns:
            ComplianceResult
        """
        # Combine notes and full text for searching
        search_text = (sheet.notes_text + "\n" + sheet.extracted_text).upper()

        # Check if ANY of the required text phrases is present
        for required_phrase in rule.required_text:
            if required_phrase.upper() in search_text:
                return ComplianceResult(
                    rule_id=rule.rule_id,
                    passed=True,
                    sheet_number=sheet.sheet_number,
                    message=f"✓ {rule.description}",
                    severity=rule.severity,
                    found_text=required_phrase,
                )

        # None of the required phrases found
        return ComplianceResult(
            rule_id=rule.rule_id,
            passed=False,
            sheet_number=sheet.sheet_number,
            message=f"✗ {rule.description}",
            severity=rule.severity,
            suggestions=[
                f"Add note: \"{rule.required_text[0]}\"",
                f"Verify this requirement is documented on sheet {sheet.sheet_number}",
            ],
        )

    def _check_regex(
        self,
        rule: ValidationRule,
        sheet: SheetMetadata
    ) -> ComplianceResult:
        """
        Check using regex pattern.

        Args:
            rule: Validation rule with regex_pattern
            sheet: Sheet to check

        Returns:
            ComplianceResult
        """
        search_text = sheet.notes_text + "\n" + sheet.extracted_text

        match = re.search(rule.regex_pattern, search_text, re.IGNORECASE)

        if match:
            return ComplianceResult(
                rule_id=rule.rule_id,
                passed=True,
                sheet_number=sheet.sheet_number,
                message=f"✓ {rule.description}",
                severity=rule.severity,
                found_text=match.group(0),
            )
        else:
            return ComplianceResult(
                rule_id=rule.rule_id,
                passed=False,
                sheet_number=sheet.sheet_number,
                message=f"✗ {rule.description}",
                severity=rule.severity,
                suggestions=[
                    f"Required pattern not found: {rule.regex_pattern}",
                ],
            )

    def _load_standard_rules(self) -> List[ValidationRule]:
        """
        Load standard validation rules for Lafayette, LA civil plans.

        Returns 25+ validation rules covering:
        - LPDES requirements
        - LUS coordination
        - DOTD standards
        - ASTM specifications
        - And more

        Returns:
            List of ValidationRule objects
        """
        rules = []

        # ============================================================
        # LPDES Requirements (Louisiana Pollutant Discharge)
        # ============================================================

        rules.append(ValidationRule(
            rule_id="LPDES-001",
            category=RequirementCategory.LPDES,
            description="LPDES permit requirement documented",
            required_text=[
                "LPDES",
                "LOUISIANA POLLUTANT DISCHARGE ELIMINATION SYSTEM",
                "LPDES GENERAL PERMIT",
            ],
            sheet_types=["C-2", "C-9"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="LPDES-002",
            category=RequirementCategory.LPDES,
            description="Stormwater Pollution Prevention Plan (SWPPP) referenced",
            required_text=[
                "SWPPP",
                "STORMWATER POLLUTION PREVENTION PLAN",
            ],
            sheet_types=["C-2", "C-9"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="LPDES-003",
            category=RequirementCategory.LPDES,
            description="Weekly inspection requirement documented",
            required_text=[
                "WEEKLY INSPECTION",
                "INSPECTED WEEKLY",
                "INSPECT WEEKLY",
            ],
            sheet_types=["C-9"],
            severity=Severity.WARNING,
        ))

        # ============================================================
        # Lafayette Utilities System (LUS)
        # ============================================================

        rules.append(ValidationRule(
            rule_id="LUS-001",
            category=RequirementCategory.LUS,
            description="LUS coordination note present",
            required_text=[
                "LAFAYETTE UTILITIES SYSTEM",
                "LUS",
                "COORDINATE WITH LUS",
            ],
            sheet_types=["C-2", "C-8"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="LUS-002",
            category=RequirementCategory.LUS,
            description="Louisiana One Call (811) requirement",
            required_text=[
                "LOUISIANA ONE CALL",
                "LA ONE CALL",
                "CALL 811",
                "811",
            ],
            sheet_types=["C-2", "C-8"],
            severity=Severity.CRITICAL,
        ))

        # ============================================================
        # DOTD (Department of Transportation and Development)
        # ============================================================

        rules.append(ValidationRule(
            rule_id="DOTD-001",
            category=RequirementCategory.DOTD,
            description="DOTD standard specifications referenced",
            required_text=[
                "DOTD STANDARD",
                "DOTD SPECIFICATIONS",
                "LA DOTD",
            ],
            sheet_types=["C-2", "C-7"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="DOTD-002",
            category=RequirementCategory.DOTD,
            description="Pavement section conforms to DOTD standards",
            required_text=[
                "DOTD STANDARD",
                "PAVEMENT SECTION",
            ],
            sheet_types=["C-2", "C-5", "C-6"],
            severity=Severity.WARNING,
        ))

        # ============================================================
        # ASTM (American Society for Testing and Materials)
        # ============================================================

        rules.append(ValidationRule(
            rule_id="ASTM-001",
            category=RequirementCategory.ASTM,
            description="Soils testing standard referenced (ASTM D1557)",
            required_text=[
                "ASTM D1557",
                "ASTM D-1557",
            ],
            sheet_types=["C-2", "C-6"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="ASTM-002",
            category=RequirementCategory.ASTM,
            description="Concrete pipe standard referenced (ASTM C478)",
            required_text=[
                "ASTM C478",
                "ASTM C-478",
            ],
            sheet_types=["C-2", "C-7"],
            severity=Severity.WARNING,
        ))

        # ============================================================
        # Erosion Control / SESC
        # ============================================================

        rules.append(ValidationRule(
            rule_id="SESC-001",
            category=RequirementCategory.EROSION_CONTROL,
            description="Silt fence installation requirement",
            required_text=[
                "SILT FENCE",
                "SEDIMENT FENCE",
            ],
            sheet_types=["C-9"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="SESC-002",
            category=RequirementCategory.EROSION_CONTROL,
            description="Construction entrance requirement",
            required_text=[
                "CONSTRUCTION ENTRANCE",
                "STABILIZED ENTRANCE",
            ],
            sheet_types=["C-9"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="SESC-003",
            category=RequirementCategory.EROSION_CONTROL,
            description="Catch basin protection required",
            required_text=[
                "CATCH BASIN PROTECTION",
                "SILT SACK",
                "INLET PROTECTION",
            ],
            sheet_types=["C-9"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="SESC-004",
            category=RequirementCategory.EROSION_CONTROL,
            description="Temporary seeding timeframe specified",
            required_text=[
                "TEMPORARY SEEDING",
                "SEED WITHIN",
                "14 DAYS",
            ],
            sheet_types=["C-9"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="SESC-005",
            category=RequirementCategory.EROSION_CONTROL,
            description="Permanent stabilization requirement",
            required_text=[
                "PERMANENT STABILIZATION",
                "PERMANENT SEEDING",
                "FINAL STABILIZATION",
            ],
            sheet_types=["C-9"],
            severity=Severity.WARNING,
        ))

        # ============================================================
        # Drainage Design
        # ============================================================

        rules.append(ValidationRule(
            rule_id="DRAIN-001",
            category=RequirementCategory.DRAINAGE_DESIGN,
            description="NOAA Atlas 14 referenced for rainfall data",
            required_text=[
                "NOAA ATLAS 14",
                "NOAA ATLAS-14",
            ],
            sheet_types=["C-2", "C-7"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="DRAIN-002",
            category=RequirementCategory.DRAINAGE_DESIGN,
            description="Rational Method documented (Q=CiA)",
            required_text=[
                "RATIONAL METHOD",
                "Q = CIA",
                "Q=CIA",
            ],
            sheet_types=["C-7"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="DRAIN-003",
            category=RequirementCategory.DRAINAGE_DESIGN,
            description="Time of Concentration method specified",
            required_text=[
                "TIME OF CONCENTRATION",
                "Tc",
                "NRCS METHOD",
                "KIRPICH",
            ],
            sheet_types=["C-7"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="DRAIN-004",
            category=RequirementCategory.DRAINAGE_DESIGN,
            description="Design storm event specified",
            required_text=[
                "10-YEAR",
                "25-YEAR",
                "50-YEAR",
                "100-YEAR",
                "STORM EVENT",
            ],
            sheet_types=["C-7"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="DRAIN-005",
            category=RequirementCategory.DRAINAGE_DESIGN,
            description="Minimum pipe slope specified",
            required_text=[
                "MINIMUM SLOPE",
                "MIN SLOPE",
                "0.5%",
            ],
            sheet_types=["C-7"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="DRAIN-006",
            category=RequirementCategory.DRAINAGE_DESIGN,
            description="Lafayette UDC drainage requirements referenced",
            required_text=[
                "LAFAYETTE UDC",
                "UDC SECTION 3.2",
                "UNIFIED DEVELOPMENT CODE",
            ],
            sheet_types=["C-2", "C-7"],
            severity=Severity.WARNING,
        ))

        # ============================================================
        # Materials & Specifications
        # ============================================================

        rules.append(ValidationRule(
            rule_id="MAT-001",
            category=RequirementCategory.MATERIALS,
            description="Pipe material specified (RCP, HDPE, etc.)",
            required_text=[
                "RCP",
                "REINFORCED CONCRETE PIPE",
                "HDPE",
                "PVC",
            ],
            sheet_types=["C-7", "C-10"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="MAT-002",
            category=RequirementCategory.MATERIALS,
            description="Concrete strength specified",
            required_text=[
                "3000 PSI",
                "4000 PSI",
                "F'C =",
            ],
            sheet_types=["C-2", "C-10"],
            severity=Severity.INFO,
        ))

        # ============================================================
        # Safety & General
        # ============================================================

        rules.append(ValidationRule(
            rule_id="GEN-001",
            category=RequirementCategory.GENERAL,
            description="Professional Engineer seal documented",
            required_text=[
                "P.E.",
                "PE",
                "PROFESSIONAL ENGINEER",
            ],
            sheet_types=["C-1", "C-2"],
            severity=Severity.CRITICAL,
        ))

        rules.append(ValidationRule(
            rule_id="GEN-002",
            category=RequirementCategory.GENERAL,
            description="Project benchmarks documented",
            required_text=[
                "BENCHMARK",
                "BM",
                "DATUM",
            ],
            sheet_types=["C-2", "C-3"],
            severity=Severity.WARNING,
        ))

        rules.append(ValidationRule(
            rule_id="GEN-003",
            category=RequirementCategory.GENERAL,
            description="Maintenance access provided",
            required_text=[
                "MAINTENANCE ACCESS",
                "ACCESS FOR MAINTENANCE",
            ],
            sheet_types=["C-7"],
            severity=Severity.INFO,
        ))

        rules.append(ValidationRule(
            rule_id="SAFE-001",
            category=RequirementCategory.SAFETY,
            description="Traffic control plan referenced",
            required_text=[
                "TRAFFIC CONTROL",
                "MOT",
                "MAINTENANCE OF TRAFFIC",
            ],
            sheet_types=["C-2"],
            severity=Severity.WARNING,
        ))

        logger.info(f"Loaded {len(rules)} standard validation rules")
        return rules

    def generate_summary(self, results: List[ComplianceResult]) -> Dict:
        """
        Generate summary statistics from compliance results.

        Args:
            results: List of ComplianceResult objects

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        # Group by severity
        critical_failures = sum(
            1 for r in results
            if not r.passed and r.severity == Severity.CRITICAL
        )
        warnings = sum(
            1 for r in results
            if not r.passed and r.severity == Severity.WARNING
        )
        info = sum(
            1 for r in results
            if not r.passed and r.severity == Severity.INFO
        )

        # Group by category
        by_category = {}
        for result in results:
            # Extract category from rule_id (e.g., "LPDES-001" -> "LPDES")
            category = result.rule_id.split("-")[0]
            if category not in by_category:
                by_category[category] = {"passed": 0, "failed": 0}

            if result.passed:
                by_category[category]["passed"] += 1
            else:
                by_category[category]["failed"] += 1

        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "critical_failures": critical_failures,
            "warnings": warnings,
            "info": info,
            "by_category": by_category,
            "overall_status": "PASS" if critical_failures == 0 else "FAIL",
        }
