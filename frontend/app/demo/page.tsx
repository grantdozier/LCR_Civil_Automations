'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { demoApi } from '@/lib/api-client';

export default function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'initial' | 'project-created' | 'dia-completed'>('initial');
  const [projectData, setProjectData] = useState<any>(null);
  const [runData, setRunData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string[]>([]);

  const addProgress = (message: string) => {
    setProgress(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const handleSetupProject = async () => {
    setLoading(true);
    setError(null);
    setProgress([]);
    addProgress('Starting demo project setup...');

    try {
      addProgress('Creating demo project with sample data...');
      const result = await demoApi.setupProject();
      setProjectData(result);
      setStep('project-created');
      addProgress('✓ Demo project created successfully!');
      addProgress(`Project: ${result.project_name}`);
      addProgress(`Project Number: ${result.project_number}`);
      addProgress(`Drainage Areas: ${result.drainage_areas}`);
      addProgress(`Total Area: ${result.total_area_acres.toFixed(3)} acres`);
    } catch (err: any) {
      setError(err.message || 'Failed to setup demo project');
      addProgress('✗ Error: ' + (err.message || 'Failed to setup demo project'));
    } finally {
      setLoading(false);
    }
  };

  const handleRunDIA = async () => {
    setLoading(true);
    setError(null);
    addProgress('Starting DIA generation workflow...');

    try {
      addProgress('Processing drainage areas...');
      addProgress('Calculating Time of Concentration (Tc)...');

      const result = await demoApi.runDIA({
        project_id: projectData.project_id,
        storm_events: ['10-year', '25-year'],
        tc_method: 'nrcs',
      });

      addProgress('Querying NOAA Atlas 14 rainfall intensities...');
      addProgress('Calculating peak flows using Rational Method (Q=CiA)...');
      addProgress('Generating DIA report and exhibits...');

      setRunData(result);
      setStep('dia-completed');

      addProgress('✓ DIA workflow completed successfully!');
      addProgress(`Run ID: ${result.run_id}`);
      addProgress(`Total Results: ${result.total_results}`);
      addProgress(`Status: ${result.status}`);
      
      // Auto-download files
      if (result.results_summary?.report_paths) {
        addProgress('📥 Downloading generated files...');
        await downloadGeneratedFiles(result.results_summary.report_paths);
        addProgress('✓ All files downloaded to your computer!');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to run DIA workflow');
      addProgress('✗ Error: ' + (err.message || 'Failed to run DIA workflow'));
    } finally {
      setLoading(false);
    }
  };

  const downloadGeneratedFiles = async (reportPaths: any) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const files: string[] = [];
    
    if (reportPaths.main_report) {
      files.push(reportPaths.main_report);
    }
    if (reportPaths.exhibits && Array.isArray(reportPaths.exhibits)) {
      files.push(...reportPaths.exhibits);
    }

    for (const filePath of files) {
      const filename = filePath.split('/').pop();
      if (filename) {
        try {
          // NEXT_PUBLIC_API_URL already includes /api/v1, so just add the endpoint path
          const downloadUrl = `${apiUrl}/dia-report/download/${filename}`;
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = filename;
          link.target = '_blank';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          await new Promise(resolve => setTimeout(resolve, 500)); // Delay between downloads
        } catch (err) {
          console.error(`Failed to download ${filename}:`, err);
        }
      }
    }
  };

  const downloadFile = async (filePath: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const filename = filePath.split('/').pop();
    if (filename) {
      const downloadUrl = `${apiUrl}/api/v1/dia-report/download/${filename}`;
      window.open(downloadUrl, '_blank');
    }
  };

  const handleReset = () => {
    setStep('initial');
    setProjectData(null);
    setRunData(null);
    setError(null);
    setProgress([]);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">
          DEMO: Complete DIA Workflow
        </h1>
        <p className="text-lg text-slate-600">
          One-click demonstration of the complete Drainage Impact Analysis workflow
        </p>
      </div>

      {/* Info Card */}
      <Card className="mb-6 bg-blue-50 border-blue-200">
        <div className="p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-3">
            What This Demo Shows
          </h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <h3 className="font-semibold mb-2">Sample Project:</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Acadian Village Parking Expansion</li>
                <li>3 drainage areas (1.274 acres total)</li>
                <li>Mixed land uses: Pavement, Grass, Gravel, Roof</li>
                <li>Lafayette, LA location</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Calculations Performed:</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Time of Concentration (Tc) - NRCS method</li>
                <li>NOAA Atlas 14 rainfall intensities</li>
                <li>Peak flow using Rational Method (Q=CiA)</li>
                <li>10-year and 25-year storm analysis</li>
              </ul>
            </div>
          </div>
          <div className="mt-4 p-3 bg-blue-100 rounded">
            <p className="text-sm font-semibold text-blue-900">
              ⚡ Time Savings: Manual process ~2-3 hours → Automated ~6 seconds (99%+ faster!)
            </p>
          </div>
        </div>
      </Card>

      {/* Main Action Buttons */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Step 1: Setup Project */}
        <Card className={step === 'initial' ? 'border-2 border-purple-600' : ''}>
          <div className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                step === 'initial' ? 'bg-purple-600' : 'bg-green-600'
              }`}>
                {step === 'initial' ? '1' : '✓'}
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Step 1: Setup Demo Project</h3>
                <p className="text-sm text-slate-600">Create sample project with drainage areas</p>
              </div>
            </div>

            <Button
              onClick={handleSetupProject}
              disabled={loading || step !== 'initial'}
              className="w-full h-14 text-lg font-semibold"
              variant={step === 'initial' ? 'primary' : 'secondary'}
            >
              {loading && step === 'initial' ? 'Creating Project...' :
               step === 'initial' ? '🚀 Initialize Demo Project' : '✓ Project Created'}
            </Button>

            {projectData && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg text-sm">
                <p className="font-semibold text-slate-900 mb-2">Project Created:</p>
                <p className="text-slate-700">{projectData.project_name}</p>
                <p className="text-slate-600 text-xs mt-1">
                  {projectData.drainage_areas} drainage areas • {projectData.total_area_acres.toFixed(3)} acres
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Step 2: Run DIA */}
        <Card className={step === 'project-created' ? 'border-2 border-purple-600' : ''}>
          <div className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                step === 'project-created' ? 'bg-purple-600' :
                step === 'dia-completed' ? 'bg-green-600' : 'bg-slate-300'
              }`}>
                {step === 'dia-completed' ? '✓' : '2'}
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Step 2: Generate DIA Report</h3>
                <p className="text-sm text-slate-600">Run complete workflow and create reports</p>
              </div>
            </div>

            <Button
              onClick={handleRunDIA}
              disabled={loading || step !== 'project-created'}
              className="w-full h-14 text-lg font-semibold"
              variant={step === 'project-created' ? 'primary' : 'secondary'}
            >
              {loading && step === 'project-created' ? 'Generating Reports...' :
               step === 'dia-completed' ? '✓ DIA Completed' : '📊 Run DIA Generation'}
            </Button>

            {runData && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg text-sm border border-green-200">
                <p className="font-semibold text-green-900 mb-2">✓ Workflow Completed!</p>
                <p className="text-green-700">Status: {runData.status}</p>
                <p className="text-green-600 text-xs mt-1">
                  {runData.total_results} calculations performed
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Progress Log */}
      {progress.length > 0 && (
        <Card className="mb-6">
          <div className="p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-3">Progress Log</h3>
            <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-green-400 max-h-64 overflow-y-auto">
              {progress.map((msg, idx) => (
                <div key={idx} className="mb-1">
                  {msg}
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Alert variant="error" className="mb-6">
          <h4 className="font-bold mb-1">Error</h4>
          <p>{error}</p>
        </Alert>
      )}

      {/* Results Display */}
      {runData && runData.results_summary && (
        <Card className="mb-6">
          <div className="p-6">
            <h3 className="text-xl font-bold text-slate-900 mb-4">Detailed Results</h3>

            {/* Project Info */}
            <div className="mb-6">
              <h4 className="font-semibold text-slate-700 mb-2">Project Information</h4>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-600">Project: <span className="font-semibold text-slate-900">
                    {runData.results_summary.project_info?.name}
                  </span></p>
                  <p className="text-slate-600">Number: <span className="font-semibold text-slate-900">
                    {runData.results_summary.project_info?.number}
                  </span></p>
                </div>
                <div>
                  <p className="text-slate-600">Client: <span className="font-semibold text-slate-900">
                    {runData.results_summary.project_info?.client}
                  </span></p>
                  <p className="text-slate-600">Location: <span className="font-semibold text-slate-900">
                    {runData.results_summary.project_info?.location}
                  </span></p>
                </div>
              </div>
            </div>

            {/* Results by Storm Event */}
            {Object.entries(runData.results_summary.results_by_storm || {}).map(([stormEvent, results]: [string, any]) => (
              <div key={stormEvent} className="mb-6">
                <h4 className="font-semibold text-slate-700 mb-3">{stormEvent} Storm Event</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-4 py-2 text-left">Area</th>
                        <th className="px-4 py-2 text-right">C</th>
                        <th className="px-4 py-2 text-right">i (in/hr)</th>
                        <th className="px-4 py-2 text-right">A (acres)</th>
                        <th className="px-4 py-2 text-right">Tc (min)</th>
                        <th className="px-4 py-2 text-right font-bold">Q (cfs)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Array.isArray(results) && results.map((result: any, idx: number) => (
                        <tr key={idx} className="border-t border-slate-200">
                          <td className="px-4 py-2 font-semibold">{result.drainage_area_label}</td>
                          <td className="px-4 py-2 text-right">{result.c_value?.toFixed(3)}</td>
                          <td className="px-4 py-2 text-right">{result.i_value?.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right">{result.area_acres?.toFixed(3)}</td>
                          <td className="px-4 py-2 text-right">{result.tc_minutes?.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right font-bold text-purple-700">
                            {result.peak_flow_cfs?.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}

            {/* Formula Explanation */}
            <div className="mt-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <h4 className="font-semibold text-purple-900 mb-2">Rational Method Formula</h4>
              <p className="text-purple-800 font-mono text-lg mb-2">Q = C × i × A</p>
              <div className="text-sm text-purple-700 space-y-1">
                <p><strong>Q</strong> = Peak flow rate (cubic feet per second, cfs)</p>
                <p><strong>C</strong> = Weighted runoff coefficient (0.0 to 1.0)</p>
                <p><strong>i</strong> = Rainfall intensity (inches per hour)</p>
                <p><strong>A</strong> = Drainage area (acres)</p>
              </div>
            </div>

            {/* Report Files */}
            {runData.results_summary.report_paths && (
              <div className="mt-6">
                <h4 className="font-semibold text-slate-700 mb-3">Generated Files (Downloaded to Your Computer)</h4>
                <div className="space-y-2 text-sm">
                  <div className="p-3 bg-green-50 rounded border border-green-200 hover:bg-green-100 transition cursor-pointer"
                       onClick={() => downloadFile(runData.results_summary.report_paths.main_report)}>
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-semibold text-green-900">📄 Main Report:</p>
                        <p className="text-green-700 text-xs font-mono break-all">
                          {runData.results_summary.report_paths.main_report.split('/').pop()}
                        </p>
                      </div>
                      <Button
                        onClick={(e) => { e.stopPropagation(); downloadFile(runData.results_summary.report_paths.main_report); }}
                        variant="secondary"
                        className="ml-2 text-xs"
                      >
                        ⬇️ Download
                      </Button>
                    </div>
                  </div>
                  {runData.results_summary.report_paths.exhibits?.map((exhibit: string, idx: number) => (
                    <div key={idx} className="p-3 bg-green-50 rounded border border-green-200 hover:bg-green-100 transition cursor-pointer"
                         onClick={() => downloadFile(exhibit)}>
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-semibold text-green-900">📊 Exhibit {idx + 1}:</p>
                          <p className="text-green-700 text-xs font-mono break-all">{exhibit.split('/').pop()}</p>
                        </div>
                        <Button
                          onClick={(e) => { e.stopPropagation(); downloadFile(exhibit); }}
                          variant="secondary"
                          className="ml-2 text-xs"
                        >
                          ⬇️ Download
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
                  <p className="text-sm text-blue-800">
                    💡 <strong>Tip:</strong> Files were automatically downloaded when the workflow completed. 
                    Click any file above to download again.
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Reset Button */}
      {step !== 'initial' && (
        <div className="flex justify-center">
          <Button
            onClick={handleReset}
            variant="secondary"
            className="px-8"
          >
            🔄 Reset Demo
          </Button>
        </div>
      )}

      {/* Footer Info */}
      <div className="mt-8 text-center text-sm text-slate-500">
        <p>This demonstration uses realistic sample data based on Lafayette, LA specifications.</p>
        <p className="mt-1">All calculations are performed using industry-standard methods and NOAA Atlas 14 data.</p>
      </div>
    </div>
  );
}
