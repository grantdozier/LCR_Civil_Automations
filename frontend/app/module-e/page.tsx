'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input, TextArea } from '@/components/ui/input';
import { Alert } from '@/components/ui/alert';

const SERVICE_PRICING = {
  DIA: { name: 'Drainage Impact Analysis Report', price: 4500, days: 10, description: 'Complete 58+ page DIA with Rational Method' },
  GRADING: { name: 'Grading Plan Review & Design', price: 3500, days: 8, description: 'Professional grading plan development and review' },
  DETENTION: { name: 'Detention Pond Design', price: 5000, days: 12, description: 'Stormwater detention facility design' },
  TOC: { name: 'Time of Concentration Analysis', price: 1500, days: 3, description: 'TOC calculations using multiple methods' },
  REVIEW: { name: 'Plan Review & QA Services', price: 2500, days: 5, description: 'Comprehensive plan review for compliance' },
  SURVEY: { name: 'Survey Coordination', price: 2000, days: 4, description: 'Survey data review and coordination' },
  SUBMITTAL: { name: 'Submittal Package Prep', price: 1200, days: 2, description: 'Professional submittal package assembly' },
  CONSTRUCTION: { name: 'Construction Observation', price: 1800, days: 1, description: 'On-site construction observation (per visit)' },
  STORMWATER: { name: 'Stormwater Management Plan', price: 3800, days: 9, description: 'SWMP with BMP design' },
};

