import React from 'react';
import { FiAlertTriangle, FiClock, FiCheckCircle } from 'react-icons/fi';
import Card from '../components/ui/Card';

const FaultsPlaceholder = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiAlertTriangle className="w-6 h-6 text-amber-500" />
            AI Fault Localization Engine
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated anomaly detection, impedance-based fault distance estimation, and pole isolation
          </p>
        </div>

        <span className="px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold rounded-lg">
          Coming Soon — Scheduled for Phase 5
        </span>
      </div>

      {/* Main Feature Status Card */}
      <Card className="p-8 text-center space-y-6">
        <div className="w-16 h-16 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto">
          <FiAlertTriangle className="w-8 h-8" />
        </div>

        <div className="max-w-md mx-auto space-y-2">
          <h2 className="text-lg font-bold text-slate-900">Feature Under Scheduled Milestone</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            The AI Fault Localization Engine analyzes real-time telemetry stream anomalies to isolate phase-to-ground and short-circuit line breaks along radial distribution lines.
          </p>
        </div>

        {/* Milestone Progress Tracker */}
        <div className="max-w-lg mx-auto bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-left space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Milestone Status</span>
            <span className="font-mono text-amber-600 font-semibold">Phase 5 Deliverable</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-emerald-700">
              <FiCheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Phase 1-4: Telemetry Ingestion Pipeline & Pole Registry (Completed)</span>
            </div>
            <div className="flex items-center gap-2 text-amber-700 font-semibold">
              <FiClock className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Phase 5: AI Fault Localization Engine & Anomaly Detection (Next Phase)</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default FaultsPlaceholder;
