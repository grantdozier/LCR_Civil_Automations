"""
Integration tests for Module E - Proposal & Document Automation
"""
import sys
from pathlib import Path
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.module_e import (
    ProposalGenerator,
    ProposalData,
    PricingCalculator,
    CoverLetterGenerator,
    SubmittalPackage,
    SubmittalDocument,
    TemplateManager,
    BrandingAssets,
)


def test_pricing_calculator():
    """Test pricing calculation for module combinations"""
    print("\\n" + "="*70)
    print("MODULE E - PRICING CALCULATOR TEST")
    print("="*70)

    calculator = PricingCalculator()

    # Test 1: Single module (no discount)
    print(f"\\nTest 1: Single Module (Module C)")
    result = calculator.calculate_total(["C"])

    print(f"  Subtotal: ${result['subtotal']:,.2f}")
    print(f"  Bundle Discount: {result['bundle_discount_percent']:.0f}%")
    print(f"  Total: ${result['total']:,.2f}")
    print(f"  Estimated Days: {result['estimated_days']}")

    assert result['subtotal'] == 12000.0
    assert result['bundle_discount_percent'] == 0.0
    assert result['total'] == 12000.0

    # Test 2: Three modules (5% discount)
    print(f"\\nTest 2: Three Modules (A, C, D) - 5% Bundle Discount")
    result = calculator.calculate_total(["A", "C", "D"])

    print(f"  Subtotal: ${result['subtotal']:,.2f}")
    print(f"  Bundle Discount: {result['bundle_discount_percent']:.0f}%")
    print(f"  Discount Amount: -${result['discount_amount']:,.2f}")
    print(f"  Total: ${result['total']:,.2f}")

    assert result['subtotal'] == 29000.0  # 7500 + 12000 + 9500
    assert result['bundle_discount_percent'] == 5.0
    assert result['total'] == 27550.0  # 29000 - 5%

    # Test 3: All modules (15% discount)
    print(f"\\nTest 3: All Modules (A, B, C, D, E) - 15% Bundle Discount")
    result = calculator.calculate_total(["A", "B", "C", "D", "E"])

    print(f"  Subtotal: ${result['subtotal']:,.2f}")
    print(f"  Bundle Discount: {result['bundle_discount_percent']:.0f}%")
    print(f"  Discount Amount: -${result['discount_amount']:,.2f}")
    print(f"  Total: ${result['total']:,.2f}")
    print(f"  Estimated Days: {result['estimated_days']}")

    assert result['subtotal'] == 42000.0  # Sum of all modules
    assert result['bundle_discount_percent'] == 15.0
    assert result['total'] == 35700.0  # 42000 - 15%

    # Test 4: Custom discount + rush fee
    print(f"\\nTest 4: Two Modules with Custom Discount and Rush Fee")
    result = calculator.calculate_total(
        modules=["A", "C"],
        discount_percent=Decimal("10"),
        rush_fee_percent=Decimal("20")
    )

    print(f"  Subtotal: ${result['subtotal']:,.2f}")
    print(f"  Custom Discount: {result['custom_discount_percent']:.0f}%")
    print(f"  Discount Amount: -${result['discount_amount']:,.2f}")
    print(f"  Discounted Subtotal: ${result['discounted_subtotal']:,.2f}")
    print(f"  Rush Fee (20%): +${result['rush_fee_amount']:,.2f}")
    print(f"  Total: ${result['total']:,.2f}")

    assert result['subtotal'] == 19500.0
    assert result['custom_discount_percent'] == 10.0

    print(f"\\n✅ PASS: Pricing calculator working correctly")


def test_proposal_generation():
    """Test proposal document generation"""
    print("\\n" + "="*70)
    print("PROPOSAL GENERATION TEST")
    print("="*70)

    # Create proposal data
    proposal_data = ProposalData(
        client_name="Acadiana High School",
        client_contact="John Smith, Facilities Director",
        client_email="jsmith@acadiana.edu",
        project_name="Campus Drainage Improvements",
        project_location="Lafayette, Louisiana",
        project_description=(
            "Comprehensive drainage analysis and improvements for the Acadiana High School "
            "campus, including automated area calculations, DIA report generation, and "
            "plan review services."
        ),
        modules_requested=["A", "C", "D"],
        custom_scope=[
            "Site visit and field verification",
            "Coordination with Lafayette Utilities System",
        ],
        discount_percent=Decimal("0"),
        rush_fee_percent=Decimal("0"),
        proposal_valid_days=30,
        prepared_by="Grant Dozier, PE",
        company="LCR",
    )

    print(f"\\nGenerating proposal for {proposal_data.client_name}...")
    print(f"  Modules: {', '.join(proposal_data.modules_requested)}")

    # Generate proposal
    generator = ProposalGenerator(output_dir="/tmp/proposals")
    proposal_path = generator.generate_proposal(proposal_data)

    print(f"\\n✅ PASS: Proposal generated")
    print(f"   File: {proposal_path}")

    assert Path(proposal_path).exists()
    assert proposal_path.endswith(".docx")

    # Check file size
    file_size = Path(proposal_path).stat().st_size
    print(f"   File size: {file_size:,} bytes")

    assert file_size > 10000  # Proposal should be substantial

    print(f"\\n✅ PASS: Proposal generation successful")


