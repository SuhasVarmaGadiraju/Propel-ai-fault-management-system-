import React, { useEffect, useState } from 'react';
import {
  FiPieChart,
  FiBarChart2,
  FiActivity,
  FiDownload,
  FiZap,
  FiRadio,
  FiClock,
  FiCheckCircle,
  FiAlertTriangle,
  FiShield,
  FiUsers,
  FiTrendingUp,
  FiFileText
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';

/**
 * Production Analytics & Operations Dashboard Page displaying real system KPIs,
 * reliability metrics (MTTR, Availability %), visual chart breakdowns, and CSV/JSON exports.
 */
const AnalyticsPage = () => {
  const [overview, setOverview] = useState(null);
  const [faultStats, setFaultStats] = useState(null);
  const [ticketStats, setTicketStats] = useState(null);
  const [reliability, setReliability] = useState(null);
  const [simStats, setSimStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      const [ovData, fData, tData, rData, sData] = await Promise.all([
        apiClient.get('/analytics/overview'),
        apiClient.get('/analytics/faults'),
        apiClient.get('/analytics/tickets'),
        apiClient.get('/analytics/reliability'),
        apiClient.get('/analytics/simulator')
      ]);

      setOverview(ovData);
      setFaultStats(fData);
      setTicketStats(tData);
      setReliability(rData);
      setSimStats(sData);
    } catch (err) {
      console.error('Failed to fetch analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const handleExport = (dataset, format) => {
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';
    window.open(`${backendUrl}/analytics/export/${dataset}?format=${format}`, '_blank');
  };

  if (loading) {
    return <Loading message="Aggregating real system analytics & reliability metrics..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Export Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiPieChart className="w-6 h-6 text-brand-600" />
            Analytics & Network Operations Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real system metrics, grid health, MTTR reliability KPIs, and raw data exports
          </p>
        </div>

        {/* Data Export Dropdown Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase px-2">Export:</span>
            <button
              onClick={() => handleExport('tickets', 'csv')}
              className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 rounded-lg text-xs font-semibold shadow-2xs flex items-center gap-1"
            >
              <FiDownload className="w-3.5 h-3.5 text-emerald-600" />
              Tickets (CSV)
            </button>
            <button
              onClick={() => handleExport('faults', 'json')}
              className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 rounded-lg text-xs font-semibold shadow-2xs flex items-center gap-1"
            >
              <FiFileText className="w-3.5 h-3.5 text-brand-600" />
              Faults (JSON)
            </button>
            <button
              onClick={() => handleExport('simulator', 'csv')}
              className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 rounded-lg text-xs font-semibold shadow-2xs flex items-center gap-1"
            >
              <FiDownload className="w-3.5 h-3.5 text-purple-600" />
              Sim Logs (CSV)
            </button>
          </div>
        </div>
      </div>

      {/* 6 Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Poles"
          value={overview ? overview.total_poles.toLocaleString() : '---'}
          statusText="Master Pole Registry"
          icon={FiShield}
          colorTheme="blue"
        />
        <StatCard
          title="Instrumented"
          value={overview ? overview.instrumented_poles.toLocaleString() : '---'}
          statusText="IoT Monitored Devices"
          icon={FiRadio}
          colorTheme="blue"
        />
        <StatCard
          title="Active Outages"
          value={overview ? overview.active_faults : '---'}
          statusText="Localized Fault Incidents"
          icon={FiAlertTriangle}
          colorTheme="red"
        />
        <StatCard
          title="Open Tickets"
          value={overview ? overview.open_tickets : '---'}
          statusText="Pending Work Orders"
          icon={FiClock}
          colorTheme="amber"
        />
        <StatCard
          title="Network Health"
          value={overview ? `${overview.network_health}%` : '---'}
          statusText="Energized Power Flow"
          icon={FiActivity}
          colorTheme="emerald"
        />
        <StatCard
          title="Telemetry 24h"
          value={overview ? overview.telemetry_today.toLocaleString() : '---'}
          statusText="Ingested IoT Events"
          icon={FiTrendingUp}
          colorTheme="purple"
        />
      </div>

      {/* Reliability & Grid KPIs Section */}
      <Card className="p-6 bg-slate-900 text-white space-y-4 border-slate-800">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-brand-400 flex items-center gap-2">
            <FiActivity className="w-4 h-4" />
            Grid Reliability & Performance KPIs
          </h2>
          <span className="text-xs font-mono text-emerald-400 font-bold">
            Availability: {reliability ? reliability.network_availability_percent : 100}%
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-850 p-4 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold block">MTTR (Mean Time To Repair)</span>
            <span className="text-2xl font-bold font-mono text-emerald-400">{reliability ? reliability.mttr_minutes : 0} min</span>
            <p className="text-[11px] text-slate-400">Avg duration from ticket creation to restoration verification</p>
          </div>

          <div className="bg-slate-850 p-4 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold block">Avg Outage Household Impact</span>
            <span className="text-2xl font-bold font-mono text-amber-400">{reliability ? reliability.avg_affected_households : 0}</span>
            <p className="text-[11px] text-slate-400">Mean estimated households affected per localized incident</p>
          </div>

          <div className="bg-slate-850 p-4 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold block">Most Affected Feeder</span>
            <span className="text-lg font-bold font-mono text-brand-400">{reliability ? reliability.most_affected_feeder : 'N/A'}</span>
            <p className="text-[11px] text-slate-400">11kV feeder line with highest outage incident frequency</p>
          </div>

          <div className="bg-slate-850 p-4 rounded-xl border border-slate-800 space-y-1">
            <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold block">Most Affected DTR Substation</span>
            <span className="text-lg font-bold font-mono text-purple-400">{reliability ? reliability.most_affected_transformer : 'N/A'}</span>
            <p className="text-[11px] text-slate-400">Transformer station with highest outage incident frequency</p>
          </div>
        </div>
      </Card>

      {/* Visual Analytics Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 1. Fault Type Breakdown */}
        <Card className="p-5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <FiZap className="w-4 h-4 text-amber-500" />
            Fault Type Distribution
          </h3>
          <div className="space-y-2 text-xs">
            {faultStats && faultStats.by_fault_type ? (
              Object.entries(faultStats.by_fault_type).map(([ftype, count]) => (
                <div key={ftype} className="space-y-1">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-700">{ftype.replace('_', ' ')}</span>
                    <span className="font-mono text-slate-900">{count}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full"
                      style={{
                        width: `${faultStats.total_incidents > 0 ? (count / faultStats.total_incidents) * 100 : 0}%`,
                      }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-400 italic">No fault distribution data.</p>
            )}
          </div>
        </Card>

        {/* 2. Ticket Priority Distribution */}
        <Card className="p-5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <FiBarChart2 className="w-4 h-4 text-red-500" />
            Ticket Priority Distribution
          </h3>
          <div className="space-y-2 text-xs">
            {ticketStats && ticketStats.by_priority ? (
              Object.entries(ticketStats.by_priority).map(([prio, count]) => {
                const colorMap = { CRITICAL: 'bg-red-600', HIGH: 'bg-amber-500', MEDIUM: 'bg-blue-500', LOW: 'bg-slate-400' };
                return (
                  <div key={prio} className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-700">{prio}</span>
                      <span className="font-mono text-slate-900">{count}</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${colorMap[prio] || 'bg-brand-500'} rounded-full`}
                        style={{
                          width: `${ticketStats.total_tickets > 0 ? (count / ticketStats.total_tickets) * 100 : 0}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-slate-400 italic">No ticket priority data.</p>
            )}
          </div>
        </Card>

        {/* 3. Ticket Status Lifecycle */}
        <Card className="p-5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <FiCheckCircle className="w-4 h-4 text-emerald-600" />
            Ticket Lifecycle Status Breakdown
          </h3>
          <div className="space-y-2 text-xs">
            {ticketStats && ticketStats.by_status ? (
              Object.entries(ticketStats.by_status).map(([st, count]) => (
                <div key={st} className="space-y-1">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-700">{st}</span>
                    <span className="font-mono text-slate-900">{count}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{
                        width: `${ticketStats.total_tickets > 0 ? (count / ticketStats.total_tickets) * 100 : 0}%`,
                      }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-400 italic">No ticket status data.</p>
            )}
          </div>
        </Card>

        {/* 4. Confidence Distribution */}
        <Card className="p-5 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <FiActivity className="w-4 h-4 text-purple-600" />
            Confidence Bucket Distribution
          </h3>
          <div className="space-y-3 text-xs">
            {faultStats && faultStats.by_confidence_bucket ? (
              <>
                <div className="flex justify-between items-center bg-emerald-50 p-2.5 rounded-lg border border-emerald-200">
                  <span className="font-bold text-emerald-800">High Certainty (&gt;= 90%)</span>
                  <span className="font-mono font-bold text-emerald-900">{faultStats.by_confidence_bucket.high}</span>
                </div>
                <div className="flex justify-between items-center bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                  <span className="font-bold text-amber-800">Medium Certainty (70-89%)</span>
                  <span className="font-mono font-bold text-amber-900">{faultStats.by_confidence_bucket.medium}</span>
                </div>
                <div className="flex justify-between items-center bg-red-50 p-2.5 rounded-lg border border-red-200">
                  <span className="font-bold text-red-800">Low Certainty (&lt; 70%)</span>
                  <span className="font-mono font-bold text-red-900">{faultStats.by_confidence_bucket.low}</span>
                </div>
              </>
            ) : (
              <p className="text-slate-400 italic">No confidence bucket data.</p>
            )}
          </div>
        </Card>

        {/* 5. Simulator Scenario Usage */}
        <Card className="p-5 space-y-4 lg:col-span-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <FiTrendingUp className="w-4 h-4 text-brand-600" />
            Simulator Scenario Execution Usage
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {simStats && simStats.scenario_counts ? (
              Object.entries(simStats.scenario_counts).map(([scen, count]) => (
                <div key={scen} className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block font-mono">{scen}</span>
                  <span className="text-lg font-bold font-mono text-slate-900">{count} runs</span>
                </div>
              ))
            ) : (
              <p className="text-slate-400 italic col-span-4">No simulation execution usage logged.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsPage;
