'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { FileUpload } from '@/components/ui/file-upload';
import { Alert } from '@/components/ui/alert';
import { specExtractionApi } from '@/lib/api-client';

type Tab = 'pdf-extract' | 'search-specs' | 'c-values' | 'rainfall';

export default function ModuleBPage() {
  const [activeTab, setActiveTab] = useState<Tab>('pdf-extract');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">Module B: Specification Extraction</h1>
        <p className="text-lg text-slate-600">
          UDC & DOTD specification extraction with AI-powered parsing
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-slate-200 overflow-x-auto">
        <TabButton active={activeTab === 'pdf-extract'} onClick={() => setActiveTab('pdf-extract')}>
          PDF Extraction
        </TabButton>
        <TabButton active={activeTab === 'search-specs'} onClick={() => setActiveTab('search-specs')}>
          Search Specs
        </TabButton>
        <TabButton active={activeTab === 'c-values'} onClick={() => setActiveTab('c-values')}>
          C-Values
        </TabButton>
        <TabButton active={activeTab === 'rainfall'} onClick={() => setActiveTab('rainfall')}>
          Rainfall Data
        </TabButton>
      </div>

      {/* Tab Content */}
      {activeTab === 'pdf-extract' && <PDFExtraction />}
      {activeTab === 'search-specs' && <SearchSpecs />}
      {activeTab === 'c-values' && <CValues />}
      {activeTab === 'rainfall' && <RainfallData />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      className={`px-6 py-3 font-semibold transition-colors whitespace-nowrap ${
        active ? 'border-b-2 border-green-600 text-green-600' : 'text-slate-600 hover:text-slate-900'
      }`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

// ============================================================================
// PDF Extraction
// ============================================================================

function PDFExtraction() {
  const [file, setFile] = useState<File | null>(null);
  const [jurisdiction, setJurisdiction] = useState('Lafayette UDC');
  const [documentName, setDocumentName] = useState('');
  const [useLangChain, setUseLangChain] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExtract = async () => {
    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await specExtractionApi.extractFromPDF(
        file,
        jurisdiction,
        documentName || undefined,
        useLangChain
      );
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to extract specifications from PDF');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card
        title="Upload Regulatory PDF"
        description="Extract C-values and rainfall data from UDC, DOTD, or NOAA documents"
      >
        <div className="space-y-4">
          <FileUpload
            accept=".pdf"
            label="PDF Document"
            description="Upload UDC, DOTD Hydraulic Manual, or NOAA Atlas 14"
            onFileSelect={setFile}
            disabled={loading}
          />

          <div className="grid md:grid-cols-2 gap-4">
            <Input
              label="Jurisdiction"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              placeholder="e.g., Lafayette UDC, DOTD"
            />
            <Input
              label="Document Name (Optional)"
              value={documentName}
              onChange={(e) => setDocumentName(e.target.value)}
              placeholder="Defaults to filename"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="useLangChain"
              checked={useLangChain}
              onChange={(e) => setUseLangChain(e.target.checked)}
              className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
            />
            <label htmlFor="useLangChain" className="text-sm text-slate-700">
              Use AI-powered extraction (LangChain) - more accurate but slower
            </label>
          </div>

          <Button variant="primary" onClick={handleExtract} isLoading={loading} disabled={!file}>
            Extract Specifications
          </Button>

          {error && (
            <Alert variant="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </div>
      </Card>

      {result && (
        <Card title="Extraction Results" description={`Processed ${result.filename}`}>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-sm text-green-600 mb-1">Total Pages</p>
                <p className="text-2xl font-bold text-green-900">{result.total_pages}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-sm text-green-600 mb-1">Specs Extracted</p>
                <p className="text-2xl font-bold text-green-900">{result.specifications_extracted}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-sm text-green-600 mb-1">Success Rate</p>
                <p className="text-2xl font-bold text-green-900">
                  {Math.round((result.specifications_extracted / result.total_pages) * 100)}%
                </p>
              </div>
            </div>

            {result.specifications_extracted > 0 && (
              <Alert variant="success">
                Successfully extracted {result.specifications_extracted} specification(s) and saved to database
              </Alert>
            )}

            <div className="border-t pt-4">
              <h4 className="font-semibold text-slate-900 mb-3">Extracted Specifications</h4>
              <div className="space-y-3">
                {result.specifications.map((spec: any, i: number) => (
                  <div key={i} className="bg-slate-50 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-slate-900">{spec.spec_type}</span>
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        {spec.jurisdiction}
                      </span>
                    </div>
                    {spec.land_use_type && (
                      <p className="text-sm text-slate-600">
                        <strong>Land Use:</strong> {spec.land_use_type}
                      </p>
                    )}
                    {spec.c_value_recommended && (
                      <p className="text-sm text-slate-600">
                        <strong>C-Value:</strong> {spec.c_value_recommended}
                      </p>
                    )}
                    {spec.intensity_in_per_hr && (
                      <p className="text-sm text-slate-600">
                        <strong>Intensity:</strong> {spec.intensity_in_per_hr} in/hr (
                        {spec.duration_minutes} min, {spec.return_period_years}-year)
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Search Specifications
// ============================================================================

function SearchSpecs() {
  const [jurisdiction, setJurisdiction] = useState('');
  const [specType, setSpecType] = useState('');
  const [landUse, setLandUse] = useState('');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await specExtractionApi.searchSpecs({
        jurisdiction: jurisdiction || undefined,
        spec_type: specType || undefined,
        land_use: landUse || undefined,
        verified_only: verifiedOnly,
      });
      setResults(response);
    } catch (err: any) {
      setError(err.message || 'Failed to search specifications');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card title="Search Specifications Database" description="Find C-values and rainfall data">
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Input
              label="Jurisdiction"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              placeholder="e.g., Lafayette UDC"
            />
            <Select
              label="Specification Type"
              value={specType}
              onChange={(e) => setSpecType(e.target.value)}
              options={[
                { value: '', label: 'All Types' },
                { value: 'runoff_coefficient', label: 'Runoff Coefficient (C-value)' },
                { value: 'rainfall_intensity', label: 'Rainfall Intensity' },
                { value: 'tc_limit', label: 'Time of Concentration Limit' },
                { value: 'detention_requirement', label: 'Detention Requirement' },
              ]}
            />
          </div>

          <Input
            label="Land Use Type"
            value={landUse}
            onChange={(e) => setLandUse(e.target.value)}
            placeholder="e.g., pavement, grass"
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="verifiedOnly"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
              className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
            />
            <label htmlFor="verifiedOnly" className="text-sm text-slate-700">
              Show only verified specifications
            </label>
          </div>

          <Button variant="primary" onClick={handleSearch} isLoading={loading}>
            Search Database
          </Button>

          {error && (
            <Alert variant="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </div>
      </Card>

      {results.length > 0 && (
        <Card title="Search Results" description={`Found ${results.length} specification(s)`}>
          <div className="space-y-3">
            {results.map((spec, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="font-semibold text-slate-900">{spec.spec_type}</span>
                    {spec.verified && (
                      <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Verified
                      </span>
                    )}
                  </div>
                  <span className="text-sm text-slate-600">{spec.jurisdiction}</span>
                </div>
                <p className="text-sm text-slate-600 mb-1">
                  <strong>Document:</strong> {spec.document_name}
                </p>
                {spec.land_use_type && (
                  <p className="text-sm text-slate-600">
                    <strong>Land Use:</strong> {spec.land_use_type}
                  </p>
                )}
                {spec.c_value_recommended && (
                  <p className="text-sm text-slate-600">
                    <strong>C-Value:</strong> {spec.c_value_recommended}
                  </p>
                )}
                {spec.intensity_in_per_hr && (
                  <p className="text-sm text-slate-600">
                    <strong>Intensity:</strong> {spec.intensity_in_per_hr} in/hr (
                    {spec.duration_minutes} min, {spec.return_period_years}-year)
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// C-Values
// ============================================================================

function CValues() {
  const [jurisdiction, setJurisdiction] = useState('Lafayette UDC');
  const [landUse, setLandUse] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await specExtractionApi.getCValues(jurisdiction, landUse || undefined);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch C-values');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card title="Runoff Coefficients (C-Values)" description="Get C-values for different land uses">
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Input
              label="Jurisdiction"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              placeholder="e.g., Lafayette UDC"
            />
            <Input
              label="Land Use (Optional)"
              value={landUse}
              onChange={(e) => setLandUse(e.target.value)}
              placeholder="e.g., pavement, grass"
            />
          </div>

          <Button variant="primary" onClick={handleFetch} isLoading={loading}>
            Get C-Values
          </Button>

          {error && (
            <Alert variant="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </div>
      </Card>

      {result && (
        <Card title="C-Values" description={`${result.total_results} result(s) from ${result.jurisdiction}`}>
          {result.c_values.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left">Land Use Type</th>
                    <th className="px-4 py-2 text-center">Min C-Value</th>
                    <th className="px-4 py-2 text-center">Recommended</th>
                    <th className="px-4 py-2 text-center">Max C-Value</th>
                  </tr>
                </thead>
                <tbody>
                  {result.c_values.map((cv: any, i: number) => (
                    <tr key={i} className="border-t">
                      <td className="px-4 py-2">{cv.land_use_type}</td>
                      <td className="px-4 py-2 text-center">{cv.c_value_min?.toFixed(2) || '-'}</td>
                      <td className="px-4 py-2 text-center font-semibold">
                        {cv.c_value_recommended?.toFixed(2) || '-'}
                      </td>
                      <td className="px-4 py-2 text-center">{cv.c_value_max?.toFixed(2) || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Alert variant="warning">No C-values found for the specified criteria</Alert>
          )}
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Rainfall Data
// ============================================================================

function RainfallData() {
  const [duration, setDuration] = useState('12.5');
  const [returnPeriod, setReturnPeriod] = useState('10');
  const [loading, setLoading] = useState(false);
  const [loadingNOAA, setLoadingNOAA] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await specExtractionApi.getRainfallIntensity({
        duration_minutes: parseFloat(duration),
        return_period_years: parseInt(returnPeriod),
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to get rainfall intensity');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadNOAA = async () => {
    setLoadingNOAA(true);
    setError(null);

    try {
      const response = await specExtractionApi.loadNOAAData();
      setError(null);
      Alert({ variant: 'success', children: response.message });
    } catch (err: any) {
      setError(err.message || 'Failed to load NOAA data');
    } finally {
      setLoadingNOAA(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card title="Rainfall Intensity Query" description="Get rainfall intensity from NOAA Atlas 14">
        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Input
              type="number"
              label="Duration (minutes)"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder="e.g., 12.5"
              step="0.1"
            />
            <Select
              label="Return Period"
              value={returnPeriod}
              onChange={(e) => setReturnPeriod(e.target.value)}
              options={[
                { value: '10', label: '10-year storm' },
                { value: '25', label: '25-year storm' },
                { value: '50', label: '50-year storm' },
                { value: '100', label: '100-year storm' },
              ]}
            />
          </div>

          <div className="flex gap-2">
            <Button variant="primary" onClick={handleQuery} isLoading={loading} className="flex-1">
              Query Intensity
            </Button>
            <Button variant="secondary" onClick={handleLoadNOAA} isLoading={loadingNOAA}>
              Load NOAA Data
            </Button>
          </div>

          {error && (
            <Alert variant="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </div>
      </Card>

      {result && (
        <Card title="Rainfall Intensity Result">
          <div className="space-y-4">
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 text-center">
              <p className="text-sm text-green-600 font-semibold mb-2">Rainfall Intensity</p>
              <p className="text-5xl font-bold text-green-900">{result.intensity_in_per_hr.toFixed(2)}</p>
              <p className="text-sm text-green-600 mt-2">inches per hour</p>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-sm text-slate-600 mb-1">Duration</p>
                <p className="text-lg font-semibold">{result.duration_minutes} minutes</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-sm text-slate-600 mb-1">Return Period</p>
                <p className="text-lg font-semibold">{result.return_period_years}-year</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-sm text-slate-600 mb-1">Source</p>
                <p className="text-lg font-semibold text-xs">{result.source}</p>
              </div>
            </div>

            {result.interpolated && (
              <Alert variant="info">
                This value was interpolated from available NOAA Atlas 14 data points
              </Alert>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
