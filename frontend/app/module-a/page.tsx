'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { FileUpload } from '@/components/ui/file-upload';
import { Alert } from '@/components/ui/alert';
import { areaCalculationApi } from '@/lib/api-client';

type Tab = 'weighted-c' | 'csv-parser' | 'area-calc';

export default function ModuleAPage() {
  const [activeTab, setActiveTab] = useState<Tab>('weighted-c');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">Module A: Area Calculation</h1>
        <p className="text-lg text-slate-600">
          Automated drainage area calculation with weighted C-values
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-slate-200">
        <button
          className={`px-6 py-3 font-semibold transition-colors ${
            activeTab === 'weighted-c'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
          onClick={() => setActiveTab('weighted-c')}
        >
          Weighted C-Value Calculator
        </button>
        <button
          className={`px-6 py-3 font-semibold transition-colors ${
            activeTab === 'csv-parser'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
          onClick={() => setActiveTab('csv-parser')}
        >
          Survey CSV Parser
        </button>
        <button
          className={`px-6 py-3 font-semibold transition-colors ${
            activeTab === 'area-calc'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-slate-600 hover:text-slate-900'
          }`}
          onClick={() => setActiveTab('area-calc')}
        >
          Full Area Calculation
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'weighted-c' && <WeightedCCalculator />}
      {activeTab === 'csv-parser' && <CSVParser />}
      {activeTab === 'area-calc' && <FullAreaCalculation />}
    </div>
  );
}

// ============================================================================
// Weighted C-Value Calculator
// ============================================================================

