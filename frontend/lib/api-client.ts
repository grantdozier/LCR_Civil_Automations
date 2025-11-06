/**
 * API Client for LCR Civil Drainage Automation
 * Centralized API calls to the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchWithError(url: string, options?: RequestInit) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `API request failed with status ${response.status}`,
      errorData
    );
  }

  return response.json();
}

// ============================================================================
// Module A - Area Calculation
// ============================================================================

export const areaCalculationApi = {
  async calculate(data: {
    project_id: string;
    area_label: string;
    total_polygon: { coordinates: number[][] };
    impervious_polygons?: { coordinates: number[][] }[];
    land_use_breakdown: { land_use: string; area: number }[];
    drawing_id?: string;
  }) {
    return fetchWithError(`${API_BASE_URL}/area-calculation/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async calculateWeightedC(land_use_areas: Record<string, number>) {
    return fetchWithError(`${API_BASE_URL}/area-calculation/weighted-c`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ land_use_areas }),
    });
  },

  async parseSurveyCSV(file: File, exportGeoJSON = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('export_geojson', String(exportGeoJSON));

    return fetchWithError(`${API_BASE_URL}/area-calculation/parse-survey-csv`, {
      method: 'POST',
      body: formData,
    });
  },

  async getProjectDrainageAreas(projectId: string) {
    return fetchWithError(`${API_BASE_URL}/area-calculation/project/${projectId}/drainage-areas`);
  },

  async updateExcelTOC(templateFile: File, drainageAreas: any[]) {
    const formData = new FormData();
    formData.append('template_file', templateFile);
    formData.append('drainage_areas_json', JSON.stringify(drainageAreas));

    return fetchWithError(`${API_BASE_URL}/area-calculation/update-excel-toc`, {
      method: 'POST',
      body: formData,
    });
  },
};

// ============================================================================
// Module B - Specification Extraction
// ============================================================================

export const specExtractionApi = {
  async extractFromPDF(
    file: File,
    jurisdiction: string = 'Unknown',
    documentName?: string,
    useLangChain = false
  ) {
    const formData = new FormData();
    formData.append('file', file);

    const url = new URL(`${API_BASE_URL}/spec-extraction/extract-from-pdf`);
    url.searchParams.append('jurisdiction', jurisdiction);
    if (documentName) url.searchParams.append('document_name', documentName);
    url.searchParams.append('use_langchain', String(useLangChain));

    return fetchWithError(url.toString(), {
      method: 'POST',
      body: formData,
    });
  },

  async searchSpecs(params: {
    jurisdiction?: string;
    spec_type?: string;
    land_use?: string;
    verified_only?: boolean;
  }) {
    const url = new URL(`${API_BASE_URL}/spec-extraction/search`);
    if (params.jurisdiction) url.searchParams.append('jurisdiction', params.jurisdiction);
    if (params.spec_type) url.searchParams.append('spec_type', params.spec_type);
    if (params.land_use) url.searchParams.append('land_use', params.land_use);
    if (params.verified_only) url.searchParams.append('verified_only', 'true');

    return fetchWithError(url.toString());
  },

  async getRainfallIntensity(data: {
    duration_minutes: number;
    return_period_years: number;
    jurisdiction?: string;
  }) {
    return fetchWithError(`${API_BASE_URL}/spec-extraction/rainfall-intensity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async loadNOAAData() {
    return fetchWithError(`${API_BASE_URL}/spec-extraction/load-noaa-data`, {
      method: 'POST',
    });
  },

  async getCValues(jurisdiction = 'Lafayette UDC', landUse?: string) {
    const url = new URL(`${API_BASE_URL}/spec-extraction/c-values`);
    url.searchParams.append('jurisdiction', jurisdiction);
    if (landUse) url.searchParams.append('land_use', landUse);

    return fetchWithError(url.toString());
  },
};

// ============================================================================
// Module C - DIA Report Generator
// ============================================================================

export const diaReportApi = {
  async calculateTc(data: {
    method: string;
    flow_length_ft: number;
    elevation_change_ft: number;
    cn?: number;
    runoff_coefficient?: number;
    slope_percent?: number;
  }) {
    return fetchWithError(`${API_BASE_URL}/dia-report/calculate-tc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async calculateFlow(data: {
    c_value: number;
    intensity_in_per_hr: number;
    area_acres: number;
    storm_event: string;
    area_label?: string;
  }) {
    return fetchWithError(`${API_BASE_URL}/dia-report/calculate-flow`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async generateReport(data: {
    project_id: string;
    storm_events?: string[];
    include_exhibits?: boolean;
    include_noaa_appendix?: boolean;
    tc_method?: string;
  }) {
    return fetchWithError(`${API_BASE_URL}/dia-report/generate-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async getRunResults(runId: string) {
    return fetchWithError(`${API_BASE_URL}/dia-report/run/${runId}/results`);
  },
};

// ============================================================================
// Projects API (for all modules)
// ============================================================================

export const projectsApi = {
  async create(data: {
    name: string;
    project_number?: string;
    client_name?: string;
    location?: string;
    description?: string;
  }) {
    return fetchWithError(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  async list() {
    return fetchWithError(`${API_BASE_URL}/projects`);
  },

  async get(projectId: string) {
    return fetchWithError(`${API_BASE_URL}/projects/${projectId}`);
  },
};

export { ApiError };
