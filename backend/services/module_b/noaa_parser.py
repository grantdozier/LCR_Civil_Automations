"""
Module B - NOAA Atlas 14 Parser
Specialized parser for NOAA Atlas 14 rainfall intensity data
"""
from typing import List, Dict, Optional, Tuple
import re
import logging

from .pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class NOAAAtlas14Parser:
    """
    Parse NOAA Atlas 14 Precipitation-Frequency Atlas data.

    NOAA Atlas 14 provides rainfall intensity data for various:
    - Return periods (2, 5, 10, 25, 50, 100, 200, 500, 1000 years)
    - Durations (5 min, 10 min, 15 min, 30 min, 1 hr, 2 hr, etc.)
    - Locations (latitude/longitude specific)
    """

    # Standard return periods in NOAA Atlas 14
    RETURN_PERIODS = [2, 5, 10, 25, 50, 100, 200, 500, 1000]

    # Standard durations (in minutes)
    DURATIONS = [5, 10, 15, 30, 60, 120, 180, 360, 720, 1440]

    def __init__(self, pdf_parser: Optional[PDFParser] = None):
        """
        Initialize NOAA Atlas 14 parser.

        Args:
            pdf_parser: Optional PDFParser for extracting from NOAA PDF
        """
        self.parser = pdf_parser
        self.data: List[Dict] = []

    def parse_intensity_table(self, table_data: List[List]) -> List[Dict]:
        """
        Parse a NOAA Atlas 14 intensity table.

        Expected format:
        - Row 1: Header with return periods (years)
        - Column 1: Durations (minutes)
        - Cells: Rainfall intensity values (in/hr)

        Args:
            table_data: 2D array of table data

        Returns:
            List of parsed intensity records
        """
        if not table_data or len(table_data) < 2:
            return []

        intensities = []

        # Parse header row to get return periods
        header = table_data[0]
        return_periods = []

        for cell in header[1:]:  # Skip first column (duration label)
            if cell is None:
                continue

            # Extract numeric return period
            match = re.search(r'(\d+)', str(cell))
            if match:
                period = int(match.group(1))
                if period in self.RETURN_PERIODS:
                    return_periods.append(period)

        logger.debug(f"Found return periods: {return_periods}")

        # Parse data rows
        for row in table_data[1:]:
            if not row or all(cell is None for cell in row):
                continue

            # Extract duration from first column
            duration_str = str(row[0]).strip()
            duration = self._parse_duration(duration_str)

            if duration is None:
                continue

            # Extract intensities for each return period
            for idx, cell in enumerate(row[1:len(return_periods) + 1]):
                if cell is None:
                    continue

                try:
                    intensity = float(str(cell).strip())

                    record = {
                        "duration_minutes": duration,
                        "return_period_years": return_periods[idx],
                        "intensity_in_per_hr": intensity,
                        "spec_type": "rainfall_intensity",
                        "document_name": "NOAA Atlas 14",
                        "jurisdiction": "NOAA Atlas 14",
                    }
                    intensities.append(record)

                except (ValueError, IndexError) as e:
                    logger.debug(f"Could not parse intensity value: {cell}")
                    continue

        logger.info(f"Parsed {len(intensities)} intensity values from table")
        return intensities

    def get_intensity(
        self,
        duration_minutes: float,
        return_period_years: int
    ) -> Optional[float]:
        """
        Get rainfall intensity for specific duration and return period.

        Args:
            duration_minutes: Duration in minutes
            return_period_years: Return period in years

        Returns:
            Rainfall intensity in inches per hour, or None if not found
        """
        for record in self.data:
            if (record.get("duration_minutes") == duration_minutes and
                record.get("return_period_years") == return_period_years):
                return record.get("intensity_in_per_hr")

        return None

    def interpolate_intensity(
        self,
        duration_minutes: float,
        return_period_years: int
    ) -> Optional[float]:
        """
        Get or interpolate rainfall intensity.

        If exact duration not found, interpolates between available durations.

        Args:
            duration_minutes: Duration in minutes
            return_period_years: Return period in years

        Returns:
            Rainfall intensity (exact or interpolated)
        """
        # Try exact match first
        exact = self.get_intensity(duration_minutes, return_period_years)
        if exact is not None:
            return exact

        # Get all records for this return period
        period_records = [
            r for r in self.data
            if r.get("return_period_years") == return_period_years
        ]

        if len(period_records) < 2:
            return None

        # Sort by duration
        period_records.sort(key=lambda x: x["duration_minutes"])

        # Find bounding durations
        lower_record = None
        upper_record = None

        for record in period_records:
            dur = record["duration_minutes"]
            if dur < duration_minutes:
                lower_record = record
            elif dur > duration_minutes and upper_record is None:
                upper_record = record
                break

        if lower_record is None or upper_record is None:
            return None

        # Linear interpolation
        d1 = lower_record["duration_minutes"]
        d2 = upper_record["duration_minutes"]
        i1 = lower_record["intensity_in_per_hr"]
        i2 = upper_record["intensity_in_per_hr"]

        # Interpolate: i = i1 + (i2 - i1) * (d - d1) / (d2 - d1)
        interpolated = i1 + (i2 - i1) * (duration_minutes - d1) / (d2 - d1)

        logger.debug(
            f"Interpolated intensity for {duration_minutes} min, {return_period_years} yr: "
            f"{interpolated:.4f} in/hr (between {d1} min={i1} and {d2} min={i2})"
        )

        return round(interpolated, 4)

    def _parse_duration(self, duration_str: str) -> Optional[float]:
        """
        Parse duration string to minutes.

        Examples:
        - "5 min" -> 5.0
        - "30" -> 30.0
        - "1 hr" -> 60.0
        - "2 hours" -> 120.0

        Args:
            duration_str: Duration string

        Returns:
            Duration in minutes, or None if invalid
        """
        duration_str = duration_str.lower().strip()

        # Try to extract number and unit
        match = re.search(r'(\d+\.?\d*)\s*(min|hr|hour|day)?', duration_str)

        if not match:
            return None

        value = float(match.group(1))
        unit = match.group(2) if match.group(2) else "min"

        # Convert to minutes
        if unit in ["min", "minute", "minutes"]:
            return value
        elif unit in ["hr", "hour", "hours"]:
            return value * 60
        elif unit in ["day", "days"]:
            return value * 1440
        else:
            # Assume minutes if no unit
            return value

    def load_standard_lafayette_data(self):
        """
        Load standard NOAA Atlas 14 data for Lafayette, LA.

        This is hardcoded data extracted from NOAA Atlas 14 Volume 9
        (Southeastern States including Louisiana).

        Location: Lafayette, LA (approximately 30.2° N, 92.0° W)
        """
        # Standard NOAA Atlas 14 data for Lafayette, LA
        # Source: NOAA Atlas 14 Volume 9, Southeastern States
        lafayette_data = [
            # 5-minute duration
            {"duration_minutes": 5, "return_period_years": 10, "intensity_in_per_hr": 8.92},
            {"duration_minutes": 5, "return_period_years": 25, "intensity_in_per_hr": 10.65},
            {"duration_minutes": 5, "return_period_years": 50, "intensity_in_per_hr": 12.08},
            {"duration_minutes": 5, "return_period_years": 100, "intensity_in_per_hr": 13.60},

            # 10-minute duration
            {"duration_minutes": 10, "return_period_years": 10, "intensity_in_per_hr": 7.25},
            {"duration_minutes": 10, "return_period_years": 25, "intensity_in_per_hr": 8.65},
            {"duration_minutes": 10, "return_period_years": 50, "intensity_in_per_hr": 9.82},
            {"duration_minutes": 10, "return_period_years": 100, "intensity_in_per_hr": 11.05},

            # 15-minute duration
            {"duration_minutes": 15, "return_period_years": 10, "intensity_in_per_hr": 6.38},
            {"duration_minutes": 15, "return_period_years": 25, "intensity_in_per_hr": 7.62},
            {"duration_minutes": 15, "return_period_years": 50, "intensity_in_per_hr": 8.65},
            {"duration_minutes": 15, "return_period_years": 100, "intensity_in_per_hr": 9.74},

            # 30-minute duration
            {"duration_minutes": 30, "return_period_years": 10, "intensity_in_per_hr": 4.85},
            {"duration_minutes": 30, "return_period_years": 25, "intensity_in_per_hr": 5.79},
            {"duration_minutes": 30, "return_period_years": 50, "intensity_in_per_hr": 6.57},
            {"duration_minutes": 30, "return_period_years": 100, "intensity_in_per_hr": 7.40},

            # 60-minute duration (1 hour)
            {"duration_minutes": 60, "return_period_years": 10, "intensity_in_per_hr": 3.54},
            {"duration_minutes": 60, "return_period_years": 25, "intensity_in_per_hr": 4.23},
            {"duration_minutes": 60, "return_period_years": 50, "intensity_in_per_hr": 4.80},
            {"duration_minutes": 60, "return_period_years": 100, "intensity_in_per_hr": 5.41},
        ]

        # Add metadata
        for record in lafayette_data:
            record.update({
                "spec_type": "rainfall_intensity",
                "document_name": "NOAA Atlas 14",
                "jurisdiction": "NOAA Atlas 14",
                "section_reference": "Volume 9 - Lafayette, LA",
            })

        self.data = lafayette_data
        logger.info(f"Loaded {len(self.data)} standard NOAA Atlas 14 records for Lafayette, LA")

    def export_to_database_format(self) -> List[Dict]:
        """
        Export data in database-compatible format.

        Returns:
            List of specifications ready for database insertion
        """
        return self.data
