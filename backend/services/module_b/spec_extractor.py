"""
Module B - Specification Extractor
Extract specific regulatory specifications from parsed PDFs
"""
from typing import List, Dict, Optional, Tuple
import re
import logging
from decimal import Decimal

from .pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class SpecificationExtractor:
    """
    Extract drainage-related specifications from regulatory documents.

    Extracts:
    - Runoff coefficients (C-values) by land use type
    - Rainfall intensity tables
    - Time of Concentration (Tc) limits
    - Detention/retention requirements
    """

    def __init__(self, pdf_parser: PDFParser):
        """
        Initialize extractor.

        Args:
            pdf_parser: PDFParser instance with loaded PDF
        """
        self.parser = pdf_parser
        self.specifications: List[Dict] = []

    def extract_runoff_coefficients(
        self,
        table_keywords: List[str] = None
    ) -> List[Dict]:
        """
        Extract runoff coefficient (C-value) tables from PDF.

        Args:
            table_keywords: Keywords to identify C-value tables
                          Default: ["runoff coefficient", "c-value", "c value"]

        Returns:
            List of extracted C-value specifications
        """
        if table_keywords is None:
            table_keywords = ["runoff coefficient", "c-value", "c value", "c factor"]

        # Extract all tables
        tables = self.parser.extract_tables()

        c_value_specs = []

        for table in tables:
            # Check if this table contains C-values
            is_c_table = False

            # Check first few rows for keywords
            for row in table["data"][:3]:
                row_text = " ".join(str(cell) for cell in row if cell).lower()
                if any(keyword in row_text for keyword in table_keywords):
                    is_c_table = True
                    break

            if not is_c_table:
                continue

            # Parse table data
            logger.info(f"Found C-value table on page {table['page_number']}")

            # Try to extract land use and C-values from table
            for row_idx, row in enumerate(table["data"]):
                # Skip header rows
                if row_idx < 2:
                    continue

                # Extract land use type and C-value
                land_use = None
                c_min = None
                c_max = None
                c_recommended = None

                for cell in row:
                    if cell is None or str(cell).strip() == "":
                        continue

                    cell_str = str(cell).strip()

                    # Try to parse as C-value (decimal between 0 and 1)
                    if self._is_c_value(cell_str):
                        c_val = float(cell_str)

                        if c_min is None:
                            c_min = c_val
                        elif c_max is None:
                            c_max = c_val
                        elif c_recommended is None:
                            c_recommended = c_val

                    # Try to parse as land use description
                    elif len(cell_str) > 3 and not cell_str.replace(".", "").replace("-", "").isdigit():
                        land_use = cell_str

                # If we found a land use and at least one C-value, save it
                if land_use and (c_min or c_max or c_recommended):
                    spec = {
                        "land_use_type": land_use,
                        "c_value_min": c_min,
                        "c_value_max": c_max,
                        "c_value_recommended": c_recommended or c_max or c_min,
                        "page_number": table["page_number"],
                        "spec_type": "runoff_coefficient",
                    }
                    c_value_specs.append(spec)

        logger.info(f"Extracted {len(c_value_specs)} runoff coefficient specifications")
        return c_value_specs

    def extract_rainfall_intensity(
        self,
        search_terms: List[str] = None
    ) -> List[Dict]:
        """
        Extract rainfall intensity data (NOAA Atlas 14 or similar).

        Args:
            search_terms: Keywords to identify rainfall intensity tables

        Returns:
            List of rainfall intensity specifications
        """
        if search_terms is None:
            search_terms = ["rainfall intensity", "intensity", "precipitation", "noaa atlas"]

        tables = self.parser.extract_tables()
        intensity_specs = []

        for table in tables:
            # Check if this table contains rainfall intensities
            is_intensity_table = False

            for row in table["data"][:3]:
                row_text = " ".join(str(cell) for cell in row if cell).lower()
                if any(term in row_text for term in search_terms):
                    is_intensity_table = True
                    break

            if not is_intensity_table:
                continue

            logger.info(f"Found rainfall intensity table on page {table['page_number']}")

            # Parse table (duration, return period, intensity)
            for row_idx, row in enumerate(table["data"]):
                if row_idx < 2:  # Skip headers
                    continue

                duration = None
                return_period = None
                intensity = None

                for cell in row:
                    if cell is None:
                        continue

                    cell_str = str(cell).strip()

                    # Try to parse as duration (e.g., "5 min", "10", "15 minutes")
                    duration_match = re.search(r'(\d+)\s*(min|hr|hour)?', cell_str, re.IGNORECASE)
                    if duration_match and duration is None:
                        duration = float(duration_match.group(1))

                    # Try to parse as return period (e.g., "10", "25-year", "100 yr")
                    period_match = re.search(r'(\d+)\s*(year|yr)?', cell_str, re.IGNORECASE)
                    if period_match and return_period is None:
                        return_period = int(period_match.group(1))

                    # Try to parse as intensity (decimal value)
                    if re.match(r'^\d+\.\d+$', cell_str) and intensity is None:
                        try:
                            intensity = float(cell_str)
                        except ValueError:
                            pass

                if duration and return_period and intensity:
                    spec = {
                        "duration_minutes": duration,
                        "return_period_years": return_period,
                        "intensity_in_per_hr": intensity,
                        "page_number": table["page_number"],
                        "spec_type": "rainfall_intensity",
                    }
                    intensity_specs.append(spec)

        logger.info(f"Extracted {len(intensity_specs)} rainfall intensity specifications")
        return intensity_specs

    def extract_tc_limits(self) -> List[Dict]:
        """
        Extract Time of Concentration (Tc) limits and requirements.

        Returns:
            List of Tc limit specifications
        """
        tc_specs = []

        # Search for Tc-related text
        tc_patterns = [
            r"time of concentration.*?(\d+\.?\d*)\s*min",
            r"tc.*?minimum.*?(\d+\.?\d*)\s*min",
            r"tc.*?maximum.*?(\d+\.?\d*)\s*min",
        ]

        for pattern in tc_patterns:
            matches = self.parser.search_text(pattern, case_sensitive=False)

            for match in matches:
                # Extract the numeric value
                value_match = re.search(r'(\d+\.?\d*)', match["matched_text"])
                if value_match:
                    tc_value = float(value_match.group(1))

                    # Determine if this is min or max
                    tc_type = "minimum" if "min" in match["matched_text"].lower() and "minimum" in match["matched_text"].lower() else "maximum"

                    spec = {
                        f"tc_{tc_type}_minutes": tc_value,
                        "page_number": match["page_number"],
                        "spec_type": "tc_limit",
                        "context": match["context"],
                    }
                    tc_specs.append(spec)

        logger.info(f"Extracted {len(tc_specs)} Tc limit specifications")
        return tc_specs

    def extract_detention_requirements(self) -> List[Dict]:
        """
        Extract detention/retention requirements.

        Returns:
            List of detention requirement specifications
        """
        detention_specs = []

        # Search for detention-related rules
        detention_patterns = [
            r"detention.*?required",
            r"retention.*?required",
            r"detention.*?volume",
            r"storage.*?volume",
        ]

        for pattern in detention_patterns:
            matches = self.parser.search_text(pattern, case_sensitive=False)

            for match in matches:
                spec = {
                    "detention_rule": match["matched_text"],
                    "page_number": match["page_number"],
                    "spec_type": "detention_requirement",
                    "full_text": match["context"],
                }
                detention_specs.append(spec)

        logger.info(f"Extracted {len(detention_specs)} detention requirement specifications")
        return detention_specs

    def extract_all(
        self,
        jurisdiction: str = "Unknown",
        document_name: str = "Unknown"
    ) -> List[Dict]:
        """
        Extract all specification types from PDF.

        Args:
            jurisdiction: Jurisdiction name (e.g., "Lafayette UDC", "DOTD")
            document_name: Document name

        Returns:
            List of all extracted specifications
        """
        logger.info(f"Extracting all specifications from {document_name}")

        all_specs = []

        # Extract each type
        all_specs.extend(self.extract_runoff_coefficients())
        all_specs.extend(self.extract_rainfall_intensity())
        all_specs.extend(self.extract_tc_limits())
        all_specs.extend(self.extract_detention_requirements())

        # Add metadata to each spec
        for spec in all_specs:
            spec["jurisdiction"] = jurisdiction
            spec["document_name"] = document_name

        logger.info(f"Total specifications extracted: {len(all_specs)}")
        return all_specs

    def _is_c_value(self, text: str) -> bool:
        """
        Check if text represents a valid C-value (0.0 to 1.0).

        Args:
            text: Text to check

        Returns:
            True if valid C-value
        """
        try:
            value = float(text)
            return 0.0 <= value <= 1.0
        except (ValueError, TypeError):
            return False

    def _clean_land_use_text(self, text: str) -> str:
        """
        Clean land use description text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common prefixes/suffixes
        text = re.sub(r'^\d+\.?\s*', '', text)  # Remove leading numbers
        text = re.sub(r'\s*\(.*?\)\s*', ' ', text)  # Remove parentheticals

        return text.strip()

    def to_database_format(self, specs: List[Dict]) -> List[Dict]:
        """
        Convert extracted specs to database-compatible format.

        Args:
            specs: List of extracted specifications

        Returns:
            List of specs ready for database insertion
        """
        db_specs = []

        for spec in specs:
            db_spec = {
                "jurisdiction": spec.get("jurisdiction", "Unknown"),
                "document_name": spec.get("document_name", "Unknown"),
                "spec_type": spec.get("spec_type"),
                "extraction_confidence": 0.80,  # Default confidence (can be improved with LangChain)
                "verified": False,
            }

            # Add type-specific fields
            if spec.get("spec_type") == "runoff_coefficient":
                db_spec.update({
                    "land_use_type": spec.get("land_use_type"),
                    "c_value_min": spec.get("c_value_min"),
                    "c_value_max": spec.get("c_value_max"),
                    "c_value_recommended": spec.get("c_value_recommended"),
                })

            elif spec.get("spec_type") == "rainfall_intensity":
                db_spec.update({
                    "duration_minutes": spec.get("duration_minutes"),
                    "return_period_years": spec.get("return_period_years"),
                    "intensity_in_per_hr": spec.get("intensity_in_per_hr"),
                })

            elif spec.get("spec_type") == "tc_limit":
                db_spec.update({
                    "tc_min_minutes": spec.get("tc_minimum_minutes"),
                    "tc_max_minutes": spec.get("tc_maximum_minutes"),
                    "full_text": spec.get("context"),
                })

            elif spec.get("spec_type") == "detention_requirement":
                db_spec.update({
                    "detention_rule": spec.get("detention_rule"),
                    "full_text": spec.get("full_text"),
                })

            # Add section reference if available
            if "page_number" in spec:
                db_spec["section_reference"] = f"Page {spec['page_number']}"

            db_specs.append(db_spec)

        return db_specs
