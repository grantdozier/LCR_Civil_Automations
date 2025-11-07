-- LCR Civil Drainage Automation System - Database Schema
-- PostgreSQL 15 + PostGIS 3.3

-- Enable PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (development only)
DROP TABLE IF EXISTS proposals CASCADE;
DROP TABLE IF EXISTS qa_results CASCADE;
DROP TABLE IF EXISTS results CASCADE;
DROP TABLE IF EXISTS runs CASCADE;
DROP TABLE IF EXISTS specs CASCADE;
DROP TABLE IF EXISTS drainage_areas CASCADE;
DROP TABLE IF EXISTS drawings CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    project_number VARCHAR(50) UNIQUE,
    client_name VARCHAR(255),
    location VARCHAR(500),
    project_type VARCHAR(100), -- e.g., "Municipal Drainage", "Land Development"
    jurisdiction VARCHAR(100), -- e.g., "Lafayette", "DOTD"
    status VARCHAR(50) DEFAULT 'active', -- active, completed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB -- Flexible field for additional project-specific data
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_jurisdiction ON projects(jurisdiction);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);

-- ============================================================================
-- DRAWINGS TABLE (CAD files linked to projects)
-- ============================================================================
CREATE TABLE drawings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    drawing_name VARCHAR(255) NOT NULL,
    drawing_number VARCHAR(50),
    file_path VARCHAR(1000),
    file_type VARCHAR(50), -- e.g., "DWG", "DXF", "PDF"
    sheet_type VARCHAR(50), -- e.g., "C-1", "C-2", ..., "C-18" for plan review
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB
);

CREATE INDEX idx_drawings_project_id ON drawings(project_id);
CREATE INDEX idx_drawings_sheet_type ON drawings(sheet_type);

-- ============================================================================
-- DRAINAGE_AREAS TABLE (PostGIS geometry for drainage basins)
-- ============================================================================
CREATE TABLE drainage_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID REFERENCES drawings(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    area_label VARCHAR(100) NOT NULL, -- e.g., "E-DA1", "E-DA2"

    -- Area calculations
    total_area_sqft NUMERIC(12, 2),
    total_area_acres NUMERIC(10, 4),
    impervious_area_sqft NUMERIC(12, 2),
    impervious_area_acres NUMERIC(10, 4),
    pervious_area_sqft NUMERIC(12, 2),
    pervious_area_acres NUMERIC(10, 4),

    -- Runoff coefficient
    weighted_c_value NUMERIC(5, 3), -- e.g., 0.720

    -- Land use breakdown (JSONB for flexibility)
    land_use_breakdown JSONB, -- e.g., {"pavement": 0.5, "roof": 0.3, "grass": 0.2}

    -- Geometry (PostGIS)
    geometry GEOMETRY(POLYGON, 4326), -- WGS84 coordinate system
    centroid GEOMETRY(POINT, 4326),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX idx_drainage_areas_project_id ON drainage_areas(project_id);
CREATE INDEX idx_drainage_areas_drawing_id ON drainage_areas(drawing_id);
CREATE INDEX idx_drainage_areas_label ON drainage_areas(area_label);
CREATE INDEX idx_drainage_areas_geometry ON drainage_areas USING GIST(geometry);
CREATE INDEX idx_drainage_areas_centroid ON drainage_areas USING GIST(centroid);

-- ============================================================================
-- RUNS TABLE (Analysis runs - each run can have multiple results)
-- ============================================================================
CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    run_type VARCHAR(50) NOT NULL, -- e.g., "drainage_analysis", "qa_review", "proposal"
    storm_events VARCHAR[] DEFAULT ARRAY['10', '25', '50', '100'], -- Year return periods

    -- Analysis parameters
    parameters JSONB, -- Flexible field for run-specific parameters

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    -- Results summary
    results_summary JSONB,
    error_message TEXT,

    -- User tracking (future enhancement)
    created_by VARCHAR(100),

    extra_data JSONB
);

