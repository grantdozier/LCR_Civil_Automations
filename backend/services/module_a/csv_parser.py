"""
Module A - Survey CSV Parser
Parses survey CSV files from Civil 3D / survey equipment
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SurveyPoint:
    """Represents a single survey point"""

    def __init__(self, point_name: str, northing: float, easting: float, elevation: float, point_code: str = ""):
        self.point_name = point_name
        self.northing = northing
        self.easting = easting
        self.elevation = elevation
        self.point_code = point_code

    def __repr__(self):
        return f"SurveyPoint({self.point_name}, N:{self.northing}, E:{self.easting}, Z:{self.elevation})"


class SurveyCSVParser:
    """
    Parses survey CSV files exported from Civil 3D or survey equipment.

    Expected CSV columns:
    - Point Name
    - Northing
    - Easting
    - Elevation
    - Point Code (optional)

    Usage:
        parser = SurveyCSVParser("path/to/survey.csv")
        points = parser.parse()
        boundary = parser.get_boundary_points()
    """

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df: Optional[pd.DataFrame] = None
        self.points: List[SurveyPoint] = []

    def parse(self) -> List[SurveyPoint]:
        """
        Parse the CSV file and extract survey points.

        Returns:
            List of SurveyPoint objects

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required columns are missing
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        try:
            # Read CSV, handling potential BOM (byte order mark)
            self.df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

            # Validate required columns
            required_columns = ['Point Name', 'Northing', 'Easting', 'Elevation']
            missing_columns = [col for col in required_columns if col not in self.df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Remove rows with NaN in critical columns
            self.df = self.df.dropna(subset=['Northing', 'Easting', 'Elevation'])

            # Convert to SurveyPoint objects
            self.points = []
            for _, row in self.df.iterrows():
                try:
                    point = SurveyPoint(
                        point_name=str(row['Point Name']),
                        northing=float(row['Northing']),
                        easting=float(row['Easting']),
                        elevation=float(row['Elevation']),
                        point_code=str(row.get('Point Code', ''))
                    )
                    self.points.append(point)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping row due to conversion error: {e}")
                    continue

            logger.info(f"Parsed {len(self.points)} survey points from {self.csv_path.name}")
            return self.points

        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise

    def get_boundary_points(self, point_code_filter: Optional[str] = None) -> List[SurveyPoint]:
        """
        Extract boundary points (e.g., points marked with specific codes).

        Args:
            point_code_filter: Filter points by code (e.g., "BOUNDARY", "EDGE")

        Returns:
            Filtered list of SurveyPoint objects
        """
        if not self.points:
            self.parse()

        if point_code_filter:
            return [p for p in self.points if point_code_filter.upper() in p.point_code.upper()]
        return self.points

    def get_statistics(self) -> Dict:
        """
        Get statistics about the survey points.

        Returns:
            Dictionary with min/max elevations, extents, etc.
        """
        if not self.points:
            self.parse()

        if not self.points:
            return {}

        northings = [p.northing for p in self.points]
        eastings = [p.easting for p in self.points]
        elevations = [p.elevation for p in self.points]

        return {
            "total_points": len(self.points),
            "northing_min": min(northings),
            "northing_max": max(northings),
            "easting_min": min(eastings),
            "easting_max": max(eastings),
            "elevation_min": min(elevations),
            "elevation_max": max(elevations),
            "elevation_range": max(elevations) - min(elevations),
        }

    def export_to_geojson(self, output_path: str) -> str:
        """
        Export survey points to GeoJSON format.

        Args:
            output_path: Path for output GeoJSON file

        Returns:
            Path to created GeoJSON file
        """
        if not self.points:
            self.parse()

        import json

        features = []
        for point in self.points:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    # NOTE: GeoJSON uses [longitude, latitude] = [easting, northing]
                    "coordinates": [point.easting, point.northing, point.elevation]
                },
                "properties": {
                    "name": point.point_name,
                    "elevation": point.elevation,
                    "code": point.point_code
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)

        logger.info(f"Exported {len(features)} points to GeoJSON: {output_path}")
        return str(output_path)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert points to pandas DataFrame.

        Returns:
            DataFrame with point data
        """
        if not self.points:
            self.parse()

        data = {
            'point_name': [p.point_name for p in self.points],
            'northing': [p.northing for p in self.points],
            'easting': [p.easting for p in self.points],
            'elevation': [p.elevation for p in self.points],
            'point_code': [p.point_code for p in self.points],
        }

        return pd.DataFrame(data)
