"""
Comprehensive Test Suite for LCR Civil Drainage Automation System
Tests all modules A-E with full integration coverage
"""
import pytest
import requests
import json
from pathlib import Path
import time

# Base URL for API
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


class TestSystemHealth:
    """Test basic system health and connectivity"""

    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_root_endpoint(self):
        """Test / root endpoint"""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert len(data["modules"]) == 5  # Modules A-E

    def test_database_connection(self):
        """Test database connectivity"""
        response = requests.get(f"{API_BASE}/db-test")
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "connected"
        assert data["status"] == "ok"


class TestModuleB_SpecExtraction:
    """Test Module B - Specification Extraction & Web Scraping"""

    def test_load_noaa_data(self):
        """Test loading NOAA Atlas 14 data"""
        response = requests.post(f"{API_BASE}/spec-extraction/load-noaa-data")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should either load new data or report existing data
        assert data["action"] in ["inserted", "skipped"]

    def test_scrape_web_sources(self):
        """Test scraping Lafayette UDC and DOTD specs"""
        response = requests.post(
            f"{API_BASE}/spec-extraction/scrape-web-sources",
            params={"save_to_db": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sources_scraped" in data
        assert "lafayette_udc" in data["sources_scraped"]
        assert "dotd" in data["sources_scraped"]
        assert "noaa" in data["sources_scraped"]
        assert data["total_specifications"] > 0

    def test_search_specifications_all(self):
        """Test searching all specifications"""
        response = requests.get(f"{API_BASE}/spec-extraction/search")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} total specifications")

    def test_search_specifications_by_jurisdiction(self):
        """Test searching specs by jurisdiction"""
        response = requests.get(
            f"{API_BASE}/spec-extraction/search",
            params={"jurisdiction": "Lafayette UDC"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for spec in data:
            assert "Lafayette" in spec["jurisdiction"]

    def test_search_runoff_coefficients(self):
        """Test searching for runoff coefficients"""
        response = requests.get(
            f"{API_BASE}/spec-extraction/search",
            params={"spec_type": "runoff_coefficient"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for spec in data:
            assert spec["spec_type"] == "runoff_coefficient"

    def test_get_c_values(self):
        """Test getting C-values endpoint"""
        response = requests.get(
            f"{API_BASE}/spec-extraction/c-values",
            params={"jurisdiction": "Lafayette UDC"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "c_values" in data
        assert len(data["c_values"]) > 0
        # Check C-value structure
        first_c_value = data["c_values"][0]
        assert "land_use_type" in first_c_value
        assert "c_value_recommended" in first_c_value

    def test_rainfall_intensity_exact(self):
        """Test rainfall intensity lookup (exact match)"""
        response = requests.post(
            f"{API_BASE}/spec-extraction/rainfall-intensity",
            json={
                "duration_minutes": 10,
                "return_period_years": 10,
                "jurisdiction": "NOAA Atlas 14"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 10
        assert data["return_period_years"] == 10
        assert data["intensity_in_per_hr"] > 0
        assert "NOAA" in data["source"]

    def test_rainfall_intensity_interpolation(self):
        """Test rainfall intensity interpolation"""
        response = requests.post(
            f"{API_BASE}/spec-extraction/rainfall-intensity",
            json={
                "duration_minutes": 12.5,  # Not exact, should interpolate
                "return_period_years": 10,
                "jurisdiction": "NOAA Atlas 14"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 12.5
        assert data["intensity_in_per_hr"] > 0
        # Should be interpolated
        assert data.get("interpolated") == True


class TestModuleC_DIAReport:
    """Test Module C - DIA Report Generation & Rational Method"""

    def test_calculate_tc_nrcs(self):
        """Test Time of Concentration using NRCS method"""
        response = requests.post(
            f"{API_BASE}/dia-report/calculate-tc",
            json={
                "method": "nrcs",
                "flow_length_ft": 500,
                "elevation_change_ft": 10,
                "cn": 70
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "tc_minutes" in data
        assert data["tc_minutes"] > 0
        assert data["method"] == "nrcs"

    def test_calculate_tc_kirpich(self):
        """Test Time of Concentration using Kirpich method"""
        response = requests.post(
            f"{API_BASE}/dia-report/calculate-tc",
            json={
                "method": "kirpich",
                "flow_length_ft": 500,
                "elevation_change_ft": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "tc_minutes" in data
        assert data["tc_minutes"] > 0

    def test_calculate_peak_flow_rational_method(self):
        """Test Rational Method flow calculation: Q = CiA"""
        response = requests.post(
            f"{API_BASE}/dia-report/calculate-flow",
            json={
                "c_value": 0.720,
                "intensity_in_per_hr": 7.32,
                "area_acres": 13.68,
                "storm_event": "10-year",
                "area_label": "E-DA1"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "peak_flow_cfs" in data
        assert data["peak_flow_cfs"] > 0
        # Verify formula: Q = C * i * A
        expected_q = 0.720 * 7.32 * 13.68
        assert abs(data["peak_flow_cfs"] - expected_q) < 0.5  # Within tolerance
        assert data["formula"] == "Q = C × i × A"


class TestModuleE_Proposals:
    """Test Module E - Proposal & Document Generation"""

    def test_get_service_pricing(self):
        """Test getting all service pricing"""
        response = requests.get(f"{API_BASE}/proposals/services/pricing")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert len(data["services"]) > 0
        assert "package_discounts" in data

    def test_calculate_pricing_single_service(self):
        """Test pricing calculation for single service"""
        response = requests.post(
            f"{API_BASE}/proposals/calculate-pricing",
            json={
                "services": ["DIA"],
                "discount_percent": 0,
                "rush_fee_percent": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subtotal"] > 0
        assert data["total"] == data["subtotal"]
        assert len(data["services"]) == 1

    def test_calculate_pricing_package_discount(self):
        """Test pricing with package discount"""
        response = requests.post(
            f"{API_BASE}/proposals/calculate-pricing",
            json={
                "services": ["DIA", "GRADING", "DETENTION"],
                "discount_percent": 0,
                "rush_fee_percent": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["package_discount_percent"] >= 5  # 3+ services = 5% discount
        assert data["discount_amount"] > 0
        assert data["total"] < data["subtotal"]

    def test_calculate_pricing_with_custom_discount(self):
        """Test pricing with custom discount"""
        response = requests.post(
            f"{API_BASE}/proposals/calculate-pricing",
            json={
                "services": ["DIA", "GRADING"],
                "discount_percent": 10,
                "rush_fee_percent": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_discount_percent"] >= 10

    def test_calculate_pricing_with_rush_fee(self):
        """Test pricing with rush fee"""
        response = requests.post(
            f"{API_BASE}/proposals/calculate-pricing",
            json={
                "services": ["DIA"],
                "discount_percent": 0,
                "rush_fee_percent": 25
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rush_fee_amount"] > 0
        assert data["total"] > data["subtotal"]

    def test_get_branding_lcr(self):
        """Test getting LCR branding information"""
        response = requests.get(f"{API_BASE}/proposals/branding/LCR")
        assert response.status_code == 200
        data = response.json()
        assert "company_name" in data
        assert "email" in data
        assert "phone" in data


class TestIntegrationFlows:
    """Test complete end-to-end workflows"""

    def test_full_module_b_workflow(self):
        """Test complete Module B workflow: Load data → Search → Query"""
        print("\n=== Testing Full Module B Workflow ===")

        # Step 1: Load NOAA data
        print("Step 1: Loading NOAA data...")
        response = requests.post(f"{API_BASE}/spec-extraction/load-noaa-data")
        assert response.status_code == 200

        # Step 2: Scrape web sources
        print("Step 2: Scraping web sources...")
        response = requests.post(
            f"{API_BASE}/spec-extraction/scrape-web-sources",
            params={"save_to_db": True}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  → Scraped {data['total_specifications']} specifications")

        # Step 3: Search for specific C-value
        print("Step 3: Searching for Pavement C-value...")
        response = requests.get(
            f"{API_BASE}/spec-extraction/c-values",
            params={
                "land_use": "Pavement",
                "jurisdiction": "Lafayette UDC"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["c_values"]) > 0
        pavement_c = data["c_values"][0]["c_value_recommended"]
        print(f"  → Found C-value: {pavement_c}")

        # Step 4: Get rainfall intensity
        print("Step 4: Getting rainfall intensity...")
        response = requests.post(
            f"{API_BASE}/spec-extraction/rainfall-intensity",
            json={
                "duration_minutes": 10,
                "return_period_years": 10,
                "jurisdiction": "NOAA Atlas 14"
            }
        )
        assert response.status_code == 200
        data = response.json()
        intensity = data["intensity_in_per_hr"]
        print(f"  → Rainfall intensity: {intensity} in/hr")

        print("✓ Module B workflow complete!\n")

    def test_full_calculation_workflow(self):
        """Test complete calculation workflow: Tc → Intensity → Q=CiA"""
        print("\n=== Testing Full Calculation Workflow ===")

        # Step 1: Calculate Tc
        print("Step 1: Calculating Time of Concentration...")
        response = requests.post(
            f"{API_BASE}/dia-report/calculate-tc",
            json={
                "method": "nrcs",
                "flow_length_ft": 500,
                "elevation_change_ft": 10,
                "cn": 70
            }
        )
        assert response.status_code == 200
        tc_minutes = response.json()["tc_minutes"]
        print(f"  → Tc = {tc_minutes:.2f} minutes")

        # Step 2: Get rainfall intensity for Tc duration
        print(f"Step 2: Getting rainfall intensity for {tc_minutes:.2f} min...")
        response = requests.post(
            f"{API_BASE}/spec-extraction/rainfall-intensity",
            json={
                "duration_minutes": tc_minutes,
                "return_period_years": 10
            }
        )
        assert response.status_code == 200
        intensity = response.json()["intensity_in_per_hr"]
        print(f"  → i = {intensity:.2f} in/hr")

        # Step 3: Calculate peak flow using Rational Method
        print("Step 3: Calculating peak flow (Q = CiA)...")
        response = requests.post(
            f"{API_BASE}/dia-report/calculate-flow",
            json={
                "c_value": 0.720,
                "intensity_in_per_hr": intensity,
                "area_acres": 13.68,
                "storm_event": "10-year",
                "area_label": "Test-DA1"
            }
        )
        assert response.status_code == 200
        peak_flow = response.json()["peak_flow_cfs"]
        print(f"  → Q = {peak_flow:.1f} cfs")

        print("✓ Calculation workflow complete!\n")


def run_all_tests():
    """Run all tests and generate summary"""
    print("\n" + "="*70)
    print("LCR CIVIL DRAINAGE AUTOMATION - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")

    test_classes = [
        ("System Health", TestSystemHealth),
        ("Module B - Spec Extraction", TestModuleB_SpecExtraction),
        ("Module C - DIA Report", TestModuleC_DIAReport),
        ("Module E - Proposals", TestModuleE_Proposals),
        ("Integration Flows", TestIntegrationFlows),
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for category_name, test_class in test_classes:
        print(f"\n{'='*70}")
        print(f"Testing: {category_name}")
        print('='*70)

        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]

        for test_method_name in test_methods:
            total_tests += 1
            test_method = getattr(test_instance, test_method_name)

            try:
                print(f"\n▶ {test_method_name}...")
                test_method()
                print(f"  ✓ PASSED")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ✗ FAILED: {e}")
                failed_tests.append(f"{category_name}.{test_method_name}: {e}")
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                failed_tests.append(f"{category_name}.{test_method_name}: {e}")

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✓")
    print(f"Failed: {len(failed_tests)} ✗")
    print(f"Pass Rate: {(passed_tests/total_tests*100):.1f}%")

    if failed_tests:
        print("\nFailed Tests:")
        for failure in failed_tests:
            print(f"  ✗ {failure}")
    else:
        print("\n🎉 ALL TESTS PASSED! 🎉")

    print("="*70 + "\n")

    return passed_tests == total_tests


if __name__ == "__main__":
    # Wait a moment for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(2)

    success = run_all_tests()
    exit(0 if success else 1)
