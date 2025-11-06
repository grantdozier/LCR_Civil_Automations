"""
SQLAlchemy models matching the database schema
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    TIMESTAMP,
    Boolean,
    Text,
    ARRAY,
    ForeignKey,
    Numeric,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from core.database import Base


class Project(Base):
    """Projects table - top level organizational unit"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    project_number = Column(String(50), unique=True)
    client_name = Column(String(255))
    location = Column(String(500))
    project_type = Column(String(100))
    jurisdiction = Column(String(100))
    status = Column(String(50), default="active")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    extra_data = Column(JSONB)

    # Relationships
    drawings = relationship("Drawing", back_populates="project", cascade="all, delete-orphan")
    drainage_areas = relationship("DrainageArea", back_populates="project", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")


class Drawing(Base):
    """Drawings table - CAD files linked to projects"""

    __tablename__ = "drawings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    drawing_name = Column(String(255), nullable=False)
    drawing_number = Column(String(50))
    file_path = Column(String(1000))
    file_type = Column(String(50))
    sheet_type = Column(String(50))
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    extra_data = Column(JSONB)

    # Relationships
    project = relationship("Project", back_populates="drawings")
    drainage_areas = relationship("DrainageArea", back_populates="drawing", cascade="all, delete-orphan")
    qa_results = relationship("QAResult", back_populates="drawing", cascade="all, delete-orphan")


class DrainageArea(Base):
    """Drainage areas with PostGIS geometry"""

    __tablename__ = "drainage_areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drawing_id = Column(UUID(as_uuid=True), ForeignKey("drawings.id", ondelete="CASCADE"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    area_label = Column(String(100), nullable=False)

    # Area calculations
    total_area_sqft = Column(Numeric(12, 2))
    total_area_acres = Column(Numeric(10, 4))
    impervious_area_sqft = Column(Numeric(12, 2))
    impervious_area_acres = Column(Numeric(10, 4))
    pervious_area_sqft = Column(Numeric(12, 2))
    pervious_area_acres = Column(Numeric(10, 4))

    # Runoff coefficient
    weighted_c_value = Column(Numeric(5, 3))

    # Land use breakdown
    land_use_breakdown = Column(JSONB)

    # Geometry (PostGIS)
    geometry = Column(Geometry("POLYGON", srid=4326))
    centroid = Column(Geometry("POINT", srid=4326))

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    notes = Column(Text)

    # Relationships
    project = relationship("Project", back_populates="drainage_areas")
    drawing = relationship("Drawing", back_populates="drainage_areas")
    results = relationship("Result", back_populates="drainage_area", cascade="all, delete-orphan")


class Run(Base):
    """Analysis runs - each run can have multiple results"""

    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    run_type = Column(String(50), nullable=False)
    storm_events = Column(ARRAY(String), default=["10", "25", "50", "100"])

    # Analysis parameters
    parameters = Column(JSONB)

    # Status tracking
    status = Column(String(50), default="pending")
    started_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP)

    # Results summary
    results_summary = Column(JSONB)
    error_message = Column(Text)

    # User tracking
    created_by = Column(String(100))

    extra_data = Column(JSONB)

    # Relationships
    project = relationship("Project", back_populates="runs")
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")
    qa_results = relationship("QAResult", back_populates="run", cascade="all, delete-orphan")


class Result(Base):
    """Drainage calculation results - Rational Method: Q=CiA"""

    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"))
    drainage_area_id = Column(UUID(as_uuid=True), ForeignKey("drainage_areas.id", ondelete="CASCADE"))

    # Storm event
    storm_event = Column(String(20), nullable=False)

    # Rational Method components: Q = CiA
    c_value = Column(Numeric(5, 3))
    i_value = Column(Numeric(8, 4))
    area_acres = Column(Numeric(10, 4))

    # Calculated flow
    peak_flow_cfs = Column(Numeric(10, 3))

    # Time of Concentration
    tc_minutes = Column(Numeric(8, 2))
    tc_method = Column(String(100))

    # Pre vs Post development
    development_condition = Column(String(20))

    # Additional hydraulic parameters
    velocity_fps = Column(Numeric(8, 2))
    pipe_diameter_inches = Column(Numeric(6, 2))
    pipe_material = Column(String(50))

    # Detention/retention
    detention_volume_cf = Column(Numeric(12, 2))

    # Calculation details
    calculation_details = Column(JSONB)

    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    run = relationship("Run", back_populates="results")
    drainage_area = relationship("DrainageArea", back_populates="results")


class Spec(Base):
    """Regulatory specifications - Module B"""

    __tablename__ = "specs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source information
    jurisdiction = Column(String(100), nullable=False)
    document_name = Column(String(255), nullable=False)
    section_reference = Column(String(255))

    # Specification type
    spec_type = Column(String(100), nullable=False)

    # Specification data
    land_use_type = Column(String(255))
    c_value_min = Column(Numeric(5, 3))
    c_value_max = Column(Numeric(5, 3))
    c_value_recommended = Column(Numeric(5, 3))

    # Rainfall intensity (NOAA Atlas 14)
    duration_minutes = Column(Numeric(8, 2))
    return_period_years = Column(Integer)
    intensity_in_per_hr = Column(Numeric(8, 4))

    # Tc limits and requirements
    tc_min_minutes = Column(Numeric(8, 2))
    tc_max_minutes = Column(Numeric(8, 2))

    # Detention/retention requirements
    detention_rule = Column(Text)

    # Full text and context
    full_text = Column(Text)
    context = Column(Text)

    # Metadata
    extracted_at = Column(TIMESTAMP, server_default=func.now())
    extraction_confidence = Column(Numeric(3, 2))
    verified = Column(Boolean, default=False)

    extra_data = Column(JSONB)


class QAResult(Base):
    """Plan review QA results - Module D"""

    __tablename__ = "qa_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"))
    drawing_id = Column(UUID(as_uuid=True), ForeignKey("drawings.id", ondelete="CASCADE"))

    # Sheet identification
    sheet_number = Column(String(50))
    sheet_title = Column(String(255))

    # QA checks
    checks_performed = Column(JSONB)
    checks_passed = Column(JSONB)
    checks_failed = Column(JSONB)

    # Overall status
    overall_status = Column(String(50))
    pass_rate = Column(Numeric(5, 2))

    # Findings
    findings = Column(JSONB)
    required_notes_missing = Column(ARRAY(Text))
    drainage_area_mismatches = Column(JSONB)

    # OCR extracted text
    extracted_text = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
    extra_data = Column(JSONB)

    # Relationships
    run = relationship("Run", back_populates="qa_results")
    drawing = relationship("Drawing", back_populates="qa_results")


class Proposal(Base):
    """Generated proposal documents - Module E"""

    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))

    # Proposal details
    proposal_number = Column(String(50), unique=True)
    client_name = Column(String(255), nullable=False)
    proposal_type = Column(String(100))

    # Scope
    modules_included = Column(ARRAY(String), default=["A", "B", "C", "D", "E"])
    scope_description = Column(Text)

    # Pricing
    total_price = Column(Numeric(10, 2))
    pricing_breakdown = Column(JSONB)

    # Timeline
    estimated_weeks = Column(Integer)
    start_date = Column(Date)
    completion_date = Column(Date)

    # Document generation
    document_path = Column(String(1000))
    document_format = Column(String(20))

    # Status
    status = Column(String(50), default="draft")
    sent_at = Column(TIMESTAMP)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    extra_data = Column(JSONB)

    # Relationships
    project = relationship("Project", back_populates="proposals")
