import React from 'react';
import { FiSettings, FiSliders } from 'react-icons/fi';
import Card from '../components/ui/Card';

const SettingsPlaceholder = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiSettings className="w-6 h-6 text-slate-700" />
            System Settings & Administration
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Telemetry ingestion threshold rules, notification webhooks, and system preferences
          </p>
        </div>

        <span className="px-3 py-1 bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold rounded-lg">
          Coming Soon — System Settings Phase
        </span>
      </div>

      {/* Main Feature Status Card */}
      <Card className="p-8 text-center space-y-6">
        <div className="w-16 h-16 bg-slate-100 text-slate-700 rounded-full flex items-center justify-center mx-auto">
          <FiSliders className="w-8 h-8" />
        </div>

        <div className="max-w-md mx-auto space-y-2">
          <h2 className="text-lg font-bold text-slate-900">Feature Under Scheduled Milestone</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            Configure system-wide settings, alert thresholds, webhook integrations, and telemetry ingestion rate limits.
          </p>
        </div>

        {/* Milestone Progress Tracker */}
        <div className="max-w-lg mx-auto bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-left space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Milestone Status</span>
            <span className="font-mono text-slate-700 font-semibold">Admin Configuration</span>
          </div>

          <div className="space-y-2 text-slate-600">
            <p>System configuration panel will be available in later administrative phases.</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SettingsPlaceholder;
