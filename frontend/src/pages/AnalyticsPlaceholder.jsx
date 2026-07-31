import React from 'react';
import { FiBarChart2, FiClock } from 'react-icons/fi';
import Card from '../components/ui/Card';

const AnalyticsPlaceholder = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiBarChart2 className="w-6 h-6 text-emerald-600" />
            Grid Reliability & Outage Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            SAIFI/SAIDI reliability indices, feeder failure heatmaps, and historical telemetry trends
          </p>
        </div>

        <span className="px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-lg">
          Coming Soon — Scheduled for Phase 7
        </span>
      </div>

      {/* Main Feature Status Card */}
      <Card className="p-8 text-center space-y-6">
        <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
          <FiBarChart2 className="w-8 h-8" />
        </div>

        <div className="max-w-md mx-auto space-y-2">
          <h2 className="text-lg font-bold text-slate-900">Feature Under Scheduled Milestone</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            The Grid Analytics module provides utility-grade SAIFI (System Average Interruption Frequency Index) and SAIDI metrics alongside historical failure heatmaps.
          </p>
        </div>

        {/* Milestone Progress Tracker */}
        <div className="max-w-lg mx-auto bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-left space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Milestone Status</span>
            <span className="font-mono text-emerald-600 font-semibold">Phase 7 Deliverable</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-slate-600">
              <FiClock className="w-4 h-4 text-slate-400 shrink-0" />
              <span>Phase 5-6: Fault Localization & Repair Tickets (Prerequisite)</span>
            </div>
            <div className="flex items-center gap-2 text-emerald-700 font-semibold">
              <FiClock className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Phase 7: Grid Reliability & Outage Analytics Reports (Upcoming)</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AnalyticsPlaceholder;
