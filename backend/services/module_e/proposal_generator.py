"""
Module E - Proposal Generator
Auto-generate branded proposals with scope, timeline, and pricing
"""
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)


@dataclass
class ModulePricing:
    """Pricing for individual automation modules"""
    module_id: str
    module_name: str
    description: str
    base_price: Decimal
    time_estimate_days: int
    deliverables: List[str] = field(default_factory=list)


@dataclass
class ProposalData:
    """
    Data for generating a proposal.

    Attributes:
        client_name: Name of client organization
        client_contact: Primary contact person
        client_email: Contact email
        project_name: Name of the project
        project_location: Project location
        project_description: Brief description
        modules_requested: List of module IDs (e.g., ["A", "C", "D"])
        custom_scope: Optional custom scope items
        discount_percent: Optional discount percentage (0-100)
        rush_fee_percent: Optional rush fee percentage (0-100)
        proposal_valid_days: Days proposal is valid (default 30)
        prepared_by: Name of person preparing proposal
        company: "LCR" or "Dozier" or "Both"
    """
    client_name: str
    client_contact: str
    client_email: str
    project_name: str
    project_location: str
    project_description: str
    modules_requested: List[str]
    custom_scope: List[str] = field(default_factory=list)
    discount_percent: Decimal = Decimal("0")
    rush_fee_percent: Decimal = Decimal("0")
    proposal_valid_days: int = 30
    prepared_by: str = "Grant Dozier, PE"
    company: str = "LCR"  # "LCR", "Dozier", or "Both"


