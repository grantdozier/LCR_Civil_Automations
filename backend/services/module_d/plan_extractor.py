"""
Module D - Plan Sheet Extractor
OCR-based extraction of plan sheet text and metadata
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SheetMetadata:
    """
    Metadata extracted from a plan sheet.

    Attributes:
        sheet_number: Sheet identifier (e.g., "C-1", "C-7")
        sheet_title: Title of the sheet (e.g., "DRAINAGE PLAN")
        project_name: Name of the project
        project_number: Project number
        date: Date on the plan sheet
        revision: Revision number/date
        scale: Drawing scale (e.g., "1\"=20'")
        engineer: Professional engineer name
        seal_found: Whether PE seal was detected
        notes_text: Full text content from notes section
        extracted_text: Complete extracted text from sheet
        confidence_score: OCR confidence (0.0 to 1.0)
    """
    sheet_number: str
    sheet_title: str
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    date: Optional[str] = None
    revision: Optional[str] = None
    scale: Optional[str] = None
    engineer: Optional[str] = None
    seal_found: bool = False
    notes_text: str = ""
    extracted_text: str = ""
    confidence_score: float = 0.0
    errors: List[str] = field(default_factory=list)


class PlanExtractor:
    """
    Extract text and metadata from civil engineering plan sheets using OCR.

    Supports:
    - PDF plan sheets
    - Image files (PNG, JPG, TIFF)
    - Multi-page plan sets

    Uses Tesseract OCR for text extraction and pattern matching for metadata.
    """

    # Sheet type patterns
    SHEET_PATTERNS = {
        "C-1": ["COVER", "INDEX", "SHEET INDEX"],
        "C-2": ["GENERAL NOTES", "NOTES"],
        "C-3": ["EXISTING CONDITIONS", "EXISTING"],
        "C-4": ["DEMOLITION", "DEMO"],
        "C-5": ["SITE LAYOUT", "SITE PLAN"],
        "C-6": ["GRADING PLAN", "GRADING"],
        "C-7": ["DRAINAGE PLAN", "DRAINAGE"],
        "C-8": ["UTILITY PLAN", "UTILITIES"],
        "C-9": ["EROSION CONTROL", "SESC"],
        "C-10": ["DETAILS", "DETAIL SHEET"],
    }

    def __init__(self, use_ocr: bool = True):
        """
        Initialize plan extractor.

        Args:
            use_ocr: Whether to use OCR for text extraction (True)
                    or just extract embedded PDF text (False)
        """
        self.use_ocr = use_ocr

    def extract_from_pdf(
        self,
        pdf_path: str,
        sheet_numbers: Optional[List[str]] = None
    ) -> List[SheetMetadata]:
        """
        Extract metadata from PDF plan set.

        Args:
            pdf_path: Path to PDF file
            sheet_numbers: Optional list of specific sheets to extract (e.g., ["C-7", "C-9"])
                          If None, extracts all sheets

        Returns:
            List of SheetMetadata objects, one per sheet
        """
        logger.info(f"Extracting from PDF: {pdf_path}")

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            if self.use_ocr:
                return self._extract_with_ocr(pdf_file, sheet_numbers)
            else:
                return self._extract_from_text(pdf_file, sheet_numbers)
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}", exc_info=True)
            raise

    def _extract_with_ocr(
        self,
        pdf_file: Path,
        sheet_numbers: Optional[List[str]]
    ) -> List[SheetMetadata]:
        """
        Extract using OCR (Tesseract).

        This is a placeholder implementation. In production, this would:
        1. Convert PDF pages to images using pdf2image
        2. Run Tesseract OCR on each page
        3. Extract text and parse metadata

        For now, returns mock data for testing.
        """
        logger.info(f"Using OCR extraction (mock mode)")

        # Mock implementation - in production, use pytesseract
        sheets = []

        # Simulate extracting C-2, C-7, C-9 (common drainage-related sheets)
        mock_sheets = [
            SheetMetadata(
                sheet_number="C-2",
                sheet_title="GENERAL NOTES",
                project_name="Example Project",
                project_number="2024-001",
                notes_text=self._get_mock_c2_notes(),
                extracted_text="[Full C-2 text content would be here]",
                confidence_score=0.95,
            ),
            SheetMetadata(
                sheet_number="C-7",
                sheet_title="DRAINAGE PLAN",
                project_name="Example Project",
                project_number="2024-001",
                scale="1\"=20'",
                notes_text=self._get_mock_c7_notes(),
                extracted_text="[Full C-7 text content would be here]",
                confidence_score=0.92,
            ),
            SheetMetadata(
                sheet_number="C-9",
                sheet_title="EROSION CONTROL PLAN",
                project_name="Example Project",
                project_number="2024-001",
                notes_text=self._get_mock_c9_notes(),
                extracted_text="[Full C-9 text content would be here]",
                confidence_score=0.90,
            ),
        ]

        # Filter by sheet_numbers if specified
        if sheet_numbers:
            sheets = [s for s in mock_sheets if s.sheet_number in sheet_numbers]
        else:
            sheets = mock_sheets

        logger.info(f"Extracted {len(sheets)} sheets")
        return sheets

    def _extract_from_text(
        self,
        pdf_file: Path,
        sheet_numbers: Optional[List[str]]
    ) -> List[SheetMetadata]:
        """
        Extract embedded text from PDF without OCR.

        Uses PyPDF2 or similar to extract text directly from PDF.
        Faster than OCR but only works if PDF has embedded text.
        """
        logger.info(f"Extracting embedded text (non-OCR mode)")

        # Placeholder - would use PyPDF2.PdfReader in production
        raise NotImplementedError("Non-OCR extraction not yet implemented")

    def identify_sheet_type(self, text: str) -> Tuple[Optional[str], float]:
        """
        Identify sheet type from extracted text.

        Args:
            text: Extracted text from sheet

        Returns:
            Tuple of (sheet_number, confidence_score)
            Returns (None, 0.0) if no match found
        """
        text_upper = text.upper()

        for sheet_num, keywords in self.SHEET_PATTERNS.items():
            for keyword in keywords:
                if keyword in text_upper:
                    # Simple confidence based on keyword match
                    confidence = 0.8 if len(keyword) > 10 else 0.6
                    return sheet_num, confidence

        return None, 0.0

    def extract_project_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract project metadata from text using regex patterns.

        Args:
            text: Extracted text from sheet

        Returns:
            Dictionary with project_name, project_number, date, engineer, etc.
        """
        metadata = {
            "project_name": None,
            "project_number": None,
            "date": None,
            "engineer": None,
            "scale": None,
        }

        # Project number pattern: "PROJECT NO.: 2024-001" or similar
        project_num_match = re.search(
            r"PROJECT\s+(?:NO\.?|NUMBER):?\s*([A-Z0-9\-]+)",
            text,
            re.IGNORECASE
        )
        if project_num_match:
            metadata["project_number"] = project_num_match.group(1)

        # Date pattern: "MM/DD/YYYY" or "MONTH DD, YYYY"
        date_match = re.search(
            r"(\d{1,2}/\d{1,2}/\d{4}|\w+\s+\d{1,2},\s+\d{4})",
            text
        )
        if date_match:
            metadata["date"] = date_match.group(1)

        # Scale pattern: '1"=20'' or similar
        scale_match = re.search(
            r'(\d+"\s*=\s*\d+\')',
            text
        )
        if scale_match:
            metadata["scale"] = scale_match.group(1)

        # Professional Engineer pattern
        pe_match = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+(?:P\.E\.|PE)",
            text
        )
        if pe_match:
            metadata["engineer"] = pe_match.group(1)

        return metadata

    def extract_notes_section(self, text: str) -> str:
        """
        Extract the notes section from plan sheet text.

        Looks for common note headers like:
        - GENERAL NOTES
        - DRAINAGE NOTES
        - EROSION CONTROL NOTES

        Args:
            text: Full extracted text from sheet

        Returns:
            Notes section text, or empty string if not found
        """
        # Common note section headers
        note_headers = [
            "GENERAL NOTES",
            "DRAINAGE NOTES",
            "EROSION CONTROL NOTES",
            "SESC NOTES",
            "NOTES:",
        ]

        text_upper = text.upper()

        for header in note_headers:
            idx = text_upper.find(header)
            if idx != -1:
                # Extract from header to end (or next major section)
                notes = text[idx:]

                # Try to find end of notes section
                end_markers = ["LEGEND", "DETAILS", "SCALE:", "SHEET"]
                for marker in end_markers:
                    end_idx = notes.upper().find(marker, len(header))
                    if end_idx != -1:
                        notes = notes[:end_idx]
                        break

                return notes.strip()

        return ""

    def detect_pe_seal(self, image_path: str) -> bool:
        """
        Detect if a Professional Engineer seal is present on the plan.

        Uses image processing to look for circular seal patterns.

        Args:
            image_path: Path to plan sheet image

        Returns:
            True if seal detected, False otherwise
        """
        # Placeholder - would use OpenCV circle detection in production
        logger.info(f"PE seal detection not yet implemented")
        return False

    # Mock data for testing
    def _get_mock_c2_notes(self) -> str:
        """Mock C-2 General Notes"""
        return """GENERAL NOTES:

1. ALL WORK SHALL COMPLY WITH THE LOUISIANA POLLUTANT DISCHARGE ELIMINATION SYSTEM (LPDES) REQUIREMENTS.

2. CONTRACTOR SHALL COORDINATE WITH LAFAYETTE UTILITIES SYSTEM (LUS) PRIOR TO ANY UTILITY WORK.

3. ALL UNDERGROUND UTILITIES SHALL BE LOCATED BY LOUISIANA ONE CALL (811) PRIOR TO EXCAVATION.

4. EROSION CONTROL MEASURES SHALL BE INSTALLED PRIOR TO ANY LAND DISTURBING ACTIVITIES.

5. ALL PAVEMENT SECTIONS SHALL CONFORM TO DOTD STANDARD SPECIFICATIONS.

6. SOILS TESTING SHALL BE PERFORMED IN ACCORDANCE WITH ASTM D1557.

7. CONTRACTOR SHALL MAINTAIN EROSION CONTROL BMPS THROUGHOUT CONSTRUCTION.

8. ALL CATCH BASINS SHALL BE PROTECTED WITH SILT SACKS DURING CONSTRUCTION.

9. DRAINAGE SYSTEM SHALL BE DESIGNED FOR 25-YEAR STORM EVENT.

10. ALL DETENTION PONDS SHALL INCLUDE MAINTENANCE ACCESS.
"""

    def _get_mock_c7_notes(self) -> str:
        """Mock C-7 Drainage Plan Notes"""
        return """DRAINAGE NOTES:

1. ALL DRAINAGE CALCULATIONS IN ACCORDANCE WITH NOAA ATLAS 14.

2. RATIONAL METHOD USED FOR PEAK FLOW CALCULATIONS: Q = CiA.

3. TIME OF CONCENTRATION CALCULATED USING NRCS METHOD.

4. MINIMUM PIPE SLOPE: 0.5% FOR STORM DRAIN PIPES.

5. ALL STORM DRAIN INLETS SHALL BE CATCH BASIN TYPE PER DOTD STANDARD.

6. STORM DRAIN PIPES SHALL BE REINFORCED CONCRETE PIPE (RCP) CLASS III.

7. ALL MANHOLES SHALL BE PRECAST CONCRETE PER ASTM C478.

8. DRAINAGE SYSTEM DESIGNED FOR POST-DEVELOPMENT CONDITIONS.

9. DETENTION BASIN OUTLET CONTROL STRUCTURE PER DETAIL 7-D1.

10. Lafayette UDC SECTION 3.2 DRAINAGE REQUIREMENTS APPLY.
"""

    def _get_mock_c9_notes(self) -> str:
        """Mock C-9 Erosion Control Notes"""
        return """EROSION CONTROL NOTES:

1. LPDES GENERAL PERMIT FOR STORMWATER DISCHARGES REQUIRED.

2. SILT FENCE SHALL BE INSTALLED ALONG ALL DISTURBED PERIMETERS.

3. CONSTRUCTION ENTRANCE SHALL USE 6" CRUSHED STONE, 50' MINIMUM LENGTH.

4. ALL CATCH BASINS SHALL BE PROTECTED WITH SILT SACKS.

5. EROSION CONTROL MEASURES SHALL BE INSPECTED WEEKLY AND AFTER RAIN EVENTS.

6. TEMPORARY SEEDING SHALL BE APPLIED TO DISTURBED AREAS WITHIN 14 DAYS.

7. PERMANENT STABILIZATION REQUIRED WITHIN 7 DAYS OF FINAL GRADE.

8. CONTRACTOR SHALL MAINTAIN SWPPP ON SITE AT ALL TIMES.

9. ALL BMPS SHALL CONFORM TO LPDES GENERAL PERMIT REQUIREMENTS.

10. WEEKLY INSPECTION REPORTS SHALL BE SUBMITTED TO OWNER.
"""


