import React, { useState } from 'react';
import {
  FiX,
  FiClipboard,
  FiUserCheck,
  FiCheckCircle,
  FiClock,
  FiAlertTriangle,
  FiSend,
  FiZap,
  FiCheckSquare,
  FiLock,
  FiInfo
} from 'react-icons/fi';
import apiClient from '../../services/api';
import { formatDate } from '../../utils/helpers';

/**
 * Slide-over drawer displaying Repair Ticket detail, visual progress timeline,
 * work assignment controls, and status transition buttons.
 */
const TicketDetailDrawer = ({ ticket, onClose, onRefresh }) => {
  if (!ticket) return null;

  const [assignedEngineer, setAssignedEngineer] = useState(ticket?.assigned_engineer || '');
  const [assignedTeam, setAssignedTeam] = useState(ticket?.assigned_team || 'Crew Alpha');
  const [updating, setUpdating] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  const stages = ['NEW', 'ACKNOWLEDGED', 'ASSIGNED', 'RESOLVED', 'VERIFIED', 'CLOSED'];
  const currentStageIdx = ticket?.status ? stages.indexOf(ticket.status) : 0;

  const handleStatusTransition = async (newStatus) => {
    setUpdating(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const payload = {
        status: newStatus,
        assigned_engineer: assignedEngineer || undefined,
        assigned_team: assignedTeam || undefined,
      };
      await apiClient.patch(`/tickets/${ticket.ticket_number}`, payload);
      setActionSuccess(`Ticket status updated to ${newStatus}.`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setActionError(err.message || 'Status transition failed.');
    } finally {
      setUpdating(false);
    }
  };

  const handleAutoVerify = async () => {
    setUpdating(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const data = await apiClient.post(`/tickets/${ticket.ticket_number}/verify`);
      setActionSuccess(data?.message || 'Auto-verification successful.');
      if (onRefresh) onRefresh();
    } catch (err) {
      setActionError(err.message || 'Auto-verification failed. Outage telemetry remains dark.');
    } finally {
      setUpdating(false);
    }
  };

  const handleSaveAssignment = async () => {
    setUpdating(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      await apiClient.patch(`/tickets/${ticket.ticket_number}`, {
        assigned_engineer: assignedEngineer,
        assigned_team: assignedTeam,
      });
      setActionSuccess('Engineer assignment saved successfully.');
      if (onRefresh) onRefresh();
    } catch (err) {
      setActionError(err.message || 'Failed to update assignment.');
    } finally {
      setUpdating(false);
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
    ASSIGNED: 'bg-amber-50 text-amber-700 border-amber-200',
    RESOLVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    VERIFIED: 'bg-teal-50 text-teal-800 border-teal-200 font-bold',
    CLOSED: 'bg-slate-100 text-slate-600 border-slate-300',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-lg bg-white border-l border-slate-200 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-brand-600 rounded-lg">
                <FiClipboard className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-base font-bold tracking-tight font-mono">{ticket?.ticket_number || 'N/A'}</h2>
                <p className="text-[11px] text-slate-400 font-mono">Incident: {ticket?.incident_id || 'N/A'}</p>
              </div>
            </div>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg">
              <FiX className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
            {/* Status & Priority Badges */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded-full text-xs uppercase tracking-wider font-semibold border ${statusBadgeMap[ticket?.status] || ''}`}>
                  {ticket?.status || 'NEW'}
                </span>
                <span className={`px-2.5 py-1 rounded-full text-xs uppercase tracking-wider border ${priorityBadgeMap[ticket?.priority] || ''}`}>
                  {ticket?.priority || 'MEDIUM'} Priority
                </span>
              </div>
              <span className="font-bold text-slate-700 text-xs">{ticket?.confidence != null ? ticket.confidence : '---'}% Confidence</span>
            </div>

            {/* Action Alert Banner */}
            {actionError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-2 font-medium">
                <FiAlertTriangle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}
            {actionSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl flex items-center gap-2 font-medium">
                <FiCheckCircle className="w-4 h-4 shrink-0" />
                <span>{actionSuccess}</span>
              </div>
            )}

            {/* Visual Lifecycle Progress Timeline */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FiClock className="w-4 h-4 text-brand-600" />
                Lifecycle State Timeline
              </h3>
              <div className="grid grid-cols-6 gap-1 text-center">
                {stages.map((st, idx) => {
                  const isDone = idx <= currentStageIdx;
                  const isCurrent = idx === currentStageIdx;
                  return (
                    <div key={st} className="space-y-1">
                      <div
                        className={`h-2 rounded-full transition-colors ${
                          isDone ? (isCurrent ? 'bg-brand-600' : 'bg-emerald-500') : 'bg-slate-200'
                        }`}
                      ></div>
                      <span className={`text-[9px] font-bold block ${isCurrent ? 'text-brand-700' : 'text-slate-500'}`}>
                        {st}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* State Transition Action Controls */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FiZap className="w-4 h-4 text-brand-600" />
                Workflow Action Controls
              </h3>
              <div className="flex flex-wrap gap-2">
                {ticket?.status === 'NEW' && (
                  <button
                    onClick={() => handleStatusTransition('ACKNOWLEDGED')}
                    disabled={updating}
                    className="py-2 px-3 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-lg text-xs"
                  >
                    Acknowledge Ticket
                  </button>
                )}

                {(ticket?.status === 'NEW' || ticket?.status === 'ACKNOWLEDGED') && (
                  <button
                    onClick={() => handleStatusTransition('ASSIGNED')}
                    disabled={updating || !assignedEngineer}
                    className="py-2 px-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg text-xs disabled:opacity-50"
                  >
                    Assign & Dispatch
                  </button>
                )}

                {ticket?.status === 'ASSIGNED' && (
                  <button
                    onClick={() => handleStatusTransition('RESOLVED')}
                    disabled={updating}
                    className="py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg text-xs"
                  >
                    Mark Repair Resolved
                  </button>
                )}

                {ticket?.status === 'RESOLVED' && (
                  <button
                    onClick={handleAutoVerify}
                    disabled={updating}
                    className="py-2 px-3 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg text-xs flex items-center gap-1.5"
                  >
                    <FiCheckSquare className="w-3.5 h-3.5" />
                    Auto-Verify via Telemetry
                  </button>
                )}

                {ticket?.status === 'VERIFIED' && (
                  <button
                    onClick={() => handleStatusTransition('CLOSED')}
                    disabled={updating}
                    className="py-2 px-3 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-lg text-xs flex items-center gap-1.5"
                  >
                    <FiLock className="w-3.5 h-3.5" />
                    Close Ticket
                  </button>
                )}
              </div>
            </div>

            {/* Engineer Work Assignment Form */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <FiUserCheck className="w-4 h-4 text-brand-600" />
                Work Order Crew Assignment
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assigned Field Engineer</label>
                  <input
                    type="text"
                    placeholder="e.g. Eng. Suhas"
                    value={assignedEngineer}
                    onChange={(e) => setAssignedEngineer(e.target.value)}
                    className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Maintenance Team</label>
                  <input
                    type="text"
                    placeholder="e.g. Crew Alpha"
                    value={assignedTeam}
                    onChange={(e) => setAssignedTeam(e.target.value)}
                    className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
                  />
                </div>
              </div>
              <button
                onClick={handleSaveAssignment}
                disabled={updating}
                className="py-1.5 px-3 bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold rounded-lg text-xs"
              >
                Save Assignment
              </button>
            </div>

            {/* Incident Details Summary */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Impact & Hardware Location
              </h3>
              <div className="grid grid-cols-2 gap-3 text-slate-700">
                <div>
                  <span className="text-slate-400 block">Feeder</span>
                  <span className="font-mono font-bold text-slate-900">{ticket?.feeder_code || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Transformer</span>
                  <span className="font-mono font-bold text-slate-900">{ticket?.transformer_code || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Upstream Pole</span>
                  <span className="font-mono font-bold text-emerald-700">{ticket?.upstream_pole || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Downstream Pole</span>
                  <span className="font-mono font-bold text-red-700">{ticket?.downstream_pole || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Estimated Outage</span>
                  <span className="font-bold text-slate-900">{ticket?.estimated_households ?? 0} Households</span>
                </div>
              </div>
            </div>

            {/* Diagnostic Reasoning Summary */}
            <div className="bg-slate-900 text-slate-200 border border-slate-800 rounded-xl p-4 space-y-2">
              <h3 className="text-slate-400 uppercase tracking-wider text-[11px] font-bold flex items-center gap-1.5">
                <FiInfo className="w-4 h-4 text-brand-400" />
                Fault Localization Reasoning Summary
              </h3>
              <pre className="text-[11px] font-mono text-emerald-400 whitespace-pre-wrap leading-relaxed">
                {ticket?.reasoning_summary || 'No reasoning summary available.'}
              </pre>
            </div>

            {/* Full Audit Timestamp Log */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Audit Timestamp Trail
              </h3>
              <div className="space-y-1 text-[11px] text-slate-600 font-mono">
                <div className="flex justify-between"><span>Created:</span> <span>{formatDate(ticket?.created_at)}</span></div>
                <div className="flex justify-between"><span>Acknowledged:</span> <span>{formatDate(ticket?.acknowledged_at)}</span></div>
                <div className="flex justify-between"><span>Assigned:</span> <span>{formatDate(ticket?.assigned_at)}</span></div>
                <div className="flex justify-between"><span>Resolved:</span> <span>{formatDate(ticket?.resolved_at)}</span></div>
                <div className="flex justify-between"><span>Verified:</span> <span>{formatDate(ticket?.verified_at)}</span></div>
                <div className="flex justify-between"><span>Closed:</span> <span>{formatDate(ticket?.closed_at)}</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicketDetailDrawer;
