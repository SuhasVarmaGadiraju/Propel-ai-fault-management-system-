import React from 'react';
import { FiX, FiActivity, FiBattery, FiWifi, FiCheckCircle, FiAlertTriangle, FiCode } from 'react-icons/fi';
import { formatDate } from '../../utils/helpers';

/**
 * Slide-over drawer component displaying detailed telemetry event metrics and formatted raw JSON.
 */
const TelemetryDetailDrawer = ({ telemetry, onClose }) => {
  if (!telemetry) return null;

  const eventColorMap = {
    heartbeat: 'bg-blue-50 text-blue-700 border-blue-200',
    power_lost: 'bg-red-50 text-red-700 border-red-200 font-bold animate-pulse',
    power_restored: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold',
    boot: 'bg-purple-50 text-purple-700 border-purple-200',
    fault_detected: 'bg-amber-50 text-amber-700 border-amber-200 font-bold',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white border-l border-slate-200 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-brand-600 rounded-lg">
                <FiActivity className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-base font-bold tracking-tight">Telemetry Event Detail</h2>
                <p className="text-[11px] text-slate-400 font-mono">Seq: {telemetry.sequence_number}</p>
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
          <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
            {/* Status Badges */}
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
                  eventColorMap[telemetry.event] || 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {telemetry.event.replace('_', ' ')}
              </span>

              {telemetry.out_of_order && (
                <span className="inline-flex items-center gap-1 px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-full font-semibold">
                  <FiAlertTriangle className="w-3.5 h-3.5" />
                  Out of Order Message
                </span>
              )}
            </div>

            {/* Event Metrics Box */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Hardware & Location Metrics
              </h3>
              <div className="grid grid-cols-2 gap-3 text-slate-700">
                <div>
                  <span className="text-slate-400 block">Device ID</span>
                  <span className="font-mono font-bold text-brand-700">{telemetry.device_id}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Pole Code</span>
                  <span className="font-mono font-bold text-slate-900">{telemetry.pole_code}</span>
                </div>
                <div>
                  <span className="text-slate-400 block flex items-center gap-1">
                    <FiBattery className="w-3.5 h-3.5 text-slate-400" />
                    Battery Voltage
                  </span>
                  <span className="font-mono text-slate-900">{telemetry.battery_mv} mV</span>
                </div>
                <div>
                  <span className="text-slate-400 block flex items-center gap-1">
                    <FiWifi className="w-3.5 h-3.5 text-slate-400" />
                    Signal RSSI
                  </span>
                  <span className="font-mono text-slate-900">{telemetry.rssi} dBm</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Firmware</span>
                  <span className="font-mono text-slate-900">{telemetry.firmware_version}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Energized</span>
                  <span className={`font-bold ${telemetry.energized ? 'text-emerald-600' : 'text-red-600'}`}>
                    {telemetry.energized ? 'TRUE (Powered)' : 'FALSE (Outage)'}
                  </span>
                </div>
              </div>
            </div>

            {/* Timestamps */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Event Timestamps
              </h3>
              <div className="space-y-1.5 text-slate-600">
                <div className="flex justify-between">
                  <span className="text-slate-400">Sensor Event Time:</span>
                  <span className="font-mono font-semibold text-slate-900">
                    {formatDate(telemetry.event_timestamp)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Server Received:</span>
                  <span className="font-mono text-slate-700">
                    {formatDate(telemetry.received_timestamp)}
                  </span>
                </div>
              </div>
            </div>

            {/* Raw Ingest Payload */}
            <div className="bg-slate-900 text-slate-200 border border-slate-800 rounded-xl p-4 space-y-2 font-mono">
              <h3 className="text-slate-400 uppercase tracking-wider text-[11px] font-sans font-bold flex items-center gap-1.5">
                <FiCode className="w-4 h-4 text-brand-400" />
                Raw Event Payload
              </h3>
              <pre className="text-[11px] leading-relaxed overflow-x-auto text-emerald-400">
{JSON.stringify({
  device_id: telemetry.device_id,
  pole_id: telemetry.pole_code,
  event: telemetry.event,
  energized: telemetry.energized,
  ts: telemetry.event_timestamp,
  seq: telemetry.sequence_number,
  battery_mv: telemetry.battery_mv,
  rssi: telemetry.rssi,
  fw: telemetry.firmware_version,
  out_of_order: telemetry.out_of_order
}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TelemetryDetailDrawer;
