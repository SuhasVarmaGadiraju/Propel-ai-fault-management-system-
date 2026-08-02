import React, { useState, useEffect } from 'react';
import {
  FiSend,
  FiRepeat,
  FiAlertTriangle,
  FiCheckCircle,
  FiTerminal,
  FiCopy,
  FiZap,
  FiActivity,
  FiLayers,
  FiXCircle
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';

/**
 * Developer Telemetry Tester Page Component for end-to-end verification.
 */
const TelemetryTester = () => {
  const [stats, setStats] = useState(null);

  // Form input state
  const [deviceId, setDeviceId] = useState('KSPDB-SD07-D0112-4431');
  const [poleId, setPoleId] = useState('POL-NORTH-01-001');
  const [event, setEvent] = useState('power_lost');
  const [energized, setEnergized] = useState(false);
  const [seq, setSeq] = useState(1001);
  const [batteryMv, setBatteryMv] = useState(3480);
  const [rssi, setRssi] = useState(-91);
  const [firmware, setFirmware] = useState('1.4.2');

  // Diagnostics output state
  const [requestConsole, setRequestConsole] = useState(null);
  const [responseConsole, setResponseConsole] = useState(null);
  const [statusCode, setStatusCode] = useState(null);
  const [isSending, setIsSending] = useState(false);

  const fetchStatistics = async () => {
    try {
      const data = await apiClient.get('/telemetry/statistics');
      setStats(data || null);
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, []);

  const sendPayload = async (payload, endpoint = '/telemetry') => {
    setIsSending(true);
    setRequestConsole(payload);
    setResponseConsole(null);
    setStatusCode(null);

    try {
      const response = await apiClient.post(endpoint, payload);
      setStatusCode(200);
      setResponseConsole(response);
    } catch (err) {
      setStatusCode(err?.status || 400);
      setResponseConsole({
        error: err?.message || 'Request failed',
        status: err?.status
      });
    } finally {
      setIsSending(false);
      fetchStatistics();
    }
  };

  // 1. Send Current Custom Telemetry
  const handleSendCustom = () => {
    const payload = {
      device_id: deviceId,
      pole_id: poleId,
      event,
      energized,
      ts: new Date().toISOString(),
      seq: Number(seq),
      battery_mv: Number(batteryMv),
      rssi: Number(rssi),
      fw: firmware
    };
    sendPayload(payload);
  };

  // 2. Duplicate Test: Sends exact same packet again
  const handleDuplicateTest = async () => {
    const payload = {
      device_id: deviceId,
      pole_id: poleId,
      event: 'heartbeat',
      energized: true,
      ts: new Date().toISOString(),
      seq: Number(seq),
      battery_mv: Number(batteryMv),
      rssi: Number(rssi),
      fw: firmware
    };
    await sendPayload(payload);
  };

  // 3. Out-of-Order Test: Sends seq 2000, then seq 1900
  const handleOutOfOrderTest = async () => {
    const now = new Date().toISOString();
    const payloadHighSeq = {
      device_id: deviceId,
      pole_id: poleId,
      event: 'heartbeat',
      energized: true,
      ts: now,
      seq: 2000,
      battery_mv: 4000,
      rssi: -60,
      fw: firmware
    };

    const payloadOlderSeq = {
      device_id: deviceId,
      pole_id: poleId,
      event: 'power_lost',
      energized: false,
      ts: new Date(Date.now() - 60000).toISOString(),
      seq: 1900,
      battery_mv: 3900,
      rssi: -70,
      fw: firmware
    };

    // First send seq 2000
    await sendPayload(payloadHighSeq);
    // Then send older seq 1900
    setTimeout(() => {
      sendPayload(payloadOlderSeq);
    }, 500);
  };

  // 4. Bulk 100 Packets Test
  const handleBulkTest = () => {
    const events = ['heartbeat', 'power_lost', 'power_restored', 'boot'];
    const bulkArray = [];
    const baseSeq = Math.floor(Math.random() * 5000) + 3000;

    for (let i = 0; i < 100; i++) {
      const evt = events[Math.floor(Math.random() * events.length)];
      const numStr = String((i % 10) + 1).padStart(4, '0');
      bulkArray.push({
        device_id: `KSPDB-SD07-D0112-${numStr}`,
        pole_id: poleId,
        event: evt,
        energized: evt !== 'power_lost',
        ts: new Date().toISOString(),
        seq: baseSeq + i,
        battery_mv: Math.floor(Math.random() * 800) + 3400,
        rssi: Math.floor(Math.random() * 45) - 95,
        fw: firmware
      });
    }

    sendPayload(bulkArray, '/telemetry/bulk');
  };

  // 5. Error Validation Tests
  const handleTestInvalidDevice = () => {
    const payload = {
      device_id: '',
      pole_id: poleId,
      event: 'heartbeat',
      energized: true,
      ts: new Date().toISOString(),
      seq: 9999
    };
    sendPayload(payload);
  };

  const handleTestInvalidPole = () => {
    const payload = {
      device_id: deviceId,
      pole_id: 'POL-NONEXISTENT-999',
      event: 'heartbeat',
      energized: true,
      ts: new Date().toISOString(),
      seq: 9998
    };
    sendPayload(payload);
  };

  const handleTestMissingFields = () => {
    const payload = {
      device_id: deviceId,
      pole_id: poleId,
      // Missing event and energized
      seq: 9997
    };
    sendPayload(payload);
  };

  const handleTestInvalidTimestamp = () => {
    const payload = {
      device_id: deviceId,
      pole_id: poleId,
      event: 'heartbeat',
      energized: true,
      ts: 'INVALID-TIMESTAMP-STRING',
      seq: 9996
    };
    sendPayload(payload);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiTerminal className="w-6 h-6 text-brand-600" />
            Telemetry API Testing Utility
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Developer sandbox tool for verifying ingestion, deduplication, sequence ordering, and validation errors
          </p>
        </div>

        <span className="px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold rounded-lg">
          Development Utility Only
        </span>
      </div>

      {/* Auto-Refreshed Live Statistics Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Telemetry"
          value={stats?.total_telemetry != null ? Number(stats.total_telemetry).toLocaleString() : '---'}
          statusText="Stored Database Events"
          icon={FiActivity}
          colorTheme="blue"
        />
        <StatCard
          title="Power Outages"
          value={stats?.power_lost != null ? Number(stats.power_lost).toLocaleString() : '---'}
          statusText="Power Lost Events"
          icon={FiZap}
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
          title="Out of Order"
          value={stats?.out_of_order_messages != null ? Number(stats.out_of_order_messages).toLocaleString() : '---'}
          statusText="Lagging Sequence Events"
          icon={FiAlertTriangle}
          colorTheme="amber"
        />
        <StatCard
          title="Online Devices"
          value={stats?.currently_online_devices != null ? Number(stats.currently_online_devices).toLocaleString() : '---'}
          statusText="Communicated < 15m"
          icon={FiZap}
          colorTheme="blue"
        />
      </div>

      {/* Main Grid: Form Customizer & Automated Test Preset Buttons */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Manual Payload Customizer Form */}
        <Card className="lg:col-span-1 p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <FiZap className="w-4 h-4 text-brand-600" />
            Payload Customizer
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Device ID</label>
              <input
                type="text"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Pole Code</label>
              <input
                type="text"
                value={poleId}
                onChange={(e) => setPoleId(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Event Type</label>
                <select
                  value={event}
                  onChange={(e) => {
                    setEvent(e.target.value);
                    if (e.target.value === 'power_lost') setEnergized(false);
                    if (e.target.value === 'power_restored') setEnergized(true);
                  }}
                  className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="heartbeat">heartbeat</option>
                  <option value="power_lost">power_lost</option>
                  <option value="power_restored">power_restored</option>
                  <option value="boot">boot</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Sequence #</label>
                <input
                  type="number"
                  value={seq}
                  onChange={(e) => setSeq(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Battery (mV)</label>
                <input
                  type="number"
                  value={batteryMv}
                  onChange={(e) => setBatteryMv(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">RSSI (dBm)</label>
                <input
                  type="number"
                  value={rssi}
                  onChange={(e) => setRssi(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="energized-check"
                checked={energized}
                onChange={(e) => setEnergized(e.target.checked)}
                className="w-4 h-4 text-brand-600 rounded"
              />
              <label htmlFor="energized-check" className="font-semibold text-slate-700 cursor-pointer">
                Energized (Power Active)
              </label>
            </div>
          </div>

          <button
            onClick={handleSendCustom}
            disabled={isSending}
            className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl text-xs shadow-sm transition-colors flex items-center justify-center gap-2"
          >
            <FiSend className="w-4 h-4" />
            Send Custom Telemetry
          </button>
        </Card>

        {/* Quick Test Presets & Validation Triggers */}
        <Card className="lg:col-span-2 p-6 space-y-6">
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <FiRepeat className="w-4 h-4 text-brand-600" />
            Automated Ingestion Test Scenarios
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Duplicate Test */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <h4 className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                <FiCopy className="w-4 h-4 text-brand-600" />
                Duplicate Detection Test
              </h4>
              <p className="text-[11px] text-slate-500">
                Sends the exact same sequence payload twice to verify deduplication status response.
              </p>
              <button
                onClick={handleDuplicateTest}
                className="w-full py-1.5 bg-white border border-slate-200 hover:border-brand-500 hover:text-brand-600 text-slate-700 font-semibold rounded-lg text-xs transition-colors"
              >
                Send Duplicate Packet
              </button>
            </div>

            {/* Out-of-Order Test */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <h4 className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                <FiAlertTriangle className="w-4 h-4 text-amber-500" />
                Out-of-Order Sequence Test
              </h4>
              <p className="text-[11px] text-slate-500">
                Sends seq 2000, then sends seq 1900 to verify backend out_of_order tagging.
              </p>
              <button
                onClick={handleOutOfOrderTest}
                className="w-full py-1.5 bg-white border border-slate-200 hover:border-amber-500 hover:text-amber-600 text-slate-700 font-semibold rounded-lg text-xs transition-colors"
              >
                Send Out-of-Order Packet
              </button>
            </div>

            {/* Bulk 100 Test */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <h4 className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                <FiLayers className="w-4 h-4 text-brand-600" />
                100 Bulk Array Ingestion Test
              </h4>
              <p className="text-[11px] text-slate-500">
                Generates 100 random events and posts to POST /api/v1/telemetry/bulk.
              </p>
              <button
                onClick={handleBulkTest}
                className="w-full py-1.5 bg-white border border-slate-200 hover:border-brand-500 hover:text-brand-600 text-slate-700 font-semibold rounded-lg text-xs transition-colors"
              >
                Send 100 Bulk Array
              </button>
            </div>

            {/* Error Validation Tests */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <h4 className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                <FiXCircle className="w-4 h-4 text-red-500" />
                Validation Error Tests
              </h4>
              <p className="text-[11px] text-slate-500">
                Trigger malformed or invalid requests to test 400/404 HTTP responses.
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={handleTestInvalidDevice}
                  className="py-1 px-2 bg-white border border-slate-200 hover:border-red-500 text-slate-700 rounded text-[10px] font-medium"
                >
                  Invalid Device
                </button>
                <button
                  onClick={handleTestInvalidPole}
                  className="py-1 px-2 bg-white border border-slate-200 hover:border-red-500 text-slate-700 rounded text-[10px] font-medium"
                >
                  Invalid Pole
                </button>
                <button
                  onClick={handleTestMissingFields}
                  className="py-1 px-2 bg-white border border-slate-200 hover:border-red-500 text-slate-700 rounded text-[10px] font-medium"
                >
                  Missing Fields
                </button>
                <button
                  onClick={handleTestInvalidTimestamp}
                  className="py-1 px-2 bg-white border border-slate-200 hover:border-red-500 text-slate-700 rounded text-[10px] font-medium"
                >
                  Bad Timestamp
                </button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Diagnostics Console Output */}
      <Card className="p-6 space-y-4 bg-slate-950 text-slate-100 font-mono">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-sans">
            <FiTerminal className="w-4 h-4 text-emerald-400" />
            API Diagnostics Console
          </h3>

          {statusCode && (
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                statusCode >= 200 && statusCode < 300
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}
            >
              HTTP {statusCode}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block mb-1 font-sans text-[11px] font-semibold">
              Request Payload:
            </span>
            <pre className="p-3 bg-slate-900 rounded-lg text-brand-300 max-h-60 overflow-y-auto">
              {requestConsole ? JSON.stringify(requestConsole, null, 2) : '// Click a test action above to inspect request'}
            </pre>
          </div>

          <div>
            <span className="text-slate-400 block mb-1 font-sans text-[11px] font-semibold">
              Server Response Body:
            </span>
            <pre className="p-3 bg-slate-900 rounded-lg text-emerald-400 max-h-60 overflow-y-auto">
              {responseConsole ? JSON.stringify(responseConsole, null, 2) : '// Server response JSON will appear here'}
            </pre>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default TelemetryTester;
