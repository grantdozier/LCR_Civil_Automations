"""
Module C - Rational Method Calculator
Implements Q = CiA for drainage flow calculations
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import math
import logging

logger = logging.getLogger(__name__)


class TimeOfConcentration:
    """
    Calculate Time of Concentration (Tc) using various methods.

    Supported methods:
    - NRCS (Natural Resources Conservation Service) - formerly SCS
    - Kirpich Formula
    - FAA (Federal Aviation Administration) method
    - Manning's Kinematic method
    """

    @staticmethod
    def nrcs_method(
        flow_length_ft: float,
        elevation_change_ft: float,
        cn: float = 70.0
    ) -> float:
        """
        Calculate Tc using NRCS (SCS) method.

        Formula: Tc = (L^0.8 * (1000/CN - 9)^0.7) / (1140 * S^0.5)

        Args:
            flow_length_ft: Flow path length in feet
            elevation_change_ft: Elevation change along flow path
            cn: Curve Number (default 70 for typical urban conditions)

        Returns:
            Time of Concentration in minutes

        Raises:
            ValueError: If inputs are invalid
        """
        if flow_length_ft <= 0:
            raise ValueError("Flow length must be positive")

        if elevation_change_ft <= 0:
            raise ValueError("Elevation change must be positive")

        if not (30 <= cn <= 100):
            raise ValueError("Curve Number must be between 30 and 100")

        slope = elevation_change_ft / flow_length_ft

        # NRCS formula
        numerator = (flow_length_ft ** 0.8) * ((1000 / cn - 9) ** 0.7)
        denominator = 1140 * (slope ** 0.5)

        tc_hours = numerator / denominator
        tc_minutes = tc_hours * 60

        logger.debug(
            f"NRCS Tc: L={flow_length_ft}ft, ΔH={elevation_change_ft}ft, "
            f"CN={cn}, Tc={tc_minutes:.2f} min"
        )

        return round(tc_minutes, 2)

    @staticmethod
    def kirpich_method(
        flow_length_ft: float,
        elevation_change_ft: float
    ) -> float:
        """
        Calculate Tc using Kirpich formula.

        Formula: Tc = 0.0078 * L^0.77 * S^-0.385

        Where:
        - Tc = time of concentration (minutes)
        - L = flow length (feet)
        - S = slope (ft/ft)

        Args:
            flow_length_ft: Flow path length in feet
            elevation_change_ft: Elevation change in feet

        Returns:
            Time of Concentration in minutes
        """
        if flow_length_ft <= 0 or elevation_change_ft <= 0:
            raise ValueError("Flow length and elevation change must be positive")

        slope = elevation_change_ft / flow_length_ft

        # Kirpich formula (converts from hours to minutes)
        tc_minutes = 0.0078 * (flow_length_ft ** 0.77) * (slope ** -0.385)

        logger.debug(
            f"Kirpich Tc: L={flow_length_ft}ft, S={slope:.6f}, "
            f"Tc={tc_minutes:.2f} min"
        )

        return round(tc_minutes, 2)

    @staticmethod
    def faa_method(
        flow_length_ft: float,
        runoff_coefficient: float,
        slope_percent: float
    ) -> float:
        """
        Calculate Tc using FAA (Federal Aviation Administration) method.

        Formula: Tc = (1.8 * (1.1 - C) * L^0.5) / (S^1/3)

        Where:
        - Tc = time of concentration (minutes)
        - C = runoff coefficient
        - L = flow length (feet)
        - S = slope (%)

        Args:
            flow_length_ft: Flow path length in feet
            runoff_coefficient: Runoff coefficient (0.0 to 1.0)
            slope_percent: Slope in percent (e.g., 2.5 for 2.5%)

        Returns:
            Time of Concentration in minutes
        """
        if not (0.0 <= runoff_coefficient <= 1.0):
            raise ValueError("Runoff coefficient must be between 0.0 and 1.0")

        if slope_percent <= 0:
            raise ValueError("Slope must be positive")

        # FAA formula
        tc_minutes = (1.8 * (1.1 - runoff_coefficient) * (flow_length_ft ** 0.5)) / (slope_percent ** (1/3))

        logger.debug(
            f"FAA Tc: L={flow_length_ft}ft, C={runoff_coefficient}, "
            f"S={slope_percent}%, Tc={tc_minutes:.2f} min"
        )

        return round(tc_minutes, 2)

    @staticmethod
    def manning_kinematic(
        flow_length_ft: float,
        mannings_n: float,
        slope: float,
        flow_depth_ft: float
    ) -> float:
        """
        Calculate Tc using Manning's kinematic wave method.

        Formula: Tc = (0.007 * n * L) / (S^0.5 * d^0.67)

        Args:
            flow_length_ft: Flow path length in feet
            mannings_n: Manning's roughness coefficient
            slope: Slope (ft/ft)
            flow_depth_ft: Flow depth in feet

        Returns:
            Time of Concentration in minutes
        """
        # Manning's kinematic formula (result in hours, convert to minutes)
        tc_hours = (0.007 * mannings_n * flow_length_ft) / ((slope ** 0.5) * (flow_depth_ft ** 0.67))
        tc_minutes = tc_hours * 60

        logger.debug(
            f"Manning Tc: L={flow_length_ft}ft, n={mannings_n}, "
            f"S={slope:.6f}, Tc={tc_minutes:.2f} min"
        )

        return round(tc_minutes, 2)


class RationalMethodCalculator:
    """
    Calculate peak runoff using the Rational Method: Q = CiA

    Where:
    - Q = peak flow rate (cubic feet per second, cfs)
    - C = weighted runoff coefficient (dimensionless)
    - i = rainfall intensity (inches per hour)
    - A = drainage area (acres)

    Accuracy requirement: ±2% per project specifications
    """

    def __init__(self, precision: int = 3):
        """
        Initialize calculator.

        Args:
            precision: Decimal places for flow calculations (default: 3)
        """
        self.precision = precision

    def calculate_peak_flow(
        self,
        c_value: float,
        intensity_in_per_hr: float,
        area_acres: float
    ) -> Dict:
        """
        Calculate peak flow using Rational Method: Q = CiA

        Args:
            c_value: Weighted runoff coefficient (0.0 to 1.0)
            intensity_in_per_hr: Rainfall intensity in inches per hour
            area_acres: Drainage area in acres

        Returns:
            Dictionary with:
            - peak_flow_cfs: Peak flow in cubic feet per second
            - c_value: Runoff coefficient used
            - intensity: Rainfall intensity used
            - area: Drainage area used
            - formula: "Q = C × i × A"

        Raises:
            ValueError: If inputs are out of valid range
        """
        # Validate inputs
        if not (0.0 <= c_value <= 1.0):
            raise ValueError(f"C-value must be between 0.0 and 1.0, got {c_value}")

        if intensity_in_per_hr <= 0:
            raise ValueError(f"Rainfall intensity must be positive, got {intensity_in_per_hr}")

        if area_acres <= 0:
            raise ValueError(f"Drainage area must be positive, got {area_acres}")

        # Rational Method: Q = CiA
        peak_flow = c_value * intensity_in_per_hr * area_acres

        # Round to specified precision
        peak_flow = self._round_decimal(peak_flow, self.precision)

        logger.info(
            f"Rational Method: Q = {c_value:.3f} × {intensity_in_per_hr:.4f} × {area_acres:.4f} = {peak_flow:.3f} cfs"
        )

        return {
            "peak_flow_cfs": peak_flow,
            "c_value": c_value,
            "intensity_in_per_hr": intensity_in_per_hr,
            "area_acres": area_acres,
            "formula": "Q = C × i × A",
            "method": "Rational Method",
        }

    def calculate_multi_storm(
        self,
        c_value: float,
        area_acres: float,
        intensities: Dict[str, float]
    ) -> Dict[str, Dict]:
        """
        Calculate peak flows for multiple storm events.

        Args:
            c_value: Weighted runoff coefficient
            area_acres: Drainage area in acres
            intensities: Dictionary mapping storm event to intensity
                        Example: {
                            "10-year": 7.25,
                            "25-year": 8.65,
                            "50-year": 9.82,
                            "100-year": 11.05
                        }

        Returns:
            Dictionary mapping storm event to flow results
        """
        results = {}

        for storm_event, intensity in intensities.items():
            result = self.calculate_peak_flow(c_value, intensity, area_acres)
            result["storm_event"] = storm_event
            results[storm_event] = result

        logger.info(f"Calculated flows for {len(results)} storm events")

        return results

    def calculate_composite_flow(
        self,
        sub_area_flows: List[Dict]
    ) -> Dict:
        """
        Calculate composite peak flow from multiple sub-areas.

        For areas with different Tc values, use the weighted method or
        peak flow addition method.

        Args:
            sub_area_flows: List of sub-area flow dictionaries
                           Each should have: peak_flow_cfs, tc_minutes

        Returns:
            Dictionary with composite flow information
        """
        if not sub_area_flows:
            raise ValueError("No sub-area flows provided")

        # Simple method: sum all peak flows (conservative)
        total_flow = sum(flow["peak_flow_cfs"] for flow in sub_area_flows)

        # Get minimum Tc (controls composite behavior)
        min_tc = min(flow.get("tc_minutes", 0) for flow in sub_area_flows)

        logger.info(
            f"Composite flow: {total_flow:.3f} cfs from {len(sub_area_flows)} sub-areas, "
            f"Tc={min_tc:.2f} min"
        )

        return {
            "composite_flow_cfs": self._round_decimal(total_flow, self.precision),
            "num_sub_areas": len(sub_area_flows),
            "controlling_tc_minutes": min_tc,
            "method": "Peak Flow Summation",
        }

    def adjust_for_detention(
        self,
        pre_dev_flow_cfs: float,
        post_dev_flow_cfs: float,
        detention_target_factor: float = 1.0
    ) -> Dict:
        """
        Calculate required detention volume to meet target.

        Args:
            pre_dev_flow_cfs: Pre-development peak flow
            post_dev_flow_cfs: Post-development peak flow
            detention_target_factor: Target post/pre ratio (default: 1.0 = match pre-dev)

        Returns:
            Dictionary with detention requirements
        """
        target_flow = pre_dev_flow_cfs * detention_target_factor
        reduction_required = max(0, post_dev_flow_cfs - target_flow)

        increase_percent = ((post_dev_flow_cfs - pre_dev_flow_cfs) / pre_dev_flow_cfs * 100) if pre_dev_flow_cfs > 0 else 0

        return {
            "pre_development_flow_cfs": pre_dev_flow_cfs,
            "post_development_flow_cfs": post_dev_flow_cfs,
            "target_flow_cfs": target_flow,
            "reduction_required_cfs": self._round_decimal(reduction_required, self.precision),
            "flow_increase_percent": round(increase_percent, 1),
            "detention_required": reduction_required > 0,
        }

    def _round_decimal(self, value: float, decimal_places: int) -> float:
        """Round to specified decimal places using ROUND_HALF_UP"""
        if value is None:
            return 0.0
        d = Decimal(str(value))
        rounded = d.quantize(Decimal(10) ** -decimal_places, rounding=ROUND_HALF_UP)
        return float(rounded)

    def validate_accuracy(
        self,
        calculated_q: float,
        expected_q: float,
        tolerance_percent: float = 2.0
    ) -> Dict:
        """
        Validate calculated flow against expected value.

        Per project specs: Q calculation accuracy must be ±2%

        Args:
            calculated_q: Calculated peak flow
            expected_q: Expected peak flow
            tolerance_percent: Acceptable tolerance (default: 2.0%)

        Returns:
            Dictionary with validation results
        """
        if expected_q == 0:
            return {
                "valid": False,
                "error": "Expected flow is zero",
            }

        error_percent = abs((calculated_q - expected_q) / expected_q * 100)
        is_valid = error_percent <= tolerance_percent

        return {
            "valid": is_valid,
            "calculated_q": calculated_q,
            "expected_q": expected_q,
            "error_percent": round(error_percent, 2),
            "tolerance_percent": tolerance_percent,
            "within_spec": is_valid,
        }
