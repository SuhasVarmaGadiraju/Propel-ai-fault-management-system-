import React from 'react';
import { FiClipboard, FiClock, FiCheckCircle } from 'react-icons/fi';
import Card from '../components/ui/Card';

const TicketsPlaceholder = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiClipboard className="w-6 h-6 text-brand-600" />
            Repair Ticket Management
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated maintenance work orders, field technician dispatching, and SLA tracking
          </p>
        </div>

        <span className="px-3 py-1 bg-brand-50 border border-brand-200 text-brand-800 text-xs font-semibold rounded-lg">
          Coming Soon — Scheduled for Phase 6
        </span>
      </div>

      {/* Main Feature Status Card */}
      <Card className="p-8 text-center space-y-6">
        <div className="w-16 h-16 bg-brand-50 text-brand-600 rounded-full flex items-center justify-center mx-auto">
          <FiClipboard className="w-8 h-8" />
        </div>

        <div className="max-w-md mx-auto space-y-2">
          <h2 className="text-lg font-bold text-slate-900">Feature Under Scheduled Milestone</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            The Repair Ticket Management module automatically dispatches work orders to field crews upon fault confirmation, tracking repair SLAs and restoration status.
          </p>
        </div>

        {/* Milestone Progress Tracker */}
        <div className="max-w-lg mx-auto bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-left space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Milestone Status</span>
            <span className="font-mono text-brand-600 font-semibold">Phase 6 Deliverable</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-slate-600">
              <FiClock className="w-4 h-4 text-slate-400 shrink-0" />
              <span>Phase 5: AI Fault Localization Engine (Prerequisite)</span>
            </div>
            <div className="flex items-center gap-2 text-brand-700 font-semibold">
              <FiClock className="w-4 h-4 text-brand-600 shrink-0" />
              <span>Phase 6: Automated Repair Ticket Management & Dispatch (Upcoming)</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default TicketsPlaceholder;