class PlanSetAnalyzer:
    """
    Analyze complete plan sets and cross-reference between sheets.

    Validates:
    - Sheet index matches actual sheets
    - Drainage calculations match drainage plan
    - Details referenced in plans actually exist
    - Consistency of project metadata across sheets
    """

    def __init__(self):
        self.extractor = PlanExtractor()

    def analyze_plan_set(
        self,
        pdf_path: str,
        drainage_results: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Analyze complete plan set and cross-reference with drainage calculations.

        Args:
            pdf_path: Path to PDF plan set
            drainage_results: Optional drainage calculation results from Module C

        Returns:
            Dictionary with analysis results including:
            - sheets_found: List of sheet numbers found
            - missing_sheets: Expected sheets not found
            - metadata_consistency: Whether metadata is consistent
            - drainage_match: Whether drainage calcs match plan
            - errors: List of issues found
        """
        logger.info(f"Analyzing plan set: {pdf_path}")

        # Extract all sheets
        sheets = self.extractor.extract_from_pdf(pdf_path)

        results = {
            "sheets_found": [s.sheet_number for s in sheets],
            "sheet_count": len(sheets),
            "missing_sheets": [],
            "metadata_consistent": True,
            "drainage_match": None,
            "errors": [],
            "warnings": [],
        }

        # Check for expected civil sheets
        expected_sheets = ["C-1", "C-2", "C-7"]  # Minimum expected
        results["missing_sheets"] = [
            s for s in expected_sheets
            if s not in results["sheets_found"]
        ]

        # Check metadata consistency
        if len(sheets) > 1:
            project_numbers = [s.project_number for s in sheets if s.project_number]
            if len(set(project_numbers)) > 1:
                results["metadata_consistent"] = False
                results["errors"].append(
                    f"Inconsistent project numbers: {set(project_numbers)}"
                )

        # Cross-reference drainage calculations if provided
        if drainage_results:
            results["drainage_match"] = self._verify_drainage_match(
                sheets,
                drainage_results
            )

        logger.info(f"Plan set analysis complete: {results['sheet_count']} sheets found")
        return results

    def _verify_drainage_match(
        self,
        sheets: List[SheetMetadata],
        drainage_results: Dict
    ) -> Dict[str, bool]:
        """
        Verify drainage calculations match drainage plan notes.

        Checks:
        - Drainage areas mentioned in plan exist in calculations
        - Storm event (10-year, 25-year, etc.) matches
        - Design method (Rational Method) is documented

        Args:
            sheets: Extracted sheet metadata
            drainage_results: Results from Module C drainage calculations

        Returns:
            Dictionary with match results
        """
        match_results = {
            "method_documented": False,
            "storm_event_documented": False,
            "areas_match": False,
        }

        # Find C-7 (Drainage Plan)
        c7_sheet = next((s for s in sheets if s.sheet_number == "C-7"), None)
        if not c7_sheet:
            return match_results

        notes_text = c7_sheet.notes_text.upper()

        # Check if Rational Method is documented
        if "RATIONAL METHOD" in notes_text:
            match_results["method_documented"] = True

        # Check if storm events are documented
        for storm in ["10-YEAR", "25-YEAR", "50-YEAR", "100-YEAR"]:
            if storm in notes_text:
                match_results["storm_event_documented"] = True
                break

        # Could add more sophisticated matching here
        # For now, basic validation

        return match_results