CREATE INDEX idx_runs_project_id ON runs(project_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_started_at ON runs(started_at DESC);

-- ============================================================================
-- RESULTS TABLE (Drainage calculation results - Rational Method: Q=CiA)
-- ============================================================================
CREATE TABLE results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
    drainage_area_id UUID REFERENCES drainage_areas(id) ON DELETE CASCADE,

    -- Storm event
    storm_event VARCHAR(20) NOT NULL, -- e.g., "10-year", "25-year", "50-year", "100-year"

    -- Rational Method components: Q = CiA
    c_value NUMERIC(5, 3), -- Runoff coefficient
    i_value NUMERIC(8, 4), -- Rainfall intensity (in/hr)
    area_acres NUMERIC(10, 4), -- Area in acres

    -- Calculated flow
    peak_flow_cfs NUMERIC(10, 3), -- Q in cubic feet per second (cfs)

    -- Time of Concentration
    tc_minutes NUMERIC(8, 2), -- Time of Concentration in minutes
    tc_method VARCHAR(100), -- e.g., "NRCS", "Kirpich", "FAA"

    -- Pre vs Post development
    development_condition VARCHAR(20), -- "pre" or "post"

    -- Additional hydraulic parameters
    velocity_fps NUMERIC(8, 2), -- Velocity in feet per second
    pipe_diameter_inches NUMERIC(6, 2),
    pipe_material VARCHAR(50),

    -- Detention/retention
    detention_volume_cf NUMERIC(12, 2), -- Cubic feet

    -- Calculation details
    calculation_details JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_results_run_id ON results(run_id);
CREATE INDEX idx_results_drainage_area_id ON results(drainage_area_id);
CREATE INDEX idx_results_storm_event ON results(storm_event);
CREATE INDEX idx_results_development_condition ON results(development_condition);

-- ============================================================================
-- SPECS TABLE (Regulatory specifications - Module B)
-- ============================================================================
CREATE TABLE specs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source information
    jurisdiction VARCHAR(100) NOT NULL, -- e.g., "Lafayette UDC", "DOTD"
    document_name VARCHAR(255) NOT NULL,
    section_reference VARCHAR(255), -- e.g., "Section 8.3.2"

    -- Specification type
    spec_type VARCHAR(100) NOT NULL, -- e.g., "runoff_coefficient", "rainfall_intensity", "tc_limit"

    -- Specification data
    land_use_type VARCHAR(255), -- For runoff coefficients
    c_value_min NUMERIC(5, 3),
    c_value_max NUMERIC(5, 3),
    c_value_recommended NUMERIC(5, 3),

    -- Rainfall intensity (NOAA Atlas 14)
    duration_minutes NUMERIC(8, 2),
    return_period_years INTEGER, -- e.g., 10, 25, 50, 100
    intensity_in_per_hr NUMERIC(8, 4),

    -- Tc limits and requirements
    tc_min_minutes NUMERIC(8, 2),
    tc_max_minutes NUMERIC(8, 2),

    -- Detention/retention requirements
    detention_rule TEXT,

    -- Full text and context
    full_text TEXT,
    context TEXT,

    -- Metadata
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence NUMERIC(3, 2), -- 0.00 to 1.00 (from LangChain)
    verified BOOLEAN DEFAULT FALSE,

    extra_data JSONB
);

CREATE INDEX idx_specs_jurisdiction ON specs(jurisdiction);
CREATE INDEX idx_specs_type ON specs(spec_type);
CREATE INDEX idx_specs_land_use ON specs(land_use_type);
CREATE INDEX idx_specs_return_period ON specs(return_period_years);

-- ============================================================================
-- QA_RESULTS TABLE (Plan review QA results - Module D)
-- ============================================================================
CREATE TABLE qa_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
    drawing_id UUID REFERENCES drawings(id) ON DELETE CASCADE,

    -- Sheet identification
    sheet_number VARCHAR(50), -- e.g., "C-1", "C-2"
    sheet_title VARCHAR(255),

    -- QA checks
    checks_performed JSONB, -- Array of check names
    checks_passed JSONB, -- Array of passed check names
    checks_failed JSONB, -- Array of failed check names

    -- Overall status
    overall_status VARCHAR(50), -- "pass", "fail", "warning"
    pass_rate NUMERIC(5, 2), -- Percentage (0.00 to 100.00)

    -- Findings
    findings JSONB, -- Detailed findings array
    required_notes_missing TEXT[],
    drainage_area_mismatches JSONB,

    -- OCR extracted text
    extracted_text TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB
);