export default function ModuleEPage() {
  const [clientName, setClientName] = useState('');
  const [clientContact, setClientContact] = useState('');
  const [clientEmail, setClientEmail] = useState('');
  const [projectName, setProjectName] = useState('');
  const [projectLocation, setProjectLocation] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [jurisdiction, setJurisdiction] = useState('Lafayette UDC');
  const [projectType, setProjectType] = useState('Commercial');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [discount, setDiscount] = useState('0');
  const [rushFee, setRushFee] = useState('0');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const toggleService = (service: string) => {
    if (selectedServices.includes(service)) {
      setSelectedServices(selectedServices.filter((s) => s !== service));
    } else {
      setSelectedServices([...selectedServices, service]);
    }
  };

  const calculatePricing = () => {
    let subtotal = 0;
    let totalDays = 0;

    selectedServices.forEach((service) => {
      subtotal += SERVICE_PRICING[service as keyof typeof SERVICE_PRICING].price;
      totalDays += SERVICE_PRICING[service as keyof typeof SERVICE_PRICING].days;
    });

    // Package discount
    let packageDiscount = 0;
    if (selectedServices.length >= 7) packageDiscount = 15;
    else if (selectedServices.length >= 5) packageDiscount = 10;
    else if (selectedServices.length >= 3) packageDiscount = 5;

    const totalDiscount = packageDiscount + parseFloat(discount);
    const discountAmount = (subtotal * totalDiscount) / 100;
    const discountedSubtotal = subtotal - discountAmount;
    const rushFeeAmount = (discountedSubtotal * parseFloat(rushFee)) / 100;
    const total = discountedSubtotal + rushFeeAmount;

    return {
      subtotal,
      packageDiscount,
      totalDiscount,
      discountAmount,
      discountedSubtotal,
      rushFeeAmount,
      total,
      totalDays,
    };
  };

  const handleGenerate = async () => {
    if (!clientName || !projectName || selectedServices.length === 0) {
      setError('Please fill in all required fields and select at least one service');
      return;
    }

    setLoading(true);
    setError(null);

    // Simulate API call
    setTimeout(() => {
      const pricing = calculatePricing();
      setResult({
        proposal_id: 'PROP-2024-001',
        proposal_path: '/outputs/proposals/Proposal_LCR_Client_2024.docx',
        total_price: pricing.total,
        estimated_days: pricing.totalDays,
        services_included: selectedServices,
        client_name: clientName,
      });
      setLoading(false);
    }, 2000);
  };

  const pricing = selectedServices.length > 0 ? calculatePricing() : null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">
          Module E: Civil Engineering Proposal Generator
        </h1>
        <p className="text-lg text-slate-600">
          Generate professional proposals for LCR & Company's civil engineering and drainage services
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
                placeholder="e.g., Lafayette Parish School Board"
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
              placeholder="e.g., john.smith@lpss.edu"
              required
            />

            <div className="grid md:grid-cols-2 gap-4">
              <Input
                label="Project Name"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., L.J. Alleman Middle School Drainage"
                required
              />
              <Input
                label="Project Location"
                value={projectLocation}
                onChange={(e) => setProjectLocation(e.target.value)}
                placeholder="e.g., Lafayette, LA"
              />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <Input
                label="Jurisdiction"
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                placeholder="e.g., Lafayette UDC, DOTD"
              />
              <Input
                label="Project Type"
                value={projectType}
                onChange={(e) => setProjectType(e.target.value)}
                placeholder="e.g., Educational, Commercial, Residential"
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

        {/* Service Selection */}
        <Card title="Select Services" description="Choose civil engineering services to include">
          <div className="space-y-3">
            {Object.entries(SERVICE_PRICING).map(([key, service]) => (
              <div
                key={key}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedServices.includes(key)
                    ? 'bg-blue-50 border-blue-500'
                    : 'bg-slate-50 border-slate-200 hover:border-slate-300'
                }`}
                onClick={() => toggleService(key)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selectedServices.includes(key)}
                      onChange={() => toggleService(key)}
                      className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div>
                      <p className="font-semibold text-slate-900">
                        {service.name}
                      </p>
                      <p className="text-sm text-slate-600">{service.description}</p>
                      <p className="text-xs text-slate-500 mt-1">{service.days} days estimated</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-slate-900">
                      ${service.price.toLocaleString()}
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
          <Card title="Professional Fee Estimate" description="Pricing breakdown for selected services">
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Subtotal ({selectedServices.length} services):</span>
                <span className="font-semibold">${pricing.subtotal.toLocaleString()}</span>
              </div>

              {pricing.packageDiscount > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Package Discount ({pricing.packageDiscount}%):</span>
                  <span>-${((pricing.subtotal * pricing.packageDiscount) / 100).toLocaleString()}</span>
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
                <span>Total Professional Fee:</span>
                <span className="text-blue-600">${pricing.total.toLocaleString()}</span>
              </div>

              <div className="bg-blue-50 rounded-lg p-3 text-sm border border-blue-200">
                <p className="text-slate-700">
                  <strong>Estimated Timeline:</strong> {pricing.totalDays} business days
                </p>
                <p className="text-slate-600 text-xs mt-1">
                  Timeline assumes timely receipt of all necessary data and client approvals
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
            disabled={selectedServices.length === 0}
            className="flex-1"
          >
            Generate Civil Engineering Proposal
          </Button>
        </div>

        {error && (
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Result */}
        {result && (
          <Card title="Proposal Generated" description="Your civil engineering proposal is ready">
            <div className="space-y-4">
              <Alert variant="success">
                <strong>Professional services proposal generated successfully!</strong>
                <p className="mt-2">Proposal ID: {result.proposal_id}</p>
              </Alert>

              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <h4 className="font-semibold text-slate-900 mb-2">Proposal Details</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Client:</span>
                    <span className="font-semibold">{result.client_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Total Professional Fee:</span>
                    <span className="font-semibold">${result.total_price.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Estimated Timeline:</span>
                    <span className="font-semibold">{result.estimated_days} business days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Services Included:</span>
                    <span className="font-semibold">{result.services_included.join(', ')}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <Button variant="primary">Download Proposal (DOCX)</Button>
                <Button variant="secondary">Download Cover Letter</Button>
                <Button variant="outline">Preview PDF</Button>
                <Button variant="outline">Email to Client</Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
