"""
Integration test for Module C - DIA Report Generator
Tests the complete workflow with real Acadiana High data
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.module_c import (
    RationalMethodCalculator,
    TimeOfConcentration,
    DIAReportGenerator,
    ExhibitGenerator,
)
from backend.services.module_b import NOAAAtlas14Parser


class TestModuleCIntegration:
    """Integration tests for Module C with real Acadiana High data"""

    def test_rational_method_acadiana_high_eda1(self):
        """
        Test Rational Method with Acadiana High E-DA1 data

        From the DIA report:
        - Area: E-DA1
        - Total Area: 13.68 acres
        - Weighted C: 0.720
        - 10-year storm, Tc=12.5 min
        """
        calc = RationalMethodCalculator()

        # Get rainfall intensity from NOAA
        noaa = NOAAAtlas14Parser()
        noaa.load_standard_lafayette_data()

        # For Tc=12.5 min, 10-year storm
        intensity = noaa.interpolate_intensity(12.5, 10)

        # Calculate peak flow: Q = CiA
        result = calc.calculate_peak_flow(
            c_value=0.720,
            intensity_in_per_hr=intensity,
            area_acres=13.68
        )

        # Verify results
        assert result["peak_flow_cfs"] > 0
        assert result["c_value"] == 0.720
        assert result["area_acres"] == 13.68
        assert result["formula"] == "Q = C × i × A"

        print(f"\n✅ E-DA1 10-year storm: Q = {result['peak_flow_cfs']:.1f} cfs")
        print(f"   C = {result['c_value']:.3f}, i = {result['intensity_in_per_hr']:.2f} in/hr, A = {result['area_acres']:.2f} ac")

    def test_time_of_concentration_methods(self):
        """Test all Tc calculation methods"""
        tc = TimeOfConcentration()

        # Test data: 500 ft flow path, 10 ft elevation change
        flow_length = 500.0
        elevation_change = 10.0

        # NRCS method
        tc_nrcs = tc.nrcs_method(flow_length, elevation_change, cn=70)
        assert 5 < tc_nrcs < 30, f"NRCS Tc out of expected range: {tc_nrcs}"

        # Kirpich method
        tc_kirpich = tc.kirpich_method(flow_length, elevation_change)
        assert 5 < tc_kirpich < 30, f"Kirpich Tc out of expected range: {tc_kirpich}"

        # FAA method
        tc_faa = tc.faa_method(flow_length, 0.70, 2.0)  # 2% slope
        assert 5 < tc_faa < 30, f"FAA Tc out of expected range: {tc_faa}"

        print(f"\n✅ Time of Concentration calculations:")
        print(f"   NRCS: {tc_nrcs:.2f} min")
        print(f"   Kirpich: {tc_kirpich:.2f} min")
        print(f"   FAA: {tc_faa:.2f} min")

    def test_multi_storm_analysis(self):
        """Test multi-storm event analysis (10/25/50/100-year)"""
        calc = RationalMethodCalculator()
        noaa = NOAAAtlas14Parser()
        noaa.load_standard_lafayette_data()

        # E-DA1 data
        c_value = 0.720
        area_acres = 13.68
        tc_minutes = 12.5

        # Get intensities for all storm events
        intensities = {
            "10-year": noaa.interpolate_intensity(tc_minutes, 10),
            "25-year": noaa.interpolate_intensity(tc_minutes, 25),
            "50-year": noaa.interpolate_intensity(tc_minutes, 50),
            "100-year": noaa.interpolate_intensity(tc_minutes, 100),
        }

        # Calculate flows
        results = calc.calculate_multi_storm(c_value, area_acres, intensities)

        # Verify all storm events calculated
        assert len(results) == 4
        for storm_event in ["10-year", "25-year", "50-year", "100-year"]:
            assert storm_event in results
            assert results[storm_event]["peak_flow_cfs"] > 0

        # Verify flows increase with return period
        q_10 = results["10-year"]["peak_flow_cfs"]
        q_25 = results["25-year"]["peak_flow_cfs"]
        q_50 = results["50-year"]["peak_flow_cfs"]
        q_100 = results["100-year"]["peak_flow_cfs"]

        assert q_10 < q_25 < q_50 < q_100, "Flow rates should increase with return period"

        print(f"\n✅ Multi-storm analysis for E-DA1:")
        for storm, result in results.items():
            print(f"   {storm}: Q = {result['peak_flow_cfs']:.1f} cfs")

    def test_accuracy_validation(self):
        """Test that calculations meet ±2% accuracy requirement"""
        calc = RationalMethodCalculator()

        # Test case: Known result
        c_value = 0.720
        intensity = 7.25
        area = 13.68
        expected_q = c_value * intensity * area  # 71.4 cfs

        result = calc.calculate_peak_flow(c_value, intensity, area)
        calculated_q = result["peak_flow_cfs"]

        # Validate accuracy
        validation = calc.validate_accuracy(
            calculated_q=calculated_q,
            expected_q=expected_q,
            tolerance_percent=2.0
        )

        assert validation["valid"], f"Accuracy validation failed: {validation}"
        assert validation["within_spec"], "Result not within ±2% specification"

        print(f"\n✅ Accuracy validation:")
        print(f"   Expected: {expected_q:.3f} cfs")
        print(f"   Calculated: {calculated_q:.3f} cfs")
        print(f"   Error: {validation['error_percent']:.2f}% (spec: ±2%)")
        print(f"   Status: {'PASS' if validation['valid'] else 'FAIL'}")

    def test_noaa_atlas_14_integration(self):
        """Test NOAA Atlas 14 data integration"""
        noaa = NOAAAtlas14Parser()
        noaa.load_standard_lafayette_data()

        # Test exact values
        i_10_10min = noaa.get_intensity(10, 10)  # 10 min, 10-year
        assert i_10_10min == 7.25, f"Expected 7.25, got {i_10_10min}"

        # Test interpolation
        i_12_10year = noaa.interpolate_intensity(12.5, 10)
        assert i_12_10year is not None
        assert 6.0 < i_12_10year < 8.0, f"Interpolated value out of range: {i_12_10year}"

        print(f"\n✅ NOAA Atlas 14 integration:")
        print(f"   10 min, 10-year: {i_10_10min:.2f} in/hr")
        print(f"   12.5 min, 10-year (interpolated): {i_12_10year:.2f} in/hr")

    def test_report_generator_initialization(self):
        """Test DIA report generator initialization"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            report_gen = DIAReportGenerator(output_dir=tmpdir)

            # Verify output directory exists
            assert Path(tmpdir).exists()
            assert report_gen.output_dir == Path(tmpdir)

            print(f"\n✅ Report generator initialized successfully")

    def test_exhibit_generator_initialization(self):
        """Test exhibit generator initialization"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            exhibit_gen = ExhibitGenerator(output_dir=tmpdir)

            # Verify output directory exists
            assert Path(tmpdir).exists()
            assert exhibit_gen.output_dir == Path(tmpdir)

            print(f"\n✅ Exhibit generator initialized successfully")

    def test_composite_flow_calculation(self):
        """Test composite flow from multiple drainage areas"""
        calc = RationalMethodCalculator()

        # Simulate 4 drainage areas (like Acadiana High)
        sub_areas = [
            {"peak_flow_cfs": 71.4, "tc_minutes": 12.5},  # E-DA1
            {"peak_flow_cfs": 54.6, "tc_minutes": 15.0},  # E-DA2
            {"peak_flow_cfs": 82.3, "tc_minutes": 18.0},  # E-DA3
            {"peak_flow_cfs": 21.2, "tc_minutes": 10.0},  # E-DA4
        ]

        result = calc.calculate_composite_flow(sub_areas)

        expected_total = sum(area["peak_flow_cfs"] for area in sub_areas)

        assert result["composite_flow_cfs"] == expected_total
        assert result["num_sub_areas"] == 4
        assert result["controlling_tc_minutes"] == 10.0  # Minimum Tc

        print(f"\n✅ Composite flow calculation:")
        print(f"   Total flow: {result['composite_flow_cfs']:.1f} cfs")
        print(f"   Number of areas: {result['num_sub_areas']}")
        print(f"   Controlling Tc: {result['controlling_tc_minutes']:.1f} min")

    def test_full_acadiana_high_simulation(self):
        """
        Full integration test simulating complete Acadiana High analysis
        Tests the entire Module C workflow
        """
        print("\n" + "="*70)
        print("FULL ACADIANA HIGH SCHOOL PROJECT SIMULATION")
        print("="*70)

        # Initialize all components
        tc_calc = TimeOfConcentration()
        rational_calc = RationalMethodCalculator()
        noaa = NOAAAtlas14Parser()
        noaa.load_standard_lafayette_data()

        # Acadiana High drainage areas (from DIA report)
        drainage_areas = [
            {
                "area_label": "E-DA1",
                "total_area_acres": 13.68,
                "impervious_area_acres": 9.85,
                "pervious_area_acres": 3.83,
                "weighted_c_value": 0.720,
                "tc_minutes": 12.5
            },
            {
                "area_label": "E-DA2",
                "total_area_acres": 15.10,
                "impervious_area_acres": 7.55,
                "pervious_area_acres": 7.55,
                "weighted_c_value": 0.500,
                "tc_minutes": 15.0
            },
            {
                "area_label": "E-DA3",
                "total_area_acres": 32.43,
                "impervious_area_acres": 13.62,
                "pervious_area_acres": 18.81,
                "weighted_c_value": 0.420,
                "tc_minutes": 18.0
            },
            {
                "area_label": "E-DA4",
                "total_area_acres": 12.10,
                "impervious_area_acres": 3.51,
                "pervious_area_acres": 8.59,
                "weighted_c_value": 0.290,
                "tc_minutes": 10.0
            }
        ]

        # Storm events to analyze
        storm_events = ["10-year", "25-year", "50-year", "100-year"]

        # Results storage
        all_results = {}

        for storm_event in storm_events:
            return_period = int(storm_event.split('-')[0])
            storm_results = []

            print(f"\n{storm_event.upper()} STORM EVENT:")
            print("-" * 70)

            for da in drainage_areas:
                # Get rainfall intensity
                intensity = noaa.interpolate_intensity(
                    da["tc_minutes"],
                    return_period
                )

                # Calculate peak flow
                flow_result = rational_calc.calculate_peak_flow(
                    c_value=da["weighted_c_value"],
                    intensity_in_per_hr=intensity,
                    area_acres=da["total_area_acres"]
                )

                storm_results.append(flow_result)

                print(f"  {da['area_label']}: "
                      f"C={da['weighted_c_value']:.3f}, "
                      f"i={intensity:.2f} in/hr, "
                      f"A={da['total_area_acres']:.2f} ac → "
                      f"Q={flow_result['peak_flow_cfs']:.1f} cfs")

            # Calculate total flow
            total_flow = sum(r["peak_flow_cfs"] for r in storm_results)
            print(f"  {'TOTAL':<6}: Q={total_flow:.1f} cfs")

            all_results[storm_event] = storm_results

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Analyzed {len(drainage_areas)} drainage areas")
        print(f"✅ Calculated flows for {len(storm_events)} storm events")
        print(f"✅ Total calculations: {len(drainage_areas) * len(storm_events)}")
        print(f"✅ All calculations completed successfully!")
        print("="*70)

        # Verify all calculations completed
        assert len(all_results) == 4
        for storm, results in all_results.items():
            assert len(results) == 4
            for result in results:
                assert result["peak_flow_cfs"] > 0


if __name__ == "__main__":
    """Run tests manually for demonstration"""
    import pytest

    # Run all tests
    pytest.main([__file__, "-v", "-s"])
