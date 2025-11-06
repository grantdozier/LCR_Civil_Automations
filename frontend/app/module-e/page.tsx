'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, TextArea } from '@/components/ui/input';
import { Alert } from '@/components/ui/alert';

const MODULE_PRICING = {
  A: { name: 'Area Calculation', price: 8500, days: 5 },
  B: { name: 'Spec Extraction', price: 7500, days: 4 },
  C: { name: 'DIA Report Generator', price: 12000, days: 7 },
  D: { name: 'Plan Review QA', price: 9000, days: 5 },
  E: { name: 'Document Automation', price: 5000, days: 3 },
};

export default function ModuleEPage() {
  const [clientName, setClientName] = useState('');
  const [clientContact, setClientContact] = useState('');
  const [clientEmail, setClientEmail] = useState('');
  const [projectName, setProjectName] = useState('');
  const [projectLocation, setProjectLocation] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [selectedModules, setSelectedModules] = useState<string[]>([]);
  const [discount, setDiscount] = useState('0');
  const [rushFee, setRushFee] = useState('0');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const toggleModule = (module: string) => {
    if (selectedModules.includes(module)) {
      setSelectedModules(selectedModules.filter((m) => m !== module));
    } else {
      setSelectedModules([...selectedModules, module]);
    }
  };

  const calculatePricing = () => {
    let subtotal = 0;
    let totalDays = 0;

    selectedModules.forEach((mod) => {
      subtotal += MODULE_PRICING[mod as keyof typeof MODULE_PRICING].price;
      totalDays += MODULE_PRICING[mod as keyof typeof MODULE_PRICING].days;
    });

    // Bundle discount
    let bundleDiscount = 0;
    if (selectedModules.length >= 5) bundleDiscount = 15;
    else if (selectedModules.length >= 3) bundleDiscount = 10;
    else if (selectedModules.length >= 2) bundleDiscount = 5;

    const totalDiscount = bundleDiscount + parseFloat(discount);
    const discountAmount = (subtotal * totalDiscount) / 100;
    const discountedSubtotal = subtotal - discountAmount;
    const rushFeeAmount = (discountedSubtotal * parseFloat(rushFee)) / 100;
    const total = discountedSubtotal + rushFeeAmount;

    return {
      subtotal,
      bundleDiscount,
      totalDiscount,
      discountAmount,
      discountedSubtotal,
      rushFeeAmount,
      total,
      totalDays,
    };
  };

  const handleGenerate = async () => {
    if (!clientName || !projectName || selectedModules.length === 0) {
      setError('Please fill in all required fields and select at least one module');
      return;
    }

    setLoading(true);
    setError(null);

    // Simulate API call
    setTimeout(() => {
      const pricing = calculatePricing();
      setResult({
        proposal_id: 'PROP-2024-001',
        proposal_path: '/outputs/proposals/Proposal_ABC_Development_2024.docx',
        total_price: pricing.total,
        estimated_days: pricing.totalDays,
        modules_included: selectedModules,
        client_name: clientName,
      });
      setLoading(false);
    }, 2000);
  };

  const pricing = selectedModules.length > 0 ? calculatePricing() : null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">
          Module E: Proposal Generator
        </h1>
        <p className="text-lg text-slate-600">
          Automated proposal and document generation for drainage automation services
        </p>
      </div>

      <div className="max-w-5xl mx-auto space-y-6">
        {/* Client Information */}
        <Card title="Client Information" description="Enter client and project details">
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <Input
                label="Client Name"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder="e.g., ABC Development LLC"
                required
              />
              <Input
                label="Contact Person"
                value={clientContact}
                onChange={(e) => setClientContact(e.target.value)}
                placeholder="e.g., John Smith"
                required
              />
            </div>

            <Input
              label="Contact Email"
              type="email"
              value={clientEmail}
              onChange={(e) => setClientEmail(e.target.value)}
              placeholder="e.g., john.smith@abcdev.com"
              required
            />

            <div className="grid md:grid-cols-2 gap-4">
              <Input
                label="Project Name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., Smith Residential Development"
                required
              />
              <Input
                label="Project Location"
                value={projectLocation}
                onChange={(e) => setProjectLocation(e.target.value)}
                placeholder="e.g., Lafayette, LA"
              />
            </div>

            <TextArea
              label="Project Description"
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="Brief project description..."
              rows={3}
            />
          </div>
        </Card>

        {/* Module Selection */}
        <Card title="Select Modules" description="Choose automation services to include">
          <div className="space-y-3">
            {Object.entries(MODULE_PRICING).map(([key, module]) => (
              <div
                key={key}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedModules.includes(key)
                    ? 'bg-pink-50 border-pink-500'
                    : 'bg-slate-50 border-slate-200 hover:border-slate-300'
                }`}
                onClick={() => toggleModule(key)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selectedModules.includes(key)}
                      onChange={() => toggleModule(key)}
                      className="w-5 h-5 text-pink-600 rounded focus:ring-pink-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div>
                      <p className="font-semibold text-slate-900">
                        Module {key}: {module.name}
                      </p>
                      <p className="text-sm text-slate-600">{module.days} days estimated</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-slate-900">
                      ${module.price.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Pricing Options */}
        <Card title="Pricing Options" description="Adjust discounts and rush fees">
          <div className="grid md:grid-cols-2 gap-4">
            <Input
              type="number"
              label="Additional Discount (%)"
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
              placeholder="0"
              min="0"
              max="100"
              step="1"
            />
            <Input
              type="number"
              label="Rush Fee (%)"
              value={rushFee}
              onChange={(e) => setRushFee(e.target.value)}
              placeholder="0"
              min="0"
              max="100"
              step="1"
            />
          </div>
        </Card>

        {/* Pricing Summary */}
        {pricing && (
          <Card title="Pricing Summary" description="Proposal pricing breakdown">
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Subtotal ({selectedModules.length} modules):</span>
                <span className="font-semibold">${pricing.subtotal.toLocaleString()}</span>
              </div>

              {pricing.bundleDiscount > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Bundle Discount ({pricing.bundleDiscount}%):</span>
                  <span>-${((pricing.subtotal * pricing.bundleDiscount) / 100).toLocaleString()}</span>
                </div>
              )}

              {parseFloat(discount) > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Additional Discount ({discount}%):</span>
                  <span>
                    -${((pricing.subtotal * parseFloat(discount)) / 100).toLocaleString()}
                  </span>
                </div>
              )}

              {pricing.totalDiscount > 0 && (
                <div className="flex justify-between text-sm border-t pt-2">
                  <span className="text-slate-600">Subtotal after discounts:</span>
                  <span className="font-semibold">
                    ${pricing.discountedSubtotal.toLocaleString()}
                  </span>
                </div>
              )}

              {parseFloat(rushFee) > 0 && (
                <div className="flex justify-between text-sm text-orange-600">
                  <span>Rush Fee ({rushFee}%):</span>
                  <span>+${pricing.rushFeeAmount.toLocaleString()}</span>
                </div>
              )}

              <div className="flex justify-between text-lg font-bold border-t-2 pt-3">
                <span>Total:</span>
                <span className="text-pink-600">${pricing.total.toLocaleString()}</span>
              </div>

              <div className="bg-slate-50 rounded-lg p-3 text-sm">
                <p className="text-slate-600">
                  <strong>Estimated Timeline:</strong> {pricing.totalDays} business days
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Generate Button */}
        <div className="flex gap-4">
          <Button
            variant="primary"
            onClick={handleGenerate}
            isLoading={loading}
            disabled={selectedModules.length === 0}
            className="flex-1"
          >
            Generate Proposal
          </Button>
        </div>

        {error && (
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Result */}
        {result && (
          <Card title="Proposal Generated" description="Your proposal is ready">
            <div className="space-y-4">
              <Alert variant="success">
                <strong>Proposal generated successfully!</strong>
                <p className="mt-2">Proposal ID: {result.proposal_id}</p>
              </Alert>

              <div className="bg-slate-50 rounded-lg p-4">
                <h4 className="font-semibold text-slate-900 mb-2">Proposal Details</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Client:</span>
                    <span className="font-semibold">{result.client_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Total Price:</span>
                    <span className="font-semibold">${result.total_price.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Estimated Days:</span>
                    <span className="font-semibold">{result.estimated_days} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Modules:</span>
                    <span className="font-semibold">{result.modules_included.join(', ')}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="primary">Download Proposal (DOCX)</Button>
                <Button variant="secondary">Download Cover Letter</Button>
                <Button variant="outline">Email to Client</Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
