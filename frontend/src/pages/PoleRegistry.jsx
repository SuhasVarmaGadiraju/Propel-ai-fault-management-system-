import React, { useEffect, useState, useCallback } from 'react';
import {
  FiCpu,
  FiUploadCloud,
  FiSearch,
  FiFilter,
  FiChevronLeft,
  FiChevronRight,
  FiEye,
  FiCheckCircle,
  FiAlertTriangle,
  FiLayers,
  FiZap
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';
import ImportCsvModal from '../components/registry/ImportCsvModal';
import PoleDetailDrawer from '../components/registry/PoleDetailDrawer';

const PoleRegistry = () => {
  const [stats, setStats] = useState(null);
  const [poles, setPoles] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 20, total_records: 0, total_pages: 1 });
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [feederFilter, setFeederFilter] = useState('');
  const [deviceFilter, setDeviceFilter] = useState('');
  const [page, setPage] = useState(1);

  // Modals & Drawers
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [selectedPoleCode, setSelectedPoleCode] = useState(null);

  const fetchStatistics = async () => {
    try {
      const data = await apiClient.get('/pole-registry/statistics');
      setStats(data || null);
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  const fetchPoles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/pole-registry', {
        params: {
          page,
          page_size: 20,
          search: searchTerm || undefined,
          feeder_code: feederFilter || undefined,
          device_installed: deviceFilter || undefined,
        },
      });
      setPoles(Array.isArray(data?.poles) ? data.poles : []);
      setPagination(data?.pagination ?? { page: 1, page_size: 20, total_records: 0, total_pages: 1 });
    } catch (err) {
      console.error('Failed to fetch poles:', err);
      setPoles([]);
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, feederFilter, deviceFilter]);

  useEffect(() => {
    fetchStatistics();
  }, []);

  useEffect(() => {
    fetchPoles();
  }, [fetchPoles]);

  const handleImportSuccess = () => {
    fetchStatistics();
    fetchPoles();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiCpu className="w-6 h-6 text-brand-600" />
            Pole Registry Master Index
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Official 11kV electrical network pole registry & radial topology dataset
          </p>
        </div>

        <button
          onClick={() => setIsImportModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
        >
          <FiUploadCloud className="w-4 h-4" />
          Import Department CSV
        </button>
      </div>

      {/* 5 Operational Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Poles"
          value={stats?.total_poles != null ? Number(stats.total_poles).toLocaleString() : '---'}
          statusText="Master Grid Assets"
          icon={FiCpu}
          colorTheme="blue"
        />
        <StatCard
          title="Transformers"
          value={stats?.total_transformers != null ? Number(stats.total_transformers).toLocaleString() : '---'}
          statusText="Distribution DTRs"
          icon={FiZap}
          colorTheme="emerald"
        />
        <StatCard
          title="Feeders"
          value={stats?.total_feeders != null ? Number(stats.total_feeders).toLocaleString() : '---'}
          statusText="11kV Radial Lines"
          icon={FiLayers}
          colorTheme="blue"
        />
        <StatCard
          title="Unknown Topology"
          value={stats?.unknown_topology_count != null ? Number(stats.unknown_topology_count).toLocaleString() : '---'}
          statusText="Unmapped Parent Poles"
          icon={FiAlertTriangle}
          colorTheme="amber"
        />
        <StatCard
          title="Poles w/o Device"
          value={stats?.poles_without_devices != null ? Number(stats.poles_without_devices).toLocaleString() : '---'}
          statusText="No IoT Hardware"
          icon={FiCheckCircle}
          colorTheme="red"
        />
      </div>

      {/* Filter & Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-80">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search Pole ID, Ward, PIN..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-800"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {/* Feeder Filter */}
            <select
              value={feederFilter}
              onChange={(e) => {
                setFeederFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">All Feeders</option>
              <option value="FDR-HYD-NORTH-01">North Feeder 01</option>
              <option value="FDR-HYD-CENTRAL-02">Central Feeder 02</option>
              <option value="FDR-HYD-SOUTH-03">South Feeder 03</option>
            </select>

            {/* Device Status Filter */}
            <select
              value={deviceFilter}
              onChange={(e) => {
                setDeviceFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">All Device Statuses</option>
              <option value="true">Device Installed</option>
              <option value="false">No Device Installed</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Main Data Table */}
      <Card className="overflow-hidden">
        {loading ? (
          <Loading message="Loading Pole Registry entries..." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Pole Code</th>
                  <th className="px-6 py-3.5">Feeder</th>
                  <th className="px-6 py-3.5">Transformer</th>
                  <th className="px-6 py-3.5">GPS Coords</th>
                  <th className="px-6 py-3.5">Ward / PIN</th>
                  <th className="px-6 py-3.5">Topology</th>
                  <th className="px-6 py-3.5">Device</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Array.isArray(poles) && poles.length > 0 ? (
                  poles.map((p) => (
                    <tr key={p?.id || p?.pole_code} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-3.5 font-bold text-slate-900 font-mono">
                        {p?.pole_code || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5 font-medium text-slate-700">
                        {p?.feeder_code || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5 font-medium text-slate-700">
                        {p?.transformer_code || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-slate-500">
                        {p?.latitude != null ? Number(p.latitude).toFixed(4) : '--'}, {p?.longitude != null ? Number(p.longitude).toFixed(4) : '--'}
                      </td>
                      <td className="px-6 py-3.5 text-slate-600">
                        {p?.ward || 'N/A'} {p?.pincode ? `(${p.pincode})` : ''}
                      </td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${
                            p?.topology_known
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}
                        >
                          {p?.topology_known ? 'Mapped' : 'Unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${
                            p?.device_installed
                              ? 'bg-brand-50 text-brand-700 border border-brand-200'
                              : 'bg-slate-100 text-slate-500 border border-slate-200'
                          }`}
                        >
                          {p?.device_installed ? 'Installed' : 'No Device'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <button
                          onClick={() => setSelectedPoleCode(p?.pole_code)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-600 rounded text-[11px] font-semibold transition-colors"
                        >
                          <FiEye className="w-3.5 h-3.5" />
                          View Spec
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-slate-400 italic">
                      No poles found matching the selected query parameters.
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
            Showing page <strong>{pagination?.page ?? 1}</strong> of <strong>{pagination?.total_pages ?? 1}</strong> ({pagination?.total_records ?? 0} total records)
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

      {/* Modals & Drawers */}
      <ImportCsvModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportSuccess={handleImportSuccess}
      />

      <PoleDetailDrawer
        poleCode={selectedPoleCode}
        onClose={() => setSelectedPoleCode(null)}
      />
    </div>
  );
};

export default PoleRegistry;
