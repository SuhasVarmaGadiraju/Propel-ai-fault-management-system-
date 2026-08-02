import React, { useEffect, useState } from 'react';
import { FiX, FiCpu, FiMapPin, FiCheckCircle, FiAlertTriangle, FiGitCommit } from 'react-icons/fi';
import apiClient from '../../services/api';
import Loading from '../common/Loading';

/**
 * Slide-over drawer component displaying detailed topology, parent/children poles, and attached device info.
 */
const PoleDetailDrawer = ({ poleCode, onClose }) => {
  const [poleData, setPoleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!poleCode) return;
    const fetchPoleDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiClient.get(`/pole-registry/${poleCode}`);
        setPoleData(data || null);
      } catch (err) {
        setError(err.message || 'Failed to fetch pole details.');
      } finally {
        setLoading(false);
      }
    };
    fetchPoleDetail();
  }, [poleCode]);

  if (!poleCode) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white border-l border-slate-200 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-brand-600 rounded-lg">
                <FiCpu className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-base font-bold tracking-tight">{poleCode}</h2>
                <p className="text-[11px] text-slate-400">Pole Topology & Device Spec</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-white rounded-lg"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {loading ? (
              <Loading message="Loading pole details..." />
            ) : error ? (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                {error}
              </div>
            ) : poleData ? (
              <>
                {/* Status Badges */}
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                      poleData?.topology_known
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}
                  >
                    {poleData?.topology_known ? 'Topology Mapped' : 'Unknown Topology'}
                  </span>

                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                      poleData?.device_installed
                        ? 'bg-brand-50 text-brand-700 border border-brand-200'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {poleData?.device_installed ? 'IoT Device Installed' : 'No Device'}
                  </span>
                </div>

                {/* Grid Network Context */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 text-xs">
                  <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                    Grid Feeder & Transformer
                  </h3>
                  <div className="grid grid-cols-2 gap-2 text-slate-700">
                    <div>
                      <span className="text-slate-400 block">Feeder Code</span>
                      <span className="font-medium text-slate-900">{poleData?.feeder?.feeder_code ?? poleData?.feeder_code ?? 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Transformer (DT)</span>
                      <span className="font-medium text-slate-900">{poleData?.transformer?.transformer_code ?? poleData?.transformer_code ?? 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Capacity</span>
                      <span className="font-medium text-slate-900">{poleData?.transformer?.capacity_kva ?? '--'} kVA</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Pole Type</span>
                      <span className="font-medium text-slate-900">{poleData?.pole_type ?? 'N/A'}</span>
                    </div>
                  </div>
                </div>

                {/* Location Specs */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 text-xs">
                  <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1">
                    <FiMapPin className="w-3.5 h-3.5 text-brand-600" />
                    Geographical Location
                  </h3>
                  <div className="grid grid-cols-2 gap-2 text-slate-700">
                    <div>
                      <span className="text-slate-400 block">Latitude</span>
                      <span className="font-mono text-slate-900">{poleData?.latitude != null ? Number(poleData.latitude).toFixed(4) : '--'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Longitude</span>
                      <span className="font-mono text-slate-900">{poleData?.longitude != null ? Number(poleData.longitude).toFixed(4) : '--'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Ward</span>
                      <span className="font-medium text-slate-900">{poleData?.ward || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Pincode</span>
                      <span className="font-medium text-slate-900">{poleData?.pincode || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                {/* Radial Topology Tree */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 text-xs">
                  <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1">
                    <FiGitCommit className="w-3.5 h-3.5 text-brand-600" />
                    Radial Network Topology
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg">
                      <span className="text-slate-500">Parent Pole</span>
                      <span className="font-semibold text-slate-900">
                        {poleData?.parent_pole?.pole_code ?? poleData?.parent_pole_code ?? 'None (Root Node)'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg">
                      <span className="text-slate-500">Sequence On Line</span>
                      <span className="font-semibold text-slate-900">
                        {poleData?.seq_on_line !== null && poleData?.seq_on_line !== undefined ? poleData.seq_on_line : 'N/A'}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white border border-slate-200 rounded-lg">
                      <span className="text-slate-500 block mb-1">Downstream Branch Poles ({Array.isArray(poleData?.children_poles) ? poleData.children_poles.length : 0})</span>
                      {Array.isArray(poleData?.children_poles) && poleData.children_poles.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {poleData.children_poles.map((c) => (
                            <span
                              key={c?.id || c?.pole_code}
                              className="px-2 py-0.5 bg-brand-50 text-brand-700 font-mono text-[10px] rounded border border-brand-200"
                            >
                              {c?.pole_code}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-[11px]">No child poles</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Attached IoT Device */}
                {poleData?.device && (
                  <div className="bg-brand-50/50 border border-brand-200 rounded-xl p-4 space-y-3 text-xs">
                    <h3 className="font-bold text-brand-900 uppercase tracking-wider text-[11px]">
                      Attached Physical IoT Device
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-slate-700">
                      <div>
                        <span className="text-slate-400 block">Device ID</span>
                        <span className="font-mono font-bold text-brand-700">{poleData.device?.device_id || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Firmware</span>
                        <span className="font-mono text-slate-900">{poleData.device?.firmware_version || '1.0.0'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Battery Voltage</span>
                        <span className="font-mono text-slate-900">{poleData.device?.battery_mv != null ? `${poleData.device.battery_mv} mV` : '---'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Signal RSSI</span>
                        <span className="font-mono text-slate-900">{poleData.device?.last_rssi != null ? `${poleData.device.last_rssi} dBm` : '---'}</span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PoleDetailDrawer;
