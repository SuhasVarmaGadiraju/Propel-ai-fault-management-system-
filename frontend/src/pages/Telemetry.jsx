import React, { useEffect, useState, useCallback } from 'react';
import {
  FiZap,
  FiSearch,
  FiChevronLeft,
  FiChevronRight,
  FiEye,
  FiAlertTriangle,
  FiCheckCircle,
  FiActivity,
  FiRadio,
  FiPower
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';
import TelemetryDetailDrawer from '../components/telemetry/TelemetryDetailDrawer';
import { formatDate } from '../utils/helpers';

const TelemetryPage = () => {
  const [stats, setStats] = useState(null);
  const [telemetryList, setTelemetryList] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 20, total_records: 0, total_pages: 1 });
  const [loading, setLoading] = useState(true);

  // Filter state
  const [searchDevice, setSearchDevice] = useState('');
  const [eventFilter, setEventFilter] = useState('');
  const [outOfOrderFilter, setOutOfOrderFilter] = useState('');
  const [page, setPage] = useState(1);

  // Selected telemetry drawer item
  const [selectedTelemetry, setSelectedTelemetry] = useState(null);

  const fetchStatistics = async () => {
    try {
      const data = await apiClient.get('/telemetry/statistics');
      setStats(data || null);
    } catch (err) {
      console.error('Failed to fetch telemetry statistics:', err);
    }
  };

  const fetchTelemetry = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/telemetry', {
        params: {
          page,
          page_size: 20,
          device_id: searchDevice || undefined,
          event: eventFilter || undefined,
          out_of_order: outOfOrderFilter || undefined,
        },
      });
      setTelemetryList(Array.isArray(data?.telemetry) ? data.telemetry : []);
      setPagination(data?.pagination ?? { page: 1, page_size: 20, total_records: 0, total_pages: 1 });
    } catch (err) {
      console.error('Failed to fetch telemetry stream:', err);
      setTelemetryList([]);
    } finally {
      setLoading(false);
    }
  }, [page, searchDevice, eventFilter, outOfOrderFilter]);

  useEffect(() => {
    fetchStatistics();
  }, []);

  useEffect(() => {
    fetchTelemetry();
  }, [fetchTelemetry]);

  const eventBadgeMap = {
    heartbeat: 'bg-blue-50 text-blue-700 border-blue-200',
    power_lost: 'bg-red-50 text-red-700 border-red-200 font-bold animate-pulse',
    power_restored: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold',
    boot: 'bg-purple-50 text-purple-700 border-purple-200',
    fault_detected: 'bg-amber-50 text-amber-700 border-amber-200 font-bold',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiZap className="w-6 h-6 text-brand-600" />
            Live IoT Telemetry Stream
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time pole sensor telemetry ingestion, sequence tracking, and deduplication
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span className="text-xs font-semibold text-emerald-700">Ingestion Pipeline Online</span>
        </div>
      </div>

      {/* 5 Operational Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Telemetry"
          value={stats?.total_telemetry != null ? Number(stats.total_telemetry).toLocaleString() : '---'}
          statusText="Ingested Events"
          icon={FiActivity}
          colorTheme="blue"
        />
        <StatCard
          title="Power Outages"
          value={stats?.power_lost != null ? Number(stats.power_lost).toLocaleString() : '---'}
          statusText="Power Lost Events"
          icon={FiPower}
          colorTheme="red"
        />
        <StatCard
          title="Power Restored"
          value={stats?.power_restored != null ? Number(stats.power_restored).toLocaleString() : '---'}
          statusText="Restoration Events"
          icon={FiCheckCircle}
          colorTheme="emerald"
        />
        <StatCard
          title="Online Devices"
          value={stats?.currently_online_devices != null ? Number(stats.currently_online_devices).toLocaleString() : '---'}
          statusText="Communicated < 15m"
          icon={FiRadio}
          colorTheme="blue"
        />
        <StatCard
          title="Out of Order"
          value={stats?.out_of_order_messages != null ? Number(stats.out_of_order_messages).toLocaleString() : '---'}
          statusText="Sequence Lag Messages"
          icon={FiAlertTriangle}
          colorTheme="amber"
        />
      </div>

      {/* Filter & Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-80">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search Device ID or Pole ID..."
              value={searchDevice}
              onChange={(e) => {
                setSearchDevice(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-800"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {/* Event Filter */}
            <select
              value={eventFilter}
              onChange={(e) => {
                setEventFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">All Event Types</option>
              <option value="heartbeat">Heartbeat</option>
              <option value="power_lost">Power Lost</option>
              <option value="power_restored">Power Restored</option>
              <option value="boot">Boot</option>
            </select>

            {/* Out of Order Filter */}
            <select
              value={outOfOrderFilter}
              onChange={(e) => {
                setOutOfOrderFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">All Sequence Statuses</option>
              <option value="false">In-Sequence Only</option>
              <option value="true">Out-of-Order Only</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Main Data Table */}
      <Card className="overflow-hidden">
        {loading ? (
          <Loading message="Fetching live telemetry stream..." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5">Device ID</th>
                  <th className="px-6 py-3.5">Pole Code</th>
                  <th className="px-6 py-3.5">Event</th>
                  <th className="px-6 py-3.5">Sequence</th>
                  <th className="px-6 py-3.5">Battery</th>
                  <th className="px-6 py-3.5">RSSI</th>
                  <th className="px-6 py-3.5">FW</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Array.isArray(telemetryList) && telemetryList.length > 0 ? (
                  telemetryList.map((t) => (
                    <tr key={t?.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-3.5 font-mono text-slate-500">
                        {formatDate(t?.event_timestamp)}
                      </td>
                      <td className="px-6 py-3.5 font-bold text-slate-900 font-mono">
                        {t?.device_id || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5 font-semibold text-brand-700 font-mono">
                        {t?.pole_code || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] uppercase font-semibold border ${
                              eventBadgeMap[t?.event] || 'bg-slate-100 text-slate-700 border-slate-200'
                            }`}
                          >
                            {t?.event ? String(t.event).replace('_', ' ') : 'UNKNOWN'}
                          </span>
                          {t?.out_of_order && (
                            <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded text-[9px] font-bold" title="Out of Order Sequence">
                              LAG
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-3.5 font-mono font-medium text-slate-800">
                        #{t?.sequence_number ?? 0}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-slate-600">
                        {t?.battery_mv != null ? `${t.battery_mv} mV` : '---'}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-slate-600">
                        {t?.rssi != null ? `${t.rssi} dBm` : '---'}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-slate-500">
                        {t?.firmware_version || '1.0.0'}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <button
                          onClick={() => setSelectedTelemetry(t)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-600 rounded text-[11px] font-semibold transition-colors"
                        >
                          <FiEye className="w-3.5 h-3.5" />
                          Payload
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-6 py-8 text-center text-slate-400 italic">
                      No telemetry event records found matching the query filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
          <span>
            Page <strong>{pagination?.page ?? 1}</strong> of <strong>{pagination?.total_pages ?? 1}</strong> ({pagination?.total_records ?? 0} total telemetry events)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
              disabled={page === 1}
              className="p-1.5 border border-slate-200 bg-white rounded-lg disabled:opacity-40 hover:bg-slate-50"
            >
              <FiChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((prev) => Math.min(prev + 1, pagination?.total_pages ?? 1))}
              disabled={page >= (pagination?.total_pages ?? 1)}
              className="p-1.5 border border-slate-200 bg-white rounded-lg disabled:opacity-40 hover:bg-slate-50"
            >
              <FiChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </Card>

      {/* Telemetry Detail Drawer */}
      <TelemetryDetailDrawer
        telemetry={selectedTelemetry}
        onClose={() => setSelectedTelemetry(null)}
      />
    </div>
  );
};

export default TelemetryPage;