def test_cover_letter_generation():
    """Test cover letter generation"""
    print("\\n" + "="*70)
    print("COVER LETTER GENERATION TEST")
    print("="*70)

    # Create submittal data
    documents = [
        SubmittalDocument(
            document_type="DIA Report",
            description="Drainage Impact Analysis Report",
            filename="DIA_Report_Acadiana_High.pdf",
            page_count=58,
            revision="Rev 1",
        ),
        SubmittalDocument(
            document_type="Drainage Plans",
            description="Plan Sheets C-1 through C-9",
            filename="Drainage_Plans.pdf",
            page_count=9,
        ),
        SubmittalDocument(
            document_type="QA Report",
            description="Quality Assurance Review Report",
            filename="QA_Report.pdf",
            page_count=15,
        ),
    ]

    submittal = SubmittalPackage(
        project_name="Acadiana High School Drainage",
        project_number="2024-001",
        client_name="Lafayette Parish School Board",
        client_address="113 Chaplin Drive\\nLafayette, LA 70508",
        client_contact="Jane Doe, PE",
        subject="Drainage Impact Analysis Submittal",
        documents=documents,
        purpose="Plan Review and Approval",
        special_instructions=(
            "Please review in accordance with Lafayette UDC Section 3.2. "
            "Contact our office with any questions."
        ),
        prepared_by="Grant Dozier, PE",
        company="LCR",
    )

    print(f"\\nGenerating cover letter for {submittal.project_name}...")
    print(f"  Documents: {len(documents)}")
    print(f"  Purpose: {submittal.purpose}")

    # Generate cover letter
    generator = CoverLetterGenerator(output_dir="/tmp/cover_letters")
    letter_path = generator.generate_cover_letter(
        submittal=submittal,
        letter_type="submittal"
    )

    print(f"\\n✅ PASS: Cover letter generated")
    print(f"   File: {letter_path}")

    assert Path(letter_path).exists()
    assert letter_path.endswith(".docx")

    print(f"\\n✅ PASS: Cover letter generation successful")


def test_transmittal_form_generation():
    """Test transmittal form generation"""
    print("\\n" + "="*70)
    print("TRANSMITTAL FORM GENERATION TEST")
    print("="*70)

    documents = [
        SubmittalDocument(
            document_type="Site Plans",
            description="Civil Site Plans",
            filename="Site_Plans.pdf",
            page_count=12,
        ),
    ]

    submittal = SubmittalPackage(
        project_name="Test Project",
        project_number="TEST-001",
        client_name="Test Client",
        client_address="123 Main St\\nLafayette, LA 70508",
        client_contact="Test Contact",
        subject="Plan Submittal",
        documents=documents,
        prepared_by="Grant Dozier, PE",
        company="LCR",
    )

    print(f"\\nGenerating transmittal form...")

    generator = CoverLetterGenerator(output_dir="/tmp/transmittals")
    form_path = generator.generate_transmittal_form(submittal)

    print(f"\\n✅ PASS: Transmittal form generated")
    print(f"   File: {form_path}")

    assert Path(form_path).exists()

    print(f"\\n✅ PASS: Transmittal form generation successful")


def test_template_manager():
    """Test template manager and branding"""
    print("\\n" + "="*70)
    print("TEMPLATE MANAGER TEST")
    print("="*70)

    manager = TemplateManager()

    # Test LCR branding
    print(f"\\nTest 1: LCR Branding")
    lcr_branding = manager.get_branding("LCR")

    print(f"  Company: {lcr_branding.company_name}")
    print(f"  Tagline: {lcr_branding.tagline}")
    print(f"  Email: {lcr_branding.email}")
    print(f"  Primary Color: RGB{lcr_branding.primary_color}")

    assert lcr_branding.company_name == "LCR & Company"
    assert lcr_branding.email == "info@lcrcompany.com"

    # Test Dozier branding
    print(f"\\nTest 2: Dozier Tech Branding")
    dozier_branding = manager.get_branding("Dozier")

    print(f"  Company: {dozier_branding.company_name}")
    print(f"  Tagline: {dozier_branding.tagline}")
    print(f"  Email: {dozier_branding.email}")

    assert dozier_branding.company_name == "Dozier Tech"
    assert dozier_branding.email == "grant@doziertech.com"

    # Test combined branding
    print(f"\\nTest 3: Combined Branding")
    both_branding = manager.get_branding("Both")

    print(f"  Company: {both_branding.company_name}")
    print(f"  Tagline: {both_branding.tagline}")

    assert "LCR" in both_branding.company_name
    assert "Dozier" in both_branding.company_name

    print(f"\\n✅ PASS: Template manager working correctly")