CREATE INDEX idx_qa_results_run_id ON qa_results(run_id);
CREATE INDEX idx_qa_results_drawing_id ON qa_results(drawing_id);
CREATE INDEX idx_qa_results_status ON qa_results(overall_status);

-- ============================================================================
-- PROPOSALS TABLE (Generated proposal documents - Module E)
-- ============================================================================
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Proposal details
    proposal_number VARCHAR(50) UNIQUE,
    client_name VARCHAR(255) NOT NULL,
    proposal_type VARCHAR(100), -- e.g., "full_service", "module_a_only"

    -- Scope
    modules_included VARCHAR[] DEFAULT ARRAY['A', 'B', 'C', 'D', 'E'],
    scope_description TEXT,

    -- Pricing
    total_price NUMERIC(10, 2),
    pricing_breakdown JSONB, -- {"module_a": 7500, "module_b": 8000, ...}

    -- Timeline
    estimated_weeks INTEGER,
    start_date DATE,
    completion_date DATE,

    -- Document generation
    document_path VARCHAR(1000),
    document_format VARCHAR(20), -- "docx", "pdf"

    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, accepted, rejected
    sent_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB
);

CREATE INDEX idx_proposals_project_id ON proposals(project_id);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_created_at ON proposals(created_at DESC);

-- ============================================================================
-- TRIGGERS FOR updated_at timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drainage_areas_updated_at BEFORE UPDATE ON drainage_areas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Complete drainage analysis results by project
CREATE OR REPLACE VIEW v_drainage_analysis AS
SELECT
    p.id AS project_id,
    p.name AS project_name,
    p.project_number,
    da.area_label,
    da.total_area_acres,
    da.weighted_c_value,
    r.storm_event,
    r.development_condition,
    r.tc_minutes,
    r.peak_flow_cfs,
    ru.started_at AS analysis_date
FROM projects p
JOIN drainage_areas da ON p.id = da.project_id
JOIN results r ON da.id = r.drainage_area_id
JOIN runs ru ON r.run_id = ru.id
ORDER BY p.name, da.area_label, r.storm_event;

-- View: QA summary by project
CREATE OR REPLACE VIEW v_qa_summary AS
SELECT
    p.id AS project_id,
    p.name AS project_name,
    COUNT(DISTINCT qa.id) AS total_sheets_reviewed,
    SUM(CASE WHEN qa.overall_status = 'pass' THEN 1 ELSE 0 END) AS sheets_passed,
    SUM(CASE WHEN qa.overall_status = 'fail' THEN 1 ELSE 0 END) AS sheets_failed,
    AVG(qa.pass_rate) AS avg_pass_rate,
    MAX(qa.created_at) AS last_review_date
FROM projects p
LEFT JOIN runs ru ON p.id = ru.project_id AND ru.run_type = 'qa_review'
LEFT JOIN qa_results qa ON ru.id = qa.run_id
GROUP BY p.id, p.name;

-- ============================================================================
-- SAMPLE COMMENTS
-- ============================================================================
COMMENT ON TABLE projects IS 'Client projects - top level organizational unit';
COMMENT ON TABLE drainage_areas IS 'Calculated drainage basins with PostGIS geometry';
COMMENT ON TABLE results IS 'Rational Method calculation results: Q = CiA';
COMMENT ON TABLE specs IS 'Extracted regulatory specifications from UDC/DOTD manuals';
COMMENT ON TABLE qa_results IS 'Plan review QA findings';
COMMENT ON TABLE proposals IS 'Generated proposal documents';

-- ============================================================================
-- INITIALIZATION COMPLETE
-- ============================================================================
