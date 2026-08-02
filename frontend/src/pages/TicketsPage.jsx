import React, { useEffect, useState, useCallback } from 'react';
import {
  FiClipboard,
  FiSearch,
  FiChevronLeft,
  FiChevronRight,
  FiEye,
  FiClock,
  FiCheckCircle,
  FiAlertTriangle,
  FiUserCheck,
  FiAlertOctagon
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';
import TicketDetailDrawer from '../components/tickets/TicketDetailDrawer';
import { formatDate } from '../utils/helpers';

/**
 * Production Repair Tickets Dashboard displaying automated work order tickets,
 * SLA priorities, state machine transitions, and auto-verification status.
 */
const TicketsPage = () => {
  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 20, total_records: 0, total_pages: 1 });
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [page, setPage] = useState(1);

  // Selected ticket for slide-over drawer
  const [selectedTicket, setSelectedTicket] = useState(null);

  const fetchStatistics = async () => {
    try {
      const data = await apiClient.get('/tickets/statistics');
      setStats(data || null);
    } catch (err) {
      console.error('Failed to fetch ticket statistics:', err);
    }
  };

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/tickets', {
        params: {
          page,
          page_size: 20,
          search: search || undefined,
          status: statusFilter || undefined,
          priority: priorityFilter || undefined,
        },
      });
      setTickets(Array.isArray(data?.tickets) ? data.tickets : []);
      setPagination(data?.pagination ?? { page: 1, page_size: 20, total_records: 0, total_pages: 1 });
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, priorityFilter]);

  useEffect(() => {
    fetchStatistics();
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const refreshAll = () => {
    fetchStatistics();
    fetchTickets();
    if (selectedTicket?.ticket_number) {
      // Re-fetch selected ticket details
      apiClient.get(`/tickets/${selectedTicket.ticket_number}`)
        .then((updated) => setSelectedTicket(updated || null))
        .catch(() => {});
    }
  };

  const priorityBadgeMap = {
    CRITICAL: 'bg-red-100 text-red-800 border-red-300 font-bold',
    HIGH: 'bg-amber-100 text-amber-800 border-amber-300 font-bold',
    MEDIUM: 'bg-blue-100 text-blue-800 border-blue-300',
    LOW: 'bg-slate-100 text-slate-700 border-slate-300',
  };

  const statusBadgeMap = {
    NEW: 'bg-blue-50 text-blue-700 border-blue-200',
    ACKNOWLEDGED: 'bg-purple-50 text-purple-700 border-purple-200',
    ASSIGNED: 'bg-amber-50 text-amber-700 border-amber-200 font-semibold',
    RESOLVED: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold',
    VERIFIED: 'bg-teal-50 text-teal-800 border-teal-200 font-bold',
    CLOSED: 'bg-slate-100 text-slate-600 border-slate-300',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiClipboard className="w-6 h-6 text-brand-600" />
            Automated Repair Ticket Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated work order generation, lifecycle state management, and telemetry verification
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-semibold text-emerald-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          Auto Generation Active
        </div>
      </div>

      {/* 5 Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Tickets"
          value={stats?.total_tickets != null ? stats.total_tickets : '---'}
          statusText="Automated Work Orders"
          icon={FiClipboard}
          colorTheme="blue"
        />
        <StatCard
          title="New / Pending"
          value={stats ? (stats.new_count ?? 0) + (stats.acknowledged_count ?? 0) : '---'}
          statusText="Awaiting Assignment"
          icon={FiClock}
          colorTheme="amber"
        />
        <StatCard
          title="In Progress"
          value={stats?.assigned_count != null ? stats.assigned_count : '---'}
          statusText="Crew Dispatched"
          icon={FiUserCheck}
          colorTheme="blue"
        />
        <StatCard
          title="Resolved / Verified"
          value={stats ? (stats.resolved_count ?? 0) + (stats.verified_count ?? 0) : '---'}
          statusText="Restoration Confirmed"
          icon={FiCheckCircle}
          colorTheme="emerald"
        />
        <StatCard
          title="Critical Priority"
          value={stats?.critical_count != null ? stats.critical_count : '---'}
          statusText="Feeder / Major Outages"
          icon={FiAlertOctagon}
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
              placeholder="Search Ticket #, Incident, Pole..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-800"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">All Statuses</option>
              <option value="NEW">NEW</option>
              <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
              <option value="ASSIGNED">ASSIGNED</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="VERIFIED">VERIFIED</option>
              <option value="CLOSED">CLOSED</option>
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Main Tickets Table */}
      <Card className="overflow-hidden">
        {loading ? (
          <Loading message="Loading repair work order tickets..." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Ticket #</th>
                  <th className="px-6 py-3.5">Priority</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Fault Type</th>
                  <th className="px-6 py-3.5">Transformer</th>
                  <th className="px-6 py-3.5">Impact</th>
                  <th className="px-6 py-3.5">Assigned Engineer</th>
                  <th className="px-6 py-3.5">Created At</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Array.isArray(tickets) && tickets.length > 0 ? (
                  tickets.map((t) => (
                    <tr key={t?.id || t?.ticket_number} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-3.5 font-bold font-mono text-slate-900">
                        {t?.ticket_number || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${priorityBadgeMap[t?.priority] || ''}`}>
                          {t?.priority || 'NORMAL'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold border ${statusBadgeMap[t?.status] || ''}`}>
                          {t?.status || 'NEW'}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 font-semibold text-slate-800">
                        {t?.fault_type ? String(t.fault_type).replace('_', ' ') : 'N/A'}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-brand-700 font-semibold">
                        {t?.transformer_code || 'N/A'}
                      </td>
                      <td className="px-6 py-3.5 text-slate-600">
                        {t?.estimated_households ?? 0} Households
                      </td>
                      <td className="px-6 py-3.5 font-medium text-slate-800">
                        {t?.assigned_engineer || <span className="text-slate-400 italic">Unassigned</span>}
                      </td>
                      <td className="px-6 py-3.5 font-mono text-slate-500">
                        {formatDate(t?.created_at)}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <button
                          onClick={() => setSelectedTicket(t)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-600 rounded text-[11px] font-semibold transition-colors"
                        >
                          <FiEye className="w-3.5 h-3.5" />
                          Details
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-6 py-8 text-center text-slate-400 italic">
                      No repair work order tickets found matching the query filters.
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
            Page <strong>{pagination?.page ?? 1}</strong> of <strong>{pagination?.total_pages ?? 1}</strong> ({pagination?.total_records ?? 0} total tickets)
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

      {/* Ticket Details Slide-Over Drawer */}
      <TicketDetailDrawer
        ticket={selectedTicket}
        onClose={() => setSelectedTicket(null)}
        onRefresh={refreshAll}
      />
    </div>
  );
};

export default TicketsPage;
