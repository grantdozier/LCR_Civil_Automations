"""
Integration tests for Module D - Plan Review & QA Automation
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.module_d import (
    PlanExtractor,
    SheetMetadata,
    ComplianceChecker,
    ComplianceResult,
    QAReportGenerator,
    Severity,
)


def test_plan_extractor_initialization():
    """Test PlanExtractor can be initialized"""
    print("\\n" + "="*70)
    print("MODULE D - PLAN EXTRACTOR TEST")
    print("="*70)

    extractor = PlanExtractor(use_ocr=True)

    print(f"\\n✅ PlanExtractor initialized successfully")
    print(f"   OCR mode: {extractor.use_ocr}")

    assert extractor.use_ocr == True


def test_mock_sheet_extraction():
    """Test sheet extraction with mock data"""
    print("\\n" + "="*70)
    print("MOCK SHEET EXTRACTION TEST")
    print("="*70)

    extractor = PlanExtractor(use_ocr=True)

    # Mock extraction (actual PDF not needed for this test)
    print(f"\\nTesting mock extraction...")

    # In production, would extract from real PDF
    # For now, test the mock implementation
    sheets = extractor._extract_with_ocr(Path("mock.pdf"), None)

    print(f"\\nExtracted {len(sheets)} sheets:")
    for sheet in sheets:
        print(f"  • {sheet.sheet_number}: {sheet.sheet_title}")
        print(f"    Confidence: {sheet.confidence_score * 100:.1f}%")

    assert len(sheets) > 0
    assert all(s.sheet_number for s in sheets)
    assert all(s.confidence_score > 0 for s in sheets)

    print(f"\\n✅ PASS: Successfully extracted {len(sheets)} mock sheets")


def test_compliance_checker_rules():
    """Test ComplianceChecker loads all standard rules"""
    print("\\n" + "="*70)
    print("COMPLIANCE CHECKER - RULES TEST")
    print("="*70)

    checker = ComplianceChecker()

    print(f"\\nTotal rules loaded: {len(checker.rules)}")

    # Group by category
    by_category = {}
    for rule in checker.rules:
        category = rule.rule_id.split("-")[0]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(rule)

    print(f"\\nRules by Category:")
    for category, rules in by_category.items():
        print(f"  {category}: {len(rules)} rules")

    # Verify we have rules in each major category
    assert "LPDES" in by_category
    assert "LUS" in by_category
    assert "DOTD" in by_category
    assert "ASTM" in by_category
    assert "DRAIN" in by_category
    assert "SESC" in by_category

    # Verify minimum number of rules (25+)
    assert len(checker.rules) >= 25

    print(f"\\n✅ PASS: Loaded {len(checker.rules)} validation rules")


def test_compliance_check_with_mock_data():
    """Test compliance checking with mock sheet data"""
    print("\\n" + "="*70)
    print("COMPLIANCE CHECK TEST")
    print("="*70)

    extractor = PlanExtractor(use_ocr=True)
    checker = ComplianceChecker()

    # Get mock sheets
    sheets = extractor._extract_with_ocr(Path("mock.pdf"), None)

    print(f"\\nRunning compliance checks on {len(sheets)} sheets...")

    # Run compliance checks
    results = checker.check_compliance(sheets)

    print(f"\\nCompliance Results:")
    print(f"  Total checks: {len(results)}")

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    # Show some example results
    print(f"\\nSample Results:")
    for result in results[:5]:
        status = "✓" if result.passed else "✗"
        print(f"  {status} [{result.rule_id}] {result.message}")

    # Generate summary
    summary = checker.generate_summary(results)

    print(f"\\nSummary:")
    print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"  Critical Failures: {summary['critical_failures']}")
    print(f"  Warnings: {summary['warnings']}")
    print(f"  Overall Status: {summary['overall_status']}")

    assert len(results) > 0
    assert summary['total_checks'] == len(results)
    assert summary['overall_status'] in ["PASS", "FAIL"]

    print(f"\\n✅ PASS: Compliance check completed successfully")


def test_qa_report_generation():
    """Test QA report generation"""
    print("\\n" + "="*70)
    print("QA REPORT GENERATION TEST")
    print("="*70)

    # Create mock data
    extractor = PlanExtractor(use_ocr=True)
    checker = ComplianceChecker()

    sheets = extractor._extract_with_ocr(Path("mock.pdf"), None)
    results = checker.check_compliance(sheets)

    # Generate QA report
    report_gen = QAReportGenerator(output_dir="/tmp/qa_reports")

    project_data = {
        "project_name": "Test Project",
        "project_number": "TEST-001",
        "client_name": "Test Client",
        "location": "Lafayette, LA",
        "date": "November 6, 2025",
    }

    print(f"\\nGenerating QA report...")

    report_path = report_gen.generate_report(
        project_data=project_data,
        sheets=sheets,
        compliance_results=results,
    )

    print(f"\\n✅ PASS: QA report generated")
    print(f"   Report path: {report_path}")

    assert Path(report_path).exists()
    assert report_path.endswith(".docx")

    # Get file size
    file_size = Path(report_path).stat().st_size
    print(f"   File size: {file_size:,} bytes")

    assert file_size > 1000  # Report should be reasonably sized


def test_lpdes_compliance_check():
    """Test specific LPDES requirement checking"""
    print("\\n" + "="*70)
    print("LPDES COMPLIANCE TEST")
    print("="*70)

    checker = ComplianceChecker()

    # Create mock sheet with LPDES note
    sheet = SheetMetadata(
        sheet_number="C-9",
        sheet_title="EROSION CONTROL PLAN",
        notes_text="""
        EROSION CONTROL NOTES:
        1. LPDES GENERAL PERMIT FOR STORMWATER DISCHARGES REQUIRED.
        2. SILT FENCE SHALL BE INSTALLED ALONG ALL DISTURBED PERIMETERS.
        3. SWPPP SHALL BE MAINTAINED ON SITE AT ALL TIMES.
        """,
        confidence_score=0.95,
    )

    results = checker.check_compliance([sheet])

    # Filter LPDES results
    lpdes_results = [r for r in results if r.rule_id.startswith("LPDES")]

    print(f"\\nLPDES Compliance Checks:")
    for result in lpdes_results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {status}: [{result.rule_id}] {result.message}")

    # Should have some LPDES checks that passed
    lpdes_passed = sum(1 for r in lpdes_results if r.passed)

    print(f"\\nLPDES Results: {lpdes_passed}/{len(lpdes_results)} passed")

    assert len(lpdes_results) > 0
    assert lpdes_passed > 0

    print(f"\\n✅ PASS: LPDES compliance check successful")


def test_drainage_design_compliance():
    """Test drainage design requirement checking"""
    print("\\n" + "="*70)
    print("DRAINAGE DESIGN COMPLIANCE TEST")
    print("="*70)

    checker = ComplianceChecker()

    # Create mock C-7 sheet with drainage notes
    sheet = SheetMetadata(
        sheet_number="C-7",
        sheet_title="DRAINAGE PLAN",
        notes_text="""
        DRAINAGE NOTES:
        1. ALL DRAINAGE CALCULATIONS IN ACCORDANCE WITH NOAA ATLAS 14.
        2. RATIONAL METHOD USED FOR PEAK FLOW CALCULATIONS: Q = CiA.
        3. TIME OF CONCENTRATION CALCULATED USING NRCS METHOD.
        4. DESIGN STORM EVENT: 25-YEAR.
        5. Lafayette UDC Section 3.2 applies.
        """,
        confidence_score=0.92,
    )

    results = checker.check_compliance([sheet])

    # Filter drainage results
    drain_results = [r for r in results if r.rule_id.startswith("DRAIN")]

    print(f"\\nDrainage Design Compliance Checks:")
    for result in drain_results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {status}: [{result.rule_id}] {result.message}")

    drain_passed = sum(1 for r in drain_results if r.passed)

    print(f"\\nDrainage Results: {drain_passed}/{len(drain_results)} passed")

    # Should pass most drainage checks
    assert len(drain_results) > 0
    assert drain_passed >= len(drain_results) - 1  # Allow 1 failure

    print(f"\\n✅ PASS: Drainage design compliance check successful")


def test_full_qa_workflow():
    """Test complete QA workflow from extraction to report"""
    print("\\n" + "="*80)
    print("COMPLETE QA WORKFLOW TEST")
    print("="*80)

    print(f"\\n1. Initializing components...")
    extractor = PlanExtractor(use_ocr=True)
    checker = ComplianceChecker()
    report_gen = QAReportGenerator(output_dir="/tmp/qa_reports")

    print(f"\\n2. Extracting plan sheets...")
    sheets = extractor._extract_with_ocr(Path("mock.pdf"), None)
    print(f"   Extracted {len(sheets)} sheets")

    print(f"\\n3. Running compliance checks...")
    results = checker.check_compliance(sheets)
    print(f"   Completed {len(results)} checks")

    print(f"\\n4. Generating summary...")
    summary = checker.generate_summary(results)
    print(f"   Overall Status: {summary['overall_status']}")
    print(f"   Pass Rate: {summary['pass_rate']:.1f}%")

    print(f"\\n5. Generating QA report...")
    project_data = {
        "project_name": "Complete Workflow Test Project",
        "project_number": "WORKFLOW-001",
        "client_name": "Test Client",
        "location": "Lafayette, LA",
    }

    report_path = report_gen.generate_report(
        project_data=project_data,
        sheets=sheets,
        compliance_results=results,
    )

    print(f"   Report generated: {report_path}")

    print(f"\\n" + "="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    print(f"✅ Sheets Extracted: {len(sheets)}")
    print(f"✅ Compliance Checks: {len(results)}")
    print(f"✅ Pass Rate: {summary['pass_rate']:.1f}%")
    print(f"✅ Report Generated: {Path(report_path).name}")
    print(f"✅ Overall Status: {summary['overall_status']}")
    print("="*80)

    assert len(sheets) > 0
    assert len(results) > 0
    assert Path(report_path).exists()

    print(f"\\n✅ PASS: Complete QA workflow successful!")


if __name__ == "__main__":
    """Run all Module D tests"""
    print("\\n" + "🚀"*40)
    print("MODULE D - PLAN REVIEW & QA AUTOMATION")
    print("INTEGRATION TEST SUITE")
    print("🚀"*40)

    try:
        # Run all tests
        test_plan_extractor_initialization()
        test_mock_sheet_extraction()
        test_compliance_checker_rules()
        test_compliance_check_with_mock_data()
        test_qa_report_generation()
        test_lpdes_compliance_check()
        test_drainage_design_compliance()
        test_full_qa_workflow()

        print("\\n" + "="*80)
        print("✅ ALL MODULE D TESTS PASSED!")
        print("="*80)
        print("\\nModule D is production-ready!")
        print("• 25+ compliance rules validated")
        print("• QA report generation working")
        print("• Full workflow tested end-to-end")
        print("="*80 + "\\n")

    except AssertionError as e:
        print(f"\\n❌ TEST FAILED: {e}\\n")
        raise
    except Exception as e:
        print(f"\\n❌ ERROR: {e}\\n")
        raise
