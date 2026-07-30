import React from 'react';
import StatCard from '../components/dashboard/StatCard';
import RecentTelemetryPlaceholder from '../components/dashboard/RecentTelemetryPlaceholder';
import FaultMapPlaceholder from '../components/dashboard/FaultMapPlaceholder';
import { FiCpu, FiAlertTriangle, FiClipboard, FiCheckCircle } from 'react-icons/fi';

/**
 * Enterprise Dashboard Page Component
 */
const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Fault Detection Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time radial distribution network telemetry & fault monitoring
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 bg-brand-50 border border-brand-200 text-brand-700 text-xs font-semibold rounded-lg">
            Network Mode: Radial Grid 1
          </span>
        </div>
      </div>

      {/* 4 Primary Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Total Poles"
          value="1,248"
          statusText="Registered Grid Assets"
          icon={FiCpu}
          colorTheme="blue"
        />

        <StatCard
          title="Active Faults"
          value="3"
          statusText="Critical Alerts Raised"
          icon={FiAlertTriangle}
          colorTheme="red"
        />

        <StatCard
          title="Open Tickets"
          value="5"
          statusText="Dispatched Maintenance"
          icon={FiClipboard}
          colorTheme="amber"
        />

        <StatCard
          title="Healthy Devices"
          value="1,245"
          statusText="99.76% Operational"
          icon={FiCheckCircle}
          colorTheme="emerald"
        />
      </div>

      {/* Main Grid Section: Recent Telemetry Stream & Fault Map */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentTelemetryPlaceholder />
        </div>
        <div className="lg:col-span-1">
          <FaultMapPlaceholder />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