class PricingCalculator:
    """
    Calculate pricing for automation module combinations.

    Standard Module Pricing:
    - Module A: $7,500 - Automated Area Calculation Engine
    - Module B: $8,000 - UDC & DOTD Specification Extraction
    - Module C: $12,000 - DIA Report Generator
    - Module D: $9,500 - Plan Review & QA Automation
    - Module E: $5,000 - Proposal & Document Automation

    Bundle Discounts:
    - 3 modules: 5% discount
    - 4 modules: 10% discount
    - All 5 modules: 15% discount
    """

    # Standard module pricing
    MODULE_PRICING = {
        "A": ModulePricing(
            module_id="A",
            module_name="Automated Area Calculation Engine",
            description="GIS-based drainage area delineation with weighted C-values",
            base_price=Decimal("7500"),
            time_estimate_days=10,
            deliverables=[
                "Automated drainage area calculation",
                "Weighted runoff coefficient (C-value) calculation",
                "Land use analysis",
                "Area split calculations (impervious/pervious)",
                "GIS integration",
            ],
        ),
        "B": ModulePricing(
            module_id="B",
            module_name="UDC & DOTD Specification Extraction",
            description="Automated extraction of regulatory requirements with NOAA Atlas 14",
            base_price=Decimal("8000"),
            time_estimate_days=12,
            deliverables=[
                "Lafayette UDC requirement extraction",
                "DOTD specification integration",
                "NOAA Atlas 14 rainfall data automation",
                "Compliance validation",
            ],
        ),
        "C": ModulePricing(
            module_id="C",
            module_name="DIA Report Generator",
            description="Professional 58+ page Drainage Impact Analysis reports",
            base_price=Decimal("12000"),
            time_estimate_days=15,
            deliverables=[
                "Automated DIA report generation (58+ pages)",
                "Rational Method calculations (Q=CiA)",
                "Time of Concentration analysis (4 methods)",
                "Multi-storm event analysis (10/25/50/100-year)",
                "Technical exhibits (3A-3D)",
                "NOAA Atlas 14 appendix",
                "Client-ready Word documents",
            ],
        ),
        "D": ModulePricing(
            module_id="D",
            module_name="Plan Review & QA Automation",
            description="OCR-based plan review with 25+ compliance checks",
            base_price=Decimal("9500"),
            time_estimate_days=14,
            deliverables=[
                "OCR-based plan sheet extraction",
                "25+ standard compliance checks",
                "LPDES/LUS/DOTD/ASTM validation",
                "Professional QA reports",
                "Sheet-by-sheet review",
                "Prioritized recommendations",
            ],
        ),
        "E": ModulePricing(
            module_id="E",
            module_name="Proposal & Document Automation",
            description="Automated proposal and submittal document generation",
            base_price=Decimal("5000"),
            time_estimate_days=7,
            deliverables=[
                "Branded proposal generation",
                "Automated pricing calculations",
                "Cover letter templates",
                "Submittal package automation",
                "Customizable document templates",
            ],
        ),
    }

    def calculate_total(
        self,
        modules: List[str],
        discount_percent: Decimal = Decimal("0"),
        rush_fee_percent: Decimal = Decimal("0")
    ) -> Dict:
        """
        Calculate total pricing for selected modules.

        Args:
            modules: List of module IDs (e.g., ["A", "C", "D"])
            discount_percent: Custom discount percentage (0-100)
            rush_fee_percent: Rush fee percentage (0-100)

        Returns:
            Dictionary with pricing breakdown
        """
        # Get module details
        selected_modules = [
            self.MODULE_PRICING[m]
            for m in modules
            if m in self.MODULE_PRICING
        ]

        # Calculate subtotal
        subtotal = sum(m.base_price for m in selected_modules)

        # Apply bundle discount
        bundle_discount = self._calculate_bundle_discount(len(modules))
        total_discount = max(discount_percent, bundle_discount)

        # Calculate discount amount
        discount_amount = subtotal * (total_discount / Decimal("100"))

        # Subtotal after discount
        discounted_subtotal = subtotal - discount_amount

        # Apply rush fee if applicable
        rush_fee_amount = discounted_subtotal * (rush_fee_percent / Decimal("100"))

        # Calculate total
        total = discounted_subtotal + rush_fee_amount

        # Estimate timeline
        total_days = sum(m.time_estimate_days for m in selected_modules)

        return {
            "modules": selected_modules,
            "subtotal": float(subtotal),
            "bundle_discount_percent": float(bundle_discount),
            "custom_discount_percent": float(discount_percent),
            "total_discount_percent": float(total_discount),
            "discount_amount": float(discount_amount),
            "discounted_subtotal": float(discounted_subtotal),
            "rush_fee_percent": float(rush_fee_percent),
            "rush_fee_amount": float(rush_fee_amount),
            "total": float(total),
            "estimated_days": total_days,
            "estimated_completion": (datetime.now() + timedelta(days=total_days)).strftime("%B %d, %Y"),
        }

    def _calculate_bundle_discount(self, module_count: int) -> Decimal:
        """
        Calculate bundle discount based on number of modules.

        Args:
            module_count: Number of modules selected

        Returns:
            Discount percentage
        """
        if module_count >= 5:
            return Decimal("15")  # 15% for all modules
        elif module_count >= 4:
            return Decimal("10")  # 10% for 4 modules
        elif module_count >= 3:
            return Decimal("5")   # 5% for 3 modules
        else:
            return Decimal("0")   # No bundle discount


