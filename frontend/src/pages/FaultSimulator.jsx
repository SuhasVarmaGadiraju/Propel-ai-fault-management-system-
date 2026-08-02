import React, { useEffect, useState } from 'react';
import {
  FiZap,
  FiRadio,
  FiAlertCircle,
  FiCheckCircle,
  FiClock,
  FiPlay,
  FiRefreshCw,
  FiLayers,
  FiSliders,
  FiCpu,
  FiActivity,
  FiClipboard,
  FiServer,
  FiTarget,
  FiAlertOctagon
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';
import { formatDate } from '../utils/helpers';

/**
 * Production Interactive Fault Simulator Page.
 * Allows operators and reviewers to inject synthetic outage scenarios through the existing
 * telemetry pipeline and verify the complete end-to-end fault management workflow.
 */
const FaultSimulator = () => {
  const [scenarios, setScenarios] = useState([]);
  const [history, setHistory] = useState([]);
  const [feeders, setFeeders] = useState([]);
  const [transformers, setTransformers] = useState([]);
  const [poles, setPoles] = useState([]);

  // Selections
  const [selectedScenario, setSelectedScenario] = useState('small_span_fault');
  const [selectedFeeder, setSelectedFeeder] = useState('');
  const [selectedTransformer, setSelectedTransformer] = useState('');
  const [selectedPole, setSelectedPole] = useState('');

  // Execution states
  const [executing, setExecuting] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const fetchScenariosAndHistory = async () => {
    try {
      const [scenData, histData] = await Promise.all([
        apiClient.get('/simulator/scenarios'),
        apiClient.get('/simulator/history')
      ]);
      setScenarios(Array.isArray(scenData) ? scenData : []);
      setHistory(Array.isArray(histData) ? histData : []);
    } catch (err) {
      console.error('Failed to fetch simulator presets/history:', err);
      setScenarios([]);
      setHistory([]);
    }
  };

  const fetchNetworkTopology = async () => {
    try {
      const treeData = await apiClient.get('/network/tree');
      if (treeData && Array.isArray(treeData.feeders) && treeData.feeders.length > 0) {
        setFeeders(treeData.feeders);
        const f0 = treeData.feeders[0];
        setSelectedFeeder(f0.code || '');
        if (Array.isArray(f0.transformers) && f0.transformers.length > 0) {
          setTransformers(f0.transformers);
          const tr0 = f0.transformers[0];
          setSelectedTransformer(tr0.code || '');
          if (Array.isArray(tr0.root_poles) && tr0.root_poles.length > 0) {
            setPoles(tr0.root_poles);
            setSelectedPole(tr0.root_poles[0].code || '');
          }
        }
      }
    } catch (err) {
      console.error('Failed to fetch topology trees for simulator:', err);
    }
  };

  useEffect(() => {
    fetchScenariosAndHistory();
    fetchNetworkTopology();
  }, []);

  const handleFeederChange = (code) => {
    setSelectedFeeder(code);
    const f = Array.isArray(feeders) ? feeders.find((item) => item?.code === code) : null;
    if (f && Array.isArray(f.transformers)) {
      setTransformers(f.transformers);
      if (f.transformers.length > 0) {
        setSelectedTransformer(f.transformers[0].code || '');
        setPoles(Array.isArray(f.transformers[0].root_poles) ? f.transformers[0].root_poles : []);
      }
    }
  };

  const handleTransformerChange = (code) => {
    setSelectedTransformer(code);
    const tr = Array.isArray(transformers) ? transformers.find((item) => item?.code === code) : null;
    if (tr && Array.isArray(tr.root_poles)) {
      setPoles(tr.root_poles);
      if (tr.root_poles.length > 0) {
        setSelectedPole(tr.root_poles[0].code || '');
      }
    }
  };

  const handleRunSimulation = async (scenarioIdOverride = null) => {
    const scenId = scenarioIdOverride || selectedScenario;
    setExecuting(true);
    try {
      const payload = {
        scenario_id: scenId,
        feeder_id: selectedFeeder,
        transformer_id: selectedTransformer,
        pole_id: selectedPole,
      };
      const res = await apiClient.post('/simulator/run', payload);
      setLastResult(res || null);
      fetchScenariosAndHistory();
    } catch (err) {
      console.error('Simulation execution failed:', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleRestorePower = async () => {
    setRestoring(true);
    try {
      const res = await apiClient.post('/simulator/restore', { target_id: selectedFeeder });
      setLastResult(res || null);
      fetchScenariosAndHistory();
    } catch (err) {
      console.error('Power restoration failed:', err);
    } finally {
      setRestoring(false);
    }
  };

  const handleResetSimulator = async () => {
    try {
      await apiClient.post('/simulator/reset');
      setLastResult(null);
      fetchScenariosAndHistory();
    } catch (err) {
      console.error('Reset failed:', err);
    }
  };

  const iconMap = {
    zap: FiZap,
    radio: FiRadio,
    'shield-alert': FiAlertOctagon,
    'alert-circle': FiAlertCircle,
    layers: FiLayers,
    clock: FiClock,
    'check-circle': FiCheckCircle,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiSliders className="w-6 h-6 text-brand-600" />
            Interactive Electrical Fault Simulator
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Inject synthetic telemetry, simulate outages, and exercise the end-to-end fault management pipeline
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRestorePower}
            disabled={restoring}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-xs shadow-xs transition-colors disabled:opacity-50"
          >
            <FiCheckCircle className={`w-4 h-4 ${restoring ? 'animate-spin' : ''}`} />
            {restoring ? 'Restoring Power...' : 'Restore Grid Power'}
          </button>
          <button
            onClick={handleResetSimulator}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold rounded-xl text-xs transition-colors"
          >
            <FiRefreshCw className="w-3.5 h-3.5" />
            Reset Cache
          </button>
        </div>
      </div>

      {/* Target Selector & Simulator Action Card */}
      <Card className="p-5 bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 text-white border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 flex-1">
            <h2 className="text-sm font-bold uppercase tracking-wider text-brand-400 flex items-center gap-2">
              <FiTarget className="w-4 h-4" />
              Target Network Location & Hardware
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Target Feeder</label>
                <select
                  value={selectedFeeder}
                  onChange={(e) => handleFeederChange(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {Array.isArray(feeders) && feeders.map((f) => (
                    <option key={f.code} value={f.code}>
                      {f.code} - {f.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Target Transformer</label>
                <select
                  value={selectedTransformer}
                  onChange={(e) => handleTransformerChange(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {Array.isArray(transformers) && transformers.map((tr) => (
                    <option key={tr.code} value={tr.code}>
                      {tr.code} ({tr.total_poles ?? 0} poles)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Target Pole</label>
                <select
                  value={selectedPole}
                  onChange={(e) => setSelectedPole(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {Array.isArray(poles) && poles.map((p) => (
                    <option key={p.code} value={p.code}>
                      {p.code}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="shrink-0 flex flex-col justify-end">
            <button
              onClick={() => handleRunSimulation()}
              disabled={executing}
              className="w-full lg:w-auto px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded-xl text-xs shadow-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <FiPlay className={`w-4 h-4 ${executing ? 'animate-spin' : ''}`} />
              {executing ? 'Injecting Telemetry...' : 'Inject Fault Simulation'}
            </button>
          </div>
        </div>
      </Card>

      {/* Preset Scenario Cards Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
          <FiLayers className="w-4 h-4 text-brand-600" />
          Built-in Outage Scenario Presets
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.isArray(scenarios) && scenarios.map((scen) => {
            const IconComp = iconMap[scen.icon] || FiZap;
            const isSelected = selectedScenario === scen.id;

            return (
              <Card
                key={scen.id}
                onClick={() => setSelectedScenario(scen.id)}
                className={`p-4 cursor-pointer transition-all border-2 space-y-3 ${
                  isSelected
                    ? 'border-brand-500 bg-brand-50/20 shadow-md ring-2 ring-brand-500/20'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'}`}>
                    <IconComp className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                    {scen.category}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-xs">{scen.name}</h3>
                  <p className="text-[11px] text-slate-500 mt-1 leading-snug">{scen.description}</p>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                  <span className={`font-semibold ${isSelected ? 'text-brand-700' : 'text-slate-500'}`}>
                    {isSelected ? 'Selected Scenario' : 'Click to select'}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedScenario(scen.id);
                      handleRunSimulation(scen.id);
                    }}
                    className="px-2.5 py-1 bg-slate-900 hover:bg-brand-600 text-white rounded font-bold text-[10px] transition-colors"
                  >
                    Run Now
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Live Execution Panel */}
      {lastResult && (
        <Card className="p-6 space-y-4 border-l-4 border-l-brand-600 bg-slate-900 text-white">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <FiActivity className="w-5 h-5 text-brand-400" />
              <h3 className="font-bold text-sm text-white">Simulation Execution Results</h3>
            </div>
            <span className="text-xs font-mono text-emerald-400">
              Duration: {lastResult.simulation ? lastResult.simulation.duration_ms : 0}ms
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Ingestion Output */}
            <div className="bg-slate-850 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold uppercase text-[10px] block flex items-center gap-1">
                <FiServer className="w-3.5 h-3.5 text-brand-400" />
                Telemetry Ingestion
              </span>
              <div className="font-mono text-emerald-400">
                Injected: {lastResult.ingestion ? lastResult.ingestion.processed : 0} sensors
              </div>
              <p className="text-[11px] text-slate-400">
                Submitted through POST /api/v1/telemetry ingestion pipeline without DB bypassing.
              </p>
            </div>

            {/* Fault Localization Output */}
            <div className="bg-slate-850 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold uppercase text-[10px] block flex items-center gap-1">
                <FiCpu className="w-3.5 h-3.5 text-amber-400" />
                Fault Localization Result
              </span>
              {lastResult.fault_localization && Array.isArray(lastResult.fault_localization.incidents) && lastResult.fault_localization.incidents.length > 0 ? (
                <div className="space-y-1">
                  <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 font-bold rounded text-[11px] inline-block font-mono">
                    {lastResult.fault_localization.incidents[0].fault_type}
                  </span>
                  <p className="text-[11px] text-slate-300 font-mono">
                    Confidence: {lastResult.fault_localization.incidents[0].confidence}%
                  </p>
                </div>
              ) : (
                <div className="text-emerald-400 font-semibold text-[11px]">
                  0 Outages / Sensor Anomaly Glitch
                </div>
              )}
            </div>

            {/* Created Ticket Output */}
            <div className="bg-slate-850 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold uppercase text-[10px] block flex items-center gap-1">
                <FiClipboard className="w-3.5 h-3.5 text-purple-400" />
                Automated Repair Ticket
              </span>
              {Array.isArray(lastResult.tickets_created) && lastResult.tickets_created.length > 0 ? (
                <div className="space-y-1">
                  <span className="font-mono font-bold text-purple-300 text-xs">
                    {lastResult.tickets_created[0].ticket_number}
                  </span>
                  <span className="ml-2 text-[10px] uppercase font-bold text-red-400 border border-red-500/40 px-1.5 py-0.5 rounded">
                    {lastResult.tickets_created[0].priority}
                  </span>
                </div>
              ) : (
                <div className="text-slate-400 text-[11px]">No ticket spawned</div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Simulation Audit History Table */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <FiClock className="w-4 h-4 text-brand-600" />
            Simulation Execution Audit Log ({Array.isArray(history) ? history.length : 0})
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">ID</th>
                <th className="px-6 py-3.5">Scenario</th>
                <th className="px-6 py-3.5">Target</th>
                <th className="px-6 py-3.5">Telemetry</th>
                <th className="px-6 py-3.5">Incidents</th>
                <th className="px-6 py-3.5">Tickets Spawned</th>
                <th className="px-6 py-3.5">Execution Time</th>
                <th className="px-6 py-3.5 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {Array.isArray(history) && history.length > 0 ? (
                history.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-3.5 font-mono font-bold text-slate-900">{h.id}</td>
                    <td className="px-6 py-3.5 font-bold text-slate-800">{h.scenario_name}</td>
                    <td className="px-6 py-3.5 font-mono text-brand-700 font-semibold">{h.target}</td>
                    <td className="px-6 py-3.5 text-slate-600">{h.telemetry_injected} sensors</td>
                    <td className="px-6 py-3.5 font-semibold text-amber-700">{h.incidents_detected} outages</td>
                    <td className="px-6 py-3.5 font-mono font-bold text-purple-700">
                      {Array.isArray(h.ticket_numbers) && h.ticket_numbers.length > 0 ? h.ticket_numbers.join(', ') : '0'}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-emerald-700 font-bold">{h.duration_ms}ms</td>
                    <td className="px-6 py-3.5 text-right font-mono text-slate-500">{formatDate(h.timestamp)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400 italic">
                    No simulation executions logged yet. Select a scenario above to run a simulation.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default FaultSimulator;