function WeightedCCalculator() {
  const [landUses, setLandUses] = useState<Array<{ type: string; area: number }>>([
    { type: 'pavement', area: 0 },
  ]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const landUseOptions = [
    { value: 'pavement', label: 'Pavement (C=0.90)' },
    { value: 'concrete', label: 'Concrete (C=0.90)' },
    { value: 'asphalt', label: 'Asphalt (C=0.90)' },
    { value: 'roof', label: 'Roof (C=0.85)' },
    { value: 'sidewalk', label: 'Sidewalk (C=0.85)' },
    { value: 'grass_flat', label: 'Grass - Flat (C=0.10)' },
    { value: 'grass_moderate', label: 'Grass - Moderate Slope (C=0.15)' },
    { value: 'grass_steep', label: 'Grass - Steep Slope (C=0.20)' },
    { value: 'gravel', label: 'Gravel (C=0.50)' },
    { value: 'dirt', label: 'Dirt (C=0.30)' },
  ];

  const addLandUse = () => {
    setLandUses([...landUses, { type: 'pavement', area: 0 }]);
  };

  const removeLandUse = (index: number) => {
    setLandUses(landUses.filter((_, i) => i !== index));
  };

  const updateLandUse = (index: number, field: 'type' | 'area', value: string | number) => {
    const updated = [...landUses];
    updated[index] = { ...updated[index], [field]: value };
    setLandUses(updated);
  };

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const land_use_areas: Record<string, number> = {};
      landUses.forEach((lu) => {
        if (lu.area > 0) {
          land_use_areas[lu.type] = lu.area;
        }
      });

      const response = await areaCalculationApi.calculateWeightedC(land_use_areas);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate weighted C-value');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card title="Land Use Input" description="Enter areas for each land use type">
        <div className="space-y-4">
          {landUses.map((lu, index) => (
            <div key={index} className="flex gap-2 items-start">
              <Select
                value={lu.type}
                onChange={(e) => updateLandUse(index, 'type', e.target.value)}
                options={landUseOptions}
                className="flex-1"
              />
              <Input
                type="number"
                value={lu.area}
                onChange={(e) => updateLandUse(index, 'area', parseFloat(e.target.value) || 0)}
                placeholder="Area (sq ft)"
                className="w-32"
              />
              <Button
                variant="danger"
                size="sm"
                onClick={() => removeLandUse(index)}
                disabled={landUses.length === 1}
              >
                Remove
              </Button>
            </div>
          ))}

          <div className="flex gap-2">
            <Button variant="outline" onClick={addLandUse} className="flex-1">
              Add Land Use
            </Button>
            <Button variant="primary" onClick={handleCalculate} isLoading={loading} className="flex-1">
              Calculate C-Value
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="error" className="mt-4">
            {error}
          </Alert>
        )}
      </Card>

      <Card title="Results" description="Weighted runoff coefficient calculation">
        {result ? (
          <div className="space-y-4">
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 text-center">
              <p className="text-sm text-blue-600 font-semibold mb-2">Weighted C-Value</p>
              <p className="text-5xl font-bold text-blue-900">{result.weighted_c_value.toFixed(3)}</p>
            </div>

            <div className="border-t pt-4">
              <h4 className="font-semibold text-slate-900 mb-3">Breakdown</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Total Area:</span>
                  <span className="font-semibold">{result.total_area.toLocaleString()} sq ft</span>
                </div>
                {Object.entries(result.breakdown).map(([type, data]: [string, any]) => (
                  <div key={type} className="flex justify-between text-sm pl-4">
                    <span className="text-slate-600">{type}:</span>
                    <span>
                      {data.area.toLocaleString()} sq ft × C={data.c_value.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <Alert variant="info">
              <strong>Formula:</strong> C_weighted = (C₁×A₁ + C₂×A₂ + ... + Cₙ×Aₙ) / A_total
            </Alert>
          </div>
        ) : (
          <div className="text-center text-slate-500 py-12">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-slate-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <p>Enter land use areas and click Calculate to see results</p>
          </div>
        )}
      </Card>
    </div>
  );
}

// ============================================================================
// CSV Parser
// ============================================================================

function CSVParser() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [exportGeoJSON, setExportGeoJSON] = useState(false);

  const handleParse = async () => {
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await areaCalculationApi.parseSurveyCSV(file, exportGeoJSON);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to parse CSV file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card title="Upload Survey CSV" description="Parse Civil 3D or survey equipment CSV files">
        <div className="space-y-4">
          <FileUpload
            accept=".csv"
            label="Survey CSV File"
            description="Required columns: Point Name, Northing, Easting, Elevation"
            onFileSelect={setFile}
            disabled={loading}
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="exportGeoJSON"
              checked={exportGeoJSON}
              onChange={(e) => setExportGeoJSON(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="exportGeoJSON" className="text-sm text-slate-700">
              Export to GeoJSON format
            </label>
          </div>

          <Button variant="primary" onClick={handleParse} isLoading={loading} disabled={!file}>
            Parse CSV File
          </Button>

          {error && (
            <Alert variant="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </div>
      </Card>

      {result && (
        <Card title="Parsing Results" description={`Processed ${result.filename}`}>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-600 mb-1">Total Points</p>
                <p className="text-2xl font-bold text-slate-900">{result.total_points}</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-600 mb-1">Min Elevation</p>
                <p className="text-2xl font-bold text-slate-900">
                  {result.statistics.elevation_min?.toFixed(2)} ft
                </p>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-600 mb-1">Max Elevation</p>
                <p className="text-2xl font-bold text-slate-900">
                  {result.statistics.elevation_max?.toFixed(2)} ft
                </p>
              </div>
            </div>

            {result.geojson_path && (
              <Alert variant="success">
                <strong>GeoJSON exported:</strong> {result.geojson_path}
              </Alert>
            )}

            <div className="border-t pt-4">
              <h4 className="font-semibold text-slate-900 mb-3">
                Point Preview (first {Math.min(result.points_preview.length, 10)} points)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Point Name</th>
                      <th className="px-4 py-2 text-right">Northing</th>
                      <th className="px-4 py-2 text-right">Easting</th>
                      <th className="px-4 py-2 text-right">Elevation</th>
                      <th className="px-4 py-2 text-left">Code</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.points_preview.slice(0, 10).map((point: any, i: number) => (
                      <tr key={i} className="border-t">
                        <td className="px-4 py-2">{point.name}</td>
                        <td className="px-4 py-2 text-right">{point.northing.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right">{point.easting.toFixed(2)}</td>
                        <td className="px-4 py-2 text-right">{point.elevation.toFixed(2)}</td>
                        <td className="px-4 py-2">{point.code || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Full Area Calculation (simplified version)
// ============================================================================

function FullAreaCalculation() {
  return (
    <Card title="Full Area Calculation" description="Calculate drainage areas with polygon coordinates">
      <Alert variant="info">
        <strong>Feature coming soon!</strong>
        <p className="mt-2">
          This feature will allow you to input polygon coordinates and calculate total drainage areas,
          impervious/pervious splits, and weighted C-values all at once. For now, use the individual tools above.
        </p>
      </Alert>
    </Card>
  );
}