class ProposalGenerator:
    """
    Generate professional branded proposals.

    Creates Word documents with:
    - Cover page with company branding
    - Project overview and scope
    - Detailed module descriptions
    - Pricing breakdown
    - Timeline and milestones
    - Terms and conditions
    - Signature page
    """

    def __init__(self, output_dir: str = "/app/outputs"):
        """
        Initialize proposal generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.calculator = PricingCalculator()

    def generate_proposal(
        self,
        proposal_data: ProposalData,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate complete proposal document.

        Args:
            proposal_data: Proposal data and requirements
            output_filename: Optional custom filename

        Returns:
            Path to generated proposal file
        """
        logger.info(f"Generating proposal for {proposal_data.client_name}")

        # Calculate pricing
        pricing = self.calculator.calculate_total(
            modules=proposal_data.modules_requested,
            discount_percent=proposal_data.discount_percent,
            rush_fee_percent=proposal_data.rush_fee_percent
        )

        # Create document
        doc = Document()

        # Cover page
        self._add_cover_page(doc, proposal_data)
        doc.add_page_break()

        # Project overview
        self._add_project_overview(doc, proposal_data)
        doc.add_page_break()

        # Scope of services
        self._add_scope_of_services(doc, proposal_data, pricing)
        doc.add_page_break()

        # Pricing
        self._add_pricing_section(doc, pricing)
        doc.add_page_break()

        # Timeline
        self._add_timeline_section(doc, pricing)
        doc.add_page_break()

        # Terms and conditions
        self._add_terms_and_conditions(doc, proposal_data)
        doc.add_page_break()

        # Signature page
        self._add_signature_page(doc, proposal_data)

        # Save document
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d")
            safe_client = proposal_data.client_name.replace(" ", "_")
            output_filename = f"Proposal_{safe_client}_{timestamp}.docx"

        output_path = self.output_dir / output_filename
        doc.save(str(output_path))

        logger.info(f"Generated proposal: {output_path}")
        return str(output_path)

    def _add_cover_page(self, doc: Document, data: ProposalData):
        """Add branded cover page"""
        # Company logo/header (would add actual logo in production)
        header = doc.add_paragraph()
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if data.company == "LCR":
            company_name = "LCR & COMPANY"
            tagline = "Civil Engineering & Land Surveying"
        elif data.company == "Dozier":
            company_name = "DOZIER TECH"
            tagline = "Engineering Technology Solutions"
        else:
            company_name = "LCR & COMPANY | DOZIER TECH"
            tagline = "Integrated Engineering Solutions"

        run = header.add_run(f"{company_name}\\n")
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)

        run = header.add_run(f"{tagline}\\n\\n\\n")
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0, 51, 102)

        # Proposal title
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run("PROFESSIONAL SERVICES PROPOSAL\\n\\n\\n")
        run.font.size = Pt(20)
        run.font.bold = True

        # Project info
        project_info = doc.add_paragraph()
        project_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = project_info.add_run(f"{data.project_name}\\n")
        run.font.size = Pt(18)
        run.font.bold = True

        run = project_info.add_run(f"{data.project_location}\\n\\n\\n")
        run.font.size = Pt(14)

        # Client info
        client_info = doc.add_paragraph()
        client_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = client_info.add_run("Prepared For:\\n")
        run.font.size = Pt(12)
        run.font.bold = True

        run = client_info.add_run(
            f"{data.client_name}\\n"
            f"{data.client_contact}\\n"
            f"{data.client_email}\\n\\n\\n"
        )
        run.font.size = Pt(12)

        # Date and validity
        date_info = doc.add_paragraph()
        date_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        proposal_date = datetime.now().strftime("%B %d, %Y")
        valid_until = (datetime.now() + timedelta(days=data.proposal_valid_days)).strftime("%B %d, %Y")

        run = date_info.add_run(
            f"Proposal Date: {proposal_date}\\n"
            f"Valid Until: {valid_until}\\n\\n"
        )
        run.font.size = Pt(11)

        # Prepared by
        doc.add_paragraph("\\n" * 5)
        prepared = doc.add_paragraph()
        prepared.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = prepared.add_run(f"Prepared By:\\n{data.prepared_by}")
        run.font.size = Pt(11)

    def _add_project_overview(self, doc: Document, data: ProposalData):
        """Add project overview section"""
        doc.add_heading("PROJECT OVERVIEW", level=1)

        overview = doc.add_paragraph()
        overview.add_run("Project Name: ").font.bold = True
        overview.add_run(f"{data.project_name}\\n\\n")

        overview.add_run("Location: ").font.bold = True
        overview.add_run(f"{data.project_location}\\n\\n")

        overview.add_run("Description:\\n").font.bold = True
        overview.add_run(f"{data.project_description}\\n\\n")

        # About section
        doc.add_heading("ABOUT OUR AUTOMATION SERVICES", level=2)

        about_text = (
            "LCR & Company and Dozier Tech have partnered to deliver cutting-edge "
            "civil engineering automation solutions. Our suite of automation modules "
            "streamlines drainage analysis, regulatory compliance, plan review, and "
            "document generation - reducing project delivery time by 70% while maintaining "
            "the highest professional engineering standards.\\n\\n"
            "Each module is built on proven methodologies, validated with real project data, "
            "and designed to generate client-ready deliverables that meet all Lafayette UDC, "
            "DOTD, and LPDES requirements."
        )
        doc.add_paragraph(about_text)

    def _add_scope_of_services(
        self,
        doc: Document,
        data: ProposalData,
        pricing: Dict
    ):
        """Add scope of services section"""
        doc.add_heading("SCOPE OF SERVICES", level=1)

        doc.add_paragraph(
            "This proposal includes the following automation modules and services:"
        )

        # Add each selected module
        for module in pricing["modules"]:
            doc.add_heading(f"Module {module.module_id}: {module.module_name}", level=2)

            desc_para = doc.add_paragraph()
            desc_para.add_run("Description: ").font.bold = True
            desc_para.add_run(f"{module.description}\\n\\n")

            desc_para.add_run("Deliverables:\\n").font.bold = True
            for deliverable in module.deliverables:
                doc.add_paragraph(deliverable, style='List Bullet')

            doc.add_paragraph("")  # Spacing

        # Custom scope items
        if data.custom_scope:
            doc.add_heading("Additional Custom Services", level=2)
            for item in data.custom_scope:
                doc.add_paragraph(item, style='List Bullet')

    def _add_pricing_section(self, doc: Document, pricing: Dict):
        """Add pricing breakdown section"""
        doc.add_heading("PRICING", level=1)

        # Create pricing table
        table = doc.add_table(rows=len(pricing["modules"]) + 6, cols=3)
        table.style = 'Light Grid Accent 1'

        # Header
        headers = ["Module", "Description", "Price"]
        for idx, header in enumerate(headers):
            cell = table.rows[0].cells[idx]
            cell.text = header
            cell.paragraphs[0].runs[0].font.bold = True

        # Module rows
        for idx, module in enumerate(pricing["modules"], start=1):
            row = table.rows[idx]
            row.cells[0].text = f"Module {module.module_id}"
            row.cells[1].text = module.module_name
            row.cells[2].text = f"${module.base_price:,.2f}"

        # Subtotal
        row_idx = len(pricing["modules"]) + 1
        table.rows[row_idx].cells[1].text = "Subtotal"
        table.rows[row_idx].cells[1].paragraphs[0].runs[0].font.bold = True
        table.rows[row_idx].cells[2].text = f"${pricing['subtotal']:,.2f}"

        # Discount
        if pricing["total_discount_percent"] > 0:
            row_idx += 1
            discount_label = f"Discount ({pricing['total_discount_percent']:.0f}%)"
            if pricing["bundle_discount_percent"] > 0:
                discount_label += " - Bundle Savings!"
            table.rows[row_idx].cells[1].text = discount_label
            table.rows[row_idx].cells[2].text = f"-${pricing['discount_amount']:,.2f}"
            table.rows[row_idx].cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 128, 0)

        # Rush fee
        if pricing["rush_fee_percent"] > 0:
            row_idx += 1
            table.rows[row_idx].cells[1].text = f"Rush Fee ({pricing['rush_fee_percent']:.0f}%)"
            table.rows[row_idx].cells[2].text = f"+${pricing['rush_fee_amount']:,.2f}"

        # Total
        row_idx += 1
        table.rows[row_idx].cells[1].text = "TOTAL INVESTMENT"
        table.rows[row_idx].cells[1].paragraphs[0].runs[0].font.bold = True
        table.rows[row_idx].cells[1].paragraphs[0].runs[0].font.size = Pt(14)
        table.rows[row_idx].cells[2].text = f"${pricing['total']:,.2f}"
        table.rows[row_idx].cells[2].paragraphs[0].runs[0].font.bold = True
        table.rows[row_idx].cells[2].paragraphs[0].runs[0].font.size = Pt(14)

        doc.add_paragraph("")
        payment_terms = doc.add_paragraph()
        payment_terms.add_run("Payment Terms:\\n").font.bold = True
        payment_terms.add_run(
            "• 50% due upon contract execution\\n"
            "• 50% due upon delivery of final deliverables\\n"
            "• Payment accepted via check or ACH transfer\\n"
        )

    def _add_timeline_section(self, doc: Document, pricing: Dict):
        """Add timeline and milestones section"""
        doc.add_heading("PROJECT TIMELINE", level=1)

        timeline_para = doc.add_paragraph()
        timeline_para.add_run("Estimated Duration: ").font.bold = True
        timeline_para.add_run(f"{pricing['estimated_days']} business days\\n\\n")

        timeline_para.add_run("Estimated Completion: ").font.bold = True
        timeline_para.add_run(f"{pricing['estimated_completion']}\\n\\n")

        doc.add_heading("Project Milestones", level=2)

        milestones = [
            "Contract Execution & Kickoff Meeting",
            "Data Collection & Requirements Review",
            "Module Development & Integration",
            "Quality Assurance Testing",
            "Client Review & Revisions",
            "Final Delivery & Training",
        ]

        for milestone in milestones:
            doc.add_paragraph(milestone, style='List Bullet')

    def _add_terms_and_conditions(self, doc: Document, data: ProposalData):
        """Add terms and conditions"""
        doc.add_heading("TERMS & CONDITIONS", level=1)

        terms = [
            ("Scope Changes", "Any changes to the scope of work will be documented via change order with associated cost and schedule adjustments."),
            ("Client Responsibilities", "Client will provide timely access to project data, site plans, and necessary regulatory documents."),
            ("Intellectual Property", "All custom automation modules and deliverables become the property of the client upon final payment."),
            ("Warranties", "All deliverables are guaranteed to meet stated specifications and comply with Lafayette UDC, DOTD, and LPDES requirements."),
            ("Support", "30 days of post-delivery support included. Extended support and maintenance plans available."),
            ("Confidentiality", "All project data and deliverables will be kept confidential and used only for this project."),
        ]

        for title, description in terms:
            term_para = doc.add_paragraph()
            term_para.add_run(f"{title}: ").font.bold = True
            term_para.add_run(f"{description}\\n")

    def _add_signature_page(self, doc: Document, data: ProposalData):
        """Add signature page"""
        doc.add_heading("ACCEPTANCE", level=1)

        acceptance = doc.add_paragraph(
            "By signing below, client accepts the scope, pricing, and terms outlined in this proposal."
        )

        doc.add_paragraph("\\n" * 2)

        # Client signature block
        client_sig = doc.add_paragraph()
        client_sig.add_run("CLIENT ACCEPTANCE:\\n\\n")
        client_sig.add_run("_" * 50 + "\\n")
        client_sig.add_run(f"{data.client_contact}, {data.client_name}\\n\\n")
        client_sig.add_run("Date: _" + "_" * 30 + "\\n\\n\\n")

        # Company signature block
        company_sig = doc.add_paragraph()
        if data.company == "LCR":
            company_name = "LCR & COMPANY"
        elif data.company == "Dozier":
            company_name = "DOZIER TECH"
        else:
            company_name = "LCR & COMPANY / DOZIER TECH"

        company_sig.add_run(f"{company_name.upper()}:\\n\\n")
        company_sig.add_run("_" * 50 + "\\n")
        company_sig.add_run(f"{data.prepared_by}\\n\\n")
        company_sig.add_run("Date: _" + "_" * 30 + "\\n")
