'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileUpload } from '@/components/ui/file-upload';
import { Alert } from '@/components/ui/alert';

export default function ModuleDPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    // Simulate API call
    setTimeout(() => {
      setResult({
        sheets_checked: 15,
        summary: {
          total_checks: 45,
          passed: 38,
          failed: 7,
          pass_rate: 84.4,
          critical_failures: 2,
          warnings: 5,
          info: 0,
          overall_status: 'needs_revision',
        },
        results: [
          {
            rule_id: 'title_block',
            passed: true,
            sheet_number: 'C-7',
            message: 'Title block is complete',
            severity: 'critical',
          },
          {
            rule_id: 'scale_bar',
            passed: false,
            sheet_number: 'C-9',
            message: 'Scale bar missing',
            severity: 'critical',
          },
          {
            rule_id: 'north_arrow',
            passed: false,
            sheet_number: 'C-10',
            message: 'North arrow not found',
            severity: 'warning',
          },
        ],
      });
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">Module D: Plan Review & QA</h1>
        <p className="text-lg text-slate-600">
          Automated plan set compliance checking and quality assurance
        </p>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        <Card
          title="Upload Plan Set"
          description="Upload PDF plan set for automated compliance checking"
        >
          <div className="space-y-4">
            <FileUpload
              accept=".pdf"
              label="PDF Plan Set"
              description="Multi-sheet engineering plan set (C-series, D-series, etc.)"
              onFileSelect={setFile}
              disabled={loading}
            />

            <Button variant="primary" onClick={handleCheck} isLoading={loading} disabled={!file}>
              Run Compliance Check
            </Button>

            {error && (
              <Alert variant="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
          </div>
        </Card>

        {result && (
          <>
            <Card title="Compliance Summary">
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-slate-600 mb-1">Total Checks</p>
                    <p className="text-2xl font-bold">{result.summary.total_checks}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-green-600 mb-1">Passed</p>
                    <p className="text-2xl font-bold text-green-900">{result.summary.passed}</p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-red-600 mb-1">Failed</p>
                    <p className="text-2xl font-bold text-red-900">{result.summary.failed}</p>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-orange-600 mb-1">Pass Rate</p>
                    <p className="text-2xl font-bold text-orange-900">
                      {result.summary.pass_rate.toFixed(1)}%
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <div>
                    <p className="font-semibold text-orange-900">Overall Status</p>
                    <p className="text-sm text-orange-700">
                      {result.summary.critical_failures} critical failure(s),{' '}
                      {result.summary.warnings} warning(s)
                    </p>
                  </div>
                  <div className="px-4 py-2 bg-orange-200 text-orange-900 rounded font-semibold">
                    {result.summary.overall_status.replace('_', ' ').toUpperCase()}
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Detailed Results" description={`Checked ${result.sheets_checked} sheets`}>
              <div className="space-y-3">
                {result.results.map((check: any, i: number) => (
                  <div
                    key={i}
                    className={`border rounded-lg p-4 ${
                      check.passed
                        ? 'bg-green-50 border-green-200'
                        : check.severity === 'critical'
                        ? 'bg-red-50 border-red-200'
                        : 'bg-yellow-50 border-yellow-200'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-2">
                        {check.passed ? (
                          <svg
                            className="w-5 h-5 text-green-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="w-5 h-5 text-red-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        )}
                        <span className="font-semibold">{check.message}</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        <span className="text-xs px-2 py-1 bg-white rounded">{check.sheet_number}</span>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            check.severity === 'critical'
                              ? 'bg-red-200 text-red-900'
                              : 'bg-yellow-200 text-yellow-900'
                          }`}
                        >
                          {check.severity}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t">
                <Button variant="primary">Download QA Report (PDF)</Button>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
