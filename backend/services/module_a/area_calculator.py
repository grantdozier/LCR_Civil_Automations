"""
Module A - Area Calculator
Calculate drainage areas, impervious/pervious split, and weighted runoff coefficients
"""
from typing import Dict, List, Tuple, Optional
from shapely.geometry import Polygon, Point
from shapely import wkt
import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

# Standard runoff coefficients (C-values) from Lafayette UDC / DOTD
# These are typical values - Module B will extract actual values from PDFs
STANDARD_C_VALUES = {
    "pavement": 0.90,
    "concrete": 0.90,
    "asphalt": 0.90,
    "roof": 0.85,
    "sidewalk": 0.85,
    "grass_flat": 0.10,  # <2% slope
    "grass_moderate": 0.15,  # 2-7% slope
    "grass_steep": 0.20,  # >7% slope
    "turf": 0.15,
    "gravel": 0.50,
    "dirt": 0.30,
}


class AreaCalculator:
    """
    Calculate drainage areas from polygon geometries.

    Accuracy requirement: ±0.5% per project specifications
    """

    SQFT_TO_ACRES = 43560.0  # Square feet per acre

    def __init__(self, precision: int = 2):
        """
        Initialize calculator.

        Args:
            precision: Decimal places for area calculations (default: 2)
        """
        self.precision = precision

    def calculate_polygon_area(self, coordinates: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        Calculate area of a polygon from coordinates.

        Args:
            coordinates: List of (x, y) tuples defining polygon vertices

        Returns:
            Dictionary with area in square feet and acres

        Raises:
            ValueError: If coordinates don't form a valid polygon
        """
        if len(coordinates) < 3:
            raise ValueError("Polygon must have at least 3 vertices")

        try:
            polygon = Polygon(coordinates)

            if not polygon.is_valid:
                # Try to fix invalid polygons
                polygon = polygon.buffer(0)

            area_sqft = abs(polygon.area)
            area_acres = area_sqft / self.SQFT_TO_ACRES

            # Round to specified precision
            area_sqft = self._round_decimal(area_sqft, self.precision)
            area_acres = self._round_decimal(area_acres, 4)  # Always 4 decimal places for acres

            logger.debug(f"Calculated area: {area_acres} acres ({area_sqft} sqft)")

            return {
                "area_sqft": area_sqft,
                "area_acres": area_acres,
                "perimeter_ft": self._round_decimal(polygon.length, self.precision),
                "centroid_x": polygon.centroid.x,
                "centroid_y": polygon.centroid.y,
            }

        except Exception as e:
            logger.error(f"Error calculating polygon area: {e}")
            raise ValueError(f"Invalid polygon geometry: {e}")

    def calculate_split_areas(
        self,
        total_polygon: List[Tuple[float, float]],
        impervious_polygons: List[List[Tuple[float, float]]] = None
    ) -> Dict[str, float]:
        """
        Calculate impervious vs. pervious areas within a drainage basin.

        Args:
            total_polygon: Coordinates of total drainage area
            impervious_polygons: List of impervious area polygons (pavement, roofs, etc.)

        Returns:
            Dictionary with total, impervious, and pervious areas
        """
        total_area = self.calculate_polygon_area(total_polygon)

        if not impervious_polygons:
            # No impervious areas defined - assume all pervious
            return {
                "total_area_sqft": total_area["area_sqft"],
                "total_area_acres": total_area["area_acres"],
                "impervious_area_sqft": 0.0,
                "impervious_area_acres": 0.0,
                "pervious_area_sqft": total_area["area_sqft"],
                "pervious_area_acres": total_area["area_acres"],
                "impervious_percentage": 0.0,
            }

        # Calculate total impervious area
        impervious_sqft = 0.0
        for imp_coords in impervious_polygons:
            imp_area = self.calculate_polygon_area(imp_coords)
            impervious_sqft += imp_area["area_sqft"]

        # Calculate pervious area (total - impervious)
        pervious_sqft = max(0, total_area["area_sqft"] - impervious_sqft)

        impervious_acres = impervious_sqft / self.SQFT_TO_ACRES
        pervious_acres = pervious_sqft / self.SQFT_TO_ACRES
        impervious_pct = (impervious_sqft / total_area["area_sqft"] * 100) if total_area["area_sqft"] > 0 else 0

        return {
            "total_area_sqft": total_area["area_sqft"],
            "total_area_acres": total_area["area_acres"],
            "impervious_area_sqft": self._round_decimal(impervious_sqft, self.precision),
            "impervious_area_acres": self._round_decimal(impervious_acres, 4),
            "pervious_area_sqft": self._round_decimal(pervious_sqft, self.precision),
            "pervious_area_acres": self._round_decimal(pervious_acres, 4),
            "impervious_percentage": self._round_decimal(impervious_pct, 1),
        }

    def _round_decimal(self, value: float, decimal_places: int) -> float:
        """Round to specified decimal places using ROUND_HALF_UP"""
        if value is None:
            return 0.0
        d = Decimal(str(value))
        rounded = d.quantize(Decimal(10) ** -decimal_places, rounding=ROUND_HALF_UP)
        return float(rounded)


class WeightedCValueCalculator:
    """
    Calculate weighted runoff coefficient (C-value) for composite land uses.

    Formula: C_weighted = (C1*A1 + C2*A2 + ... + Cn*An) / A_total

    Accuracy requirement: Exact to 3 decimal places per project specifications
    """

    def __init__(self, c_value_lookup: Dict[str, float] = None):
        """
        Initialize calculator.

        Args:
            c_value_lookup: Custom C-value lookup table (optional)
                           Defaults to STANDARD_C_VALUES
        """
        self.c_value_lookup = c_value_lookup or STANDARD_C_VALUES

    def calculate_weighted_c(self, land_use_areas: Dict[str, float]) -> Dict:
        """
        Calculate weighted runoff coefficient.

        Args:
            land_use_areas: Dictionary mapping land use type to area (sqft or acres)
                          Example: {"pavement": 100000, "grass_flat": 50000, "roof": 25000}

        Returns:
            Dictionary with weighted C-value and breakdown

        Raises:
            ValueError: If land use type not found in lookup table
        """
        if not land_use_areas:
            raise ValueError("No land use areas provided")

        total_area = sum(land_use_areas.values())

        if total_area <= 0:
            raise ValueError("Total area must be greater than zero")

        # Calculate weighted sum: Σ(Ci * Ai)
        weighted_sum = 0.0
        breakdown = {}

        for land_use, area in land_use_areas.items():
            # Get C-value from lookup table
            c_value = self.c_value_lookup.get(land_use.lower())

            if c_value is None:
                # Try to find partial match
                matched = False
                for key, val in self.c_value_lookup.items():
                    if key in land_use.lower() or land_use.lower() in key:
                        c_value = val
                        matched = True
                        break

                if not matched:
                    raise ValueError(
                        f"Land use type '{land_use}' not found in C-value lookup table. "
                        f"Available types: {list(self.c_value_lookup.keys())}"
                    )

            weighted_sum += c_value * area
            percentage = (area / total_area) * 100

            breakdown[land_use] = {
                "area": area,
                "percentage": round(percentage, 1),
                "c_value": c_value,
                "weighted_contribution": c_value * area,
            }

        # Calculate weighted C-value
        c_weighted = weighted_sum / total_area

        # Round to 3 decimal places (exact per requirements)
        c_weighted = round(c_weighted, 3)

        logger.info(f"Calculated weighted C-value: {c_weighted}")

        return {
            "weighted_c_value": c_weighted,
            "total_area": total_area,
            "breakdown": breakdown,
        }

    def calculate_from_percentages(self, land_use_percentages: Dict[str, float]) -> float:
        """
        Calculate weighted C-value from percentages.

        Args:
            land_use_percentages: Dictionary mapping land use to percentage (0-100)
                                Example: {"pavement": 60, "grass_flat": 28, "roof": 12}

        Returns:
            Weighted C-value (float)

        Raises:
            ValueError: If percentages don't sum to ~100%
        """
        total_pct = sum(land_use_percentages.values())

        if not (99.0 <= total_pct <= 101.0):  # Allow small rounding errors
            raise ValueError(f"Percentages must sum to 100%, got {total_pct}%")

        # Normalize to ensure exact 100%
        normalized_pct = {k: (v / total_pct) for k, v in land_use_percentages.items()}

        # Calculate weighted sum
        c_weighted = 0.0
        for land_use, pct in normalized_pct.items():
            c_value = self.c_value_lookup.get(land_use.lower())

            if c_value is None:
                raise ValueError(
                    f"Land use type '{land_use}' not found in C-value lookup table"
                )

            c_weighted += c_value * pct

        # Round to 3 decimal places
        return round(c_weighted, 3)

    def add_custom_c_value(self, land_use: str, c_value: float):
        """
        Add or update a custom C-value.

        Args:
            land_use: Land use type name
            c_value: Runoff coefficient (0.0 to 1.0)

        Raises:
            ValueError: If C-value is out of valid range
        """
        if not (0.0 <= c_value <= 1.0):
            raise ValueError(f"C-value must be between 0.0 and 1.0, got {c_value}")

        self.c_value_lookup[land_use.lower()] = c_value
        logger.info(f"Added custom C-value: {land_use} = {c_value}")
