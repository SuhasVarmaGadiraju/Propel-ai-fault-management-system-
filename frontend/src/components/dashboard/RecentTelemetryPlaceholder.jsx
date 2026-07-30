import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { FiActivity, FiArrowRight } from 'react-icons/fi';

const dummyTelemetryData = [
  { id: 'POLE-101', voltage: '230.4 V', current: '14.2 A', freq: '50.0 Hz', status: 'Normal', timestamp: '10:42:15 AM' },
  { id: 'POLE-102', voltage: '215.1 V', current: '18.9 A', freq: '49.8 Hz', status: 'Warning', timestamp: '10:42:12 AM' },
  { id: 'POLE-103', voltage: '0.0 V', current: '0.0 A', freq: '0.0 Hz', status: 'Faulted', timestamp: '10:41:58 AM' },
  { id: 'POLE-104', voltage: '229.8 V', current: '12.5 A', freq: '50.1 Hz', status: 'Normal', timestamp: '10:41:45 AM' },
  { id: 'POLE-105', voltage: '231.0 V', current: '13.0 A', freq: '50.0 Hz', status: 'Normal', timestamp: '10:41:30 AM' },
];

/**
 * Recent Telemetry Data Table Placeholder Component
 */
const RecentTelemetryPlaceholder = () => {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center gap-2">
          <FiActivity className="w-5 h-5 text-brand-600" />
          <CardTitle>Recent Telemetry Stream</CardTitle>
        </div>
        <span className="text-xs text-slate-500 font-medium">Dummy Telemetry Feed</span>
      </CardHeader>

      <CardContent className="p-0 flex-1 overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-700">
          <thead className="bg-slate-50 text-slate-500 text-xs font-semibold uppercase tracking-wider border-b border-slate-100">
            <tr>
              <th className="px-6 py-3">Pole ID</th>
              <th className="px-6 py-3">Voltage</th>
              <th className="px-6 py-3">Current</th>
              <th className="px-6 py-3">Frequency</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {dummyTelemetryData.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-6 py-3.5 font-medium text-slate-900">{row.id}</td>
                <td className="px-6 py-3.5 font-mono text-xs">{row.voltage}</td>
                <td className="px-6 py-3.5 font-mono text-xs">{row.current}</td>
                <td className="px-6 py-3.5 font-mono text-xs">{row.freq}</td>
                <td className="px-6 py-3.5">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      row.status === 'Normal'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : row.status === 'Warning'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}
                  >
                    {row.status}
                  </span>
                </td>
                <td className="px-6 py-3.5 text-xs text-slate-500">{row.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
};

export default RecentTelemetryPlaceholder;