def test_full_proposal_workflow():
    """Test complete proposal workflow"""
    print("\\n" + "="*80)
    print("COMPLETE PROPOSAL WORKFLOW TEST")
    print("="*80)

    print(f"\\n1. Calculating pricing...")
    calculator = PricingCalculator()
    pricing = calculator.calculate_total(
        modules=["A", "B", "C"],
        discount_percent=Decimal("0"),
        rush_fee_percent=Decimal("0")
    )

    print(f"   Modules: A, B, C")
    print(f"   Subtotal: ${pricing['subtotal']:,.2f}")
    print(f"   Discount: {pricing['bundle_discount_percent']:.0f}%")
    print(f"   Total: ${pricing['total']:,.2f}")
    print(f"   Estimated: {pricing['estimated_days']} days")

    print(f"\\n2. Preparing proposal data...")
    proposal_data = ProposalData(
        client_name="Complete Workflow Test Client",
        client_contact="Test Contact, PE",
        client_email="test@client.com",
        project_name="Full Workflow Test Project",
        project_location="Lafayette, LA",
        project_description="Test project for complete workflow validation",
        modules_requested=["A", "B", "C"],
        prepared_by="Grant Dozier, PE",
        company="Both",
    )

    print(f"\\n3. Generating proposal document...")
    generator = ProposalGenerator(output_dir="/tmp/proposals")
    proposal_path = generator.generate_proposal(proposal_data)

    print(f"   Generated: {Path(proposal_path).name}")

    print(f"\\n4. Preparing cover letter...")
    documents = [
        SubmittalDocument(
            document_type="Proposal",
            description="Professional Services Proposal",
            filename=Path(proposal_path).name,
            page_count=8,
        ),
    ]

    submittal = SubmittalPackage(
        project_name=proposal_data.project_name,
        project_number="WORKFLOW-001",
        client_name=proposal_data.client_name,
        client_address="123 Test St\\nLafayette, LA 70508",
        client_contact=proposal_data.client_contact,
        subject="Professional Services Proposal",
        documents=documents,
        prepared_by=proposal_data.prepared_by,
        company=proposal_data.company,
    )

    print(f"\\n5. Generating cover letter...")
    cover_gen = CoverLetterGenerator(output_dir="/tmp/cover_letters")
    cover_path = cover_gen.generate_cover_letter(submittal)

    print(f"   Generated: {Path(cover_path).name}")

    print(f"\\n" + "="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    print(f"✅ Pricing: ${pricing['total']:,.2f} for {len(proposal_data.modules_requested)} modules")
    print(f"✅ Timeline: {pricing['estimated_days']} days")
    print(f"✅ Proposal: {Path(proposal_path).name}")
    print(f"✅ Cover Letter: {Path(cover_path).name}")
    print(f"✅ Status: Ready for client delivery!")
    print("="*80)

    assert Path(proposal_path).exists()
    assert Path(cover_path).exists()

    print(f"\\n✅ PASS: Complete workflow successful!")


def test_module_pricing_info():
    """Test module pricing information retrieval"""
    print("\\n" + "="*70)
    print("MODULE PRICING INFO TEST")
    print("="*70)

    calculator = PricingCalculator()

    print(f"\\nAvailable Modules:")
    print(f"  Total modules: {len(calculator.MODULE_PRICING)}")

    for module_id, module in calculator.MODULE_PRICING.items():
        print(f"\\n  Module {module_id}: {module.module_name}")
        print(f"    Price: ${module.base_price:,.2f}")
        print(f"    Time: {module.time_estimate_days} days")
        print(f"    Deliverables: {len(module.deliverables)}")

    # Verify all modules present
    assert len(calculator.MODULE_PRICING) == 5
    assert all(m in calculator.MODULE_PRICING for m in ["A", "B", "C", "D", "E"])

    # Verify pricing matches contract
    assert calculator.MODULE_PRICING["A"].base_price == Decimal("7500")
    assert calculator.MODULE_PRICING["B"].base_price == Decimal("8000")
    assert calculator.MODULE_PRICING["C"].base_price == Decimal("12000")
    assert calculator.MODULE_PRICING["D"].base_price == Decimal("9500")
    assert calculator.MODULE_PRICING["E"].base_price == Decimal("5000")

    print(f"\\n✅ PASS: All module pricing correct")


if __name__ == "__main__":
    """Run all Module E tests"""
    print("\\n" + "🚀"*40)
    print("MODULE E - PROPOSAL & DOCUMENT AUTOMATION")
    print("INTEGRATION TEST SUITE")
    print("🚀"*40)

    try:
        # Run all tests
        test_pricing_calculator()
        test_proposal_generation()
        test_cover_letter_generation()
        test_transmittal_form_generation()
        test_template_manager()
        test_full_proposal_workflow()
        test_module_pricing_info()

        print("\\n" + "="*80)
        print("✅ ALL MODULE E TESTS PASSED!")
        print("="*80)
        print("\\nModule E is production-ready!")
        print("• Pricing calculator validated")
        print("• Proposal generation working")
        print("• Cover letter generation working")
        print("• Template management functional")
        print("• Full workflow tested end-to-end")
        print("="*80 + "\\n")

    except AssertionError as e:
        print(f"\\n❌ TEST FAILED: {e}\\n")
        raise
    except Exception as e:
        print(f"\\n❌ ERROR: {e}\\n")
        raise
