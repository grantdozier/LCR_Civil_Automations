-- Sample data for development and testing
-- This file is optional and only runs if present

-- Insert sample project (Acadiana High School - from project_context)
INSERT INTO projects (id, name, project_number, client_name, location, project_type, jurisdiction, status) VALUES
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Acadiana High School Drainage Improvements',
    '2025-10-10',
    'Lafayette Parish School Board',
    'Lafayette, LA',
    'Municipal Drainage',
    'Lafayette',
    'active'
);

-- Insert sample drawing
INSERT INTO drawings (id, project_id, drawing_name, drawing_number, sheet_type) VALUES
(
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'Acadiana High School Civil Plans',
    'C-1',
    'C-1'
);

-- Insert sample drainage areas (from Acadiana High DIA report)
INSERT INTO drainage_areas (
    id,
    drawing_id,
    project_id,
    area_label,
    total_area_acres,
    impervious_area_acres,
    pervious_area_acres,
    weighted_c_value,
    land_use_breakdown
) VALUES
(
    '550e8400-e29b-41d4-a716-446655440010',
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'E-DA1',
    13.68,
    9.85,
    3.83,
    0.720,
    '{"pavement": 0.60, "roof": 0.12, "grass": 0.28}'::jsonb
),
(
    '550e8400-e29b-41d4-a716-446655440011',
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'E-DA2',
    15.10,
    7.55,
    7.55,
    0.500,
    '{"pavement": 0.40, "roof": 0.10, "grass": 0.50}'::jsonb
),
(
    '550e8400-e29b-41d4-a716-446655440012',
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'E-DA3',
    32.43,
    13.62,
    18.81,
    0.420,
    '{"pavement": 0.30, "roof": 0.12, "grass": 0.58}'::jsonb
),
(
    '550e8400-e29b-41d4-a716-446655440013',
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'E-DA4',
    12.10,
    3.51,
    8.59,
    0.290,
    '{"pavement": 0.20, "roof": 0.09, "grass": 0.71}'::jsonb
);

-- Insert sample run
INSERT INTO runs (
    id,
    project_id,
    run_type,
    storm_events,
    status,
    completed_at,
    created_by
) VALUES
(
    '550e8400-e29b-41d4-a716-446655440020',
    '550e8400-e29b-41d4-a716-446655440000',
    'drainage_analysis',
    ARRAY['10', '25', '50', '100'],
    'completed',
    CURRENT_TIMESTAMP,
    'system'
);

-- Insert sample results for 10-year storm (E-DA1)
INSERT INTO results (
    run_id,
    drainage_area_id,
    storm_event,
    c_value,
    i_value,
    area_acres,
    peak_flow_cfs,
    tc_minutes,
    tc_method,
    development_condition
) VALUES
-- E-DA1 - 10 year
(
    '550e8400-e29b-41d4-a716-446655440020',
    '550e8400-e29b-41d4-a716-446655440010',
    '10-year',
    0.720,
    7.25,
    13.68,
    71.4,
    12.5,
    'NRCS',
    'post'
),
-- E-DA1 - 25 year
(
    '550e8400-e29b-41d4-a716-446655440020',
    '550e8400-e29b-41d4-a716-446655440010',
    '25-year',
    0.720,
    8.65,
    13.68,
    85.2,
    12.5,
    'NRCS',
    'post'
),
-- E-DA1 - 50 year
(
    '550e8400-e29b-41d4-a716-446655440020',
    '550e8400-e29b-41d4-a716-446655440010',
    '50-year',
    0.720,
    9.82,
    13.68,
    96.7,
    12.5,
    'NRCS',
    'post'
),
-- E-DA1 - 100 year
(
    '550e8400-e29b-41d4-a716-446655440020',
    '550e8400-e29b-41d4-a716-446655440010',
    '100-year',
    0.720,
    11.05,
    13.68,
    108.9,
    12.5,
    'NRCS',
    'post'
);

-- Insert sample specs (Lafayette UDC runoff coefficients)
INSERT INTO specs (
    jurisdiction,
    document_name,
    section_reference,
    spec_type,
    land_use_type,
    c_value_min,
    c_value_max,
    c_value_recommended,
    verified
) VALUES
('Lafayette UDC', 'Unified Development Code', 'Table 8-1', 'runoff_coefficient', 'Pavement (Asphalt)', 0.85, 0.95, 0.90, true),
('Lafayette UDC', 'Unified Development Code', 'Table 8-1', 'runoff_coefficient', 'Pavement (Concrete)', 0.80, 0.95, 0.90, true),
('Lafayette UDC', 'Unified Development Code', 'Table 8-1', 'runoff_coefficient', 'Roof', 0.75, 0.95, 0.85, true),
('Lafayette UDC', 'Unified Development Code', 'Table 8-1', 'runoff_coefficient', 'Grass (Flat <2%)', 0.05, 0.15, 0.10, true),
('Lafayette UDC', 'Unified Development Code', 'Table 8-1', 'runoff_coefficient', 'Grass (Moderate 2-7%)', 0.10, 0.20, 0.15, true),
('DOTD', 'Hydraulic Design Manual', 'Chapter 5', 'runoff_coefficient', 'Pavement', 0.85, 0.95, 0.90, true),
('DOTD', 'Hydraulic Design Manual', 'Chapter 5', 'runoff_coefficient', 'Turf', 0.10, 0.25, 0.15, true);

-- Insert sample rainfall intensities (NOAA Atlas 14 for Lafayette, LA)
INSERT INTO specs (
    jurisdiction,
    document_name,
    spec_type,
    duration_minutes,
    return_period_years,
    intensity_in_per_hr
) VALUES
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 5, 10, 8.92),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 10, 10, 7.25),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 15, 10, 6.38),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 30, 10, 4.85),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 5, 25, 10.65),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 10, 25, 8.65),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 15, 25, 7.62),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 30, 25, 5.79),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 5, 50, 12.08),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 10, 50, 9.82),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 15, 50, 8.65),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 30, 50, 6.57),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 5, 100, 13.60),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 10, 100, 11.05),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 15, 100, 9.74),
('NOAA Atlas 14', 'Precipitation-Frequency Atlas', 'rainfall_intensity', 30, 100, 7.40);

-- Sample proposal
INSERT INTO proposals (
    project_id,
    proposal_number,
    client_name,
    proposal_type,
    modules_included,
    total_price,
    pricing_breakdown,
    estimated_weeks,
    status
) VALUES
(
    '550e8400-e29b-41d4-a716-446655440000',
    'PROP-2025-001',
    'Lafayette Parish School Board',
    'full_service',
    ARRAY['A', 'B', 'C', 'D', 'E'],
    42000.00,
    '{"module_a": 7500, "module_b": 8000, "module_c": 12000, "module_d": 9500, "module_e": 5000}'::jsonb,
    15,
    'draft'
);
