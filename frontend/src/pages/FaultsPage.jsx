import React, { useEffect, useState } from 'react';
import {
  FiAlertTriangle,
  FiRefreshCw,
  FiZap,
  FiRadio,
  FiCpu,
  FiUsers,
  FiClock,
  FiInfo,
  FiSearch,
  FiCheckCircle,
  FiAlertCircle,
  FiChevronDown,
  FiChevronUp,
  FiTarget
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';
import { formatDate } from '../utils/helpers';

/**
 * Advanced Fault Detection Dashboard Page displaying deterministic localization results,
 * confidence scores, gap ranges, and step-by-step reasoning narrative cards.
 */
const FaultsPage = () => {
  const [summary, setSummary] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  // Filters
  const [filterType, setFilterType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Expanded reasoning drawer cards
  const [expandedReasoning, setExpandedReasoning] = useState({});

  const fetchLatestFaults = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/faults/latest');
      setSummary(data.summary);
      setIncidents(data.incidents || []);
      setAnomalies(data.sensor_anomalies || []);
    } catch (err) {
      console.error('Failed to fetch fault localization results:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      const data = await apiClient.post('/faults/analyze');
      setSummary(data.summary);
      setIncidents(data.incidents || []);
      setAnomalies(data.sensor_anomalies || []);
    } catch (err) {
      console.error('Failed to run fault localization analysis:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  useEffect(() => {
    fetchLatestFaults();
  }, []);

  const toggleReasoning = (incidentId) => {
    setExpandedReasoning((prev) => ({
      ...prev,
      [incidentId]: !prev[incidentId]
    }));
  };

  // Filtered incidents list
  const filteredIncidents = incidents.filter((inc) => {
    const matchesType = filterType === 'ALL' || inc.fault_type === filterType;
    const matchesQuery =
      searchQuery === '' ||
      inc.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.feeder_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inc.transformer_code && inc.transformer_code.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (inc.upstream_pole && inc.upstream_pole.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (inc.downstream_pole && inc.downstream_pole.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesType && matchesQuery;
  });

  const badgeThemeMap = {
    SPAN_FAULT: 'bg-amber-50 text-amber-700 border-amber-200 font-bold',
    UNKNOWN_SPAN: 'bg-slate-100 text-slate-700 border-slate-300 font-bold',
    TRANSFORMER_FAULT: 'bg-red-50 text-red-700 border-red-200 font-bold',
    FEEDER_FAULT: 'bg-purple-50 text-purple-700 border-purple-200 font-bold',
  };

  const getConfidenceBadge = (score) => {
    if (score >= 90) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    if (score >= 70) return 'bg-amber-100 text-amber-800 border-amber-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiAlertTriangle className="w-6 h-6 text-red-600" />
            Advanced Deterministic Fault Localization Engine
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Span boundaries, confidence scoring (0-100%), gap traversal range, and narrative step-by-step reasoning
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-xl text-xs shadow-sm transition-colors disabled:opacity-50"
        >
          <FiRefreshCw className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
          {analyzing ? 'Running Fault Localization...' : 'Run Fault Analysis'}
        </button>
      </div>

      {/* Top 5 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Active Faults"
          value={summary ? summary.total_incidents : '---'}
          statusText="Localized Outage Incidents"
          icon={FiAlertTriangle}
          colorTheme="red"
        />
        <StatCard
          title="Span Faults"
          value={summary ? summary.span_faults : '---'}
          statusText="Span & Unknown Spans"
          icon={FiZap}
          colorTheme="amber"
        />
        <StatCard
          title="Transformer Faults"
          value={summary ? summary.transformer_faults : '---'}
          statusText="DTR Station Outages"
          icon={FiRadio}
          colorTheme="red"
        />
        <StatCard
          title="Feeder Trips"
          value={summary ? summary.feeder_faults : '---'}
          statusText="11kV Main Line Trips"
          icon={FiZap}
          colorTheme="purple"
        />
        <StatCard
          title="Impacted Households"
          value={summary ? summary.total_estimated_households.toLocaleString() : '---'}
          statusText={`${summary ? summary.total_affected_poles : 0} Affected Poles`}
          icon={FiUsers}
          colorTheme="blue"
        />
      </div>

      {/* Filter & Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-80">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search Incident ID, Feeder, Pole..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-800"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Fault Type:</span>
            <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1 rounded-lg">
              {['ALL', 'SPAN_FAULT', 'UNKNOWN_SPAN', 'TRANSFORMER_FAULT', 'FEEDER_FAULT'].map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                    filterType === type
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {type === 'ALL' ? 'All Incidents' : type.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Incident List */}
      {loading ? (
        <Loading message="Running deterministic fault localization..." />
      ) : filteredIncidents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredIncidents.map((inc) => (
            <Card key={inc.incident_id} className="p-6 space-y-4 hover:shadow-md transition-shadow border-l-4 border-l-red-500">
              {/* Incident Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-sm font-bold text-slate-900">{inc.incident_id}</span>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded text-[10px] uppercase font-semibold border ${
                      badgeThemeMap[inc.fault_type] || 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {inc.fault_type.replace('_', ' ')}
                  </span>
                </div>

                {/* Confidence Badge */}
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${getConfidenceBadge(
                      inc.confidence
                    )}`}
                    title={inc.confidence_reason}
                  >
                    <FiTarget className="w-3.5 h-3.5" />
                    {inc.confidence}% Confidence
                  </span>
                </div>
              </div>

              {/* Fault Boundary Details */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block">Feeder Code</span>
                  <span className="font-mono font-bold text-slate-900">{inc.feeder_code}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Transformer Code</span>
                  <span className="font-mono font-bold text-slate-900">{inc.transformer_code || 'N/A (Feeder Outage)'}</span>
                </div>

                {inc.fault_type === 'SPAN_FAULT' && (
                  <>
                    <div className="bg-emerald-50/70 border border-emerald-200 rounded-lg p-2">
                      <span className="text-emerald-800 block text-[10px] font-bold uppercase">Upstream Pole (Energized)</span>
                      <span className="font-mono font-bold text-emerald-700 text-xs">{inc.upstream_pole}</span>
                    </div>
                    <div className="bg-red-50/70 border border-red-200 rounded-lg p-2">
                      <span className="text-red-800 block text-[10px] font-bold uppercase">Downstream Pole (Dark)</span>
                      <span className="font-mono font-bold text-red-700 text-xs">{inc.downstream_pole}</span>
                    </div>
                  </>
                )}

                {inc.fault_type === 'UNKNOWN_SPAN' && (
                  <div className="col-span-2 bg-amber-50/70 border border-amber-200 rounded-lg p-2.5">
                    <span className="text-amber-800 block text-[10px] font-bold uppercase">Estimated Fault Area (Unknown Topology)</span>
                    <span className="font-mono font-bold text-amber-900 text-xs">{inc.estimated_area || inc.transformer_code}</span>
                  </div>
                )}
              </div>

              {/* Possible Fault Range Pill List (Gap Traversal) */}
              {inc.possible_fault_range && inc.possible_fault_range.length > 0 && (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-1 text-xs">
                  <span className="text-slate-500 font-bold uppercase text-[10px] block">
                    Possible Fault Range (Span / Gaps):
                  </span>
                  <div className="flex flex-wrap items-center gap-1 font-mono text-[11px]">
                    {inc.possible_fault_range.map((code, idx) => (
                      <React.Fragment key={code}>
                        <span className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded font-semibold">
                          {code}
                        </span>
                        {idx < inc.possible_fault_range.length - 1 && <span className="text-slate-400">→</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {/* Engineering Reason & Step-by-Step Narrative Reasoning */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px] flex items-center gap-1">
                    <FiInfo className="w-3.5 h-3.5 text-brand-600" />
                    Deterministic Diagnosis
                  </span>

                  {inc.reasoning && (
                    <button
                      onClick={() => toggleReasoning(inc.incident_id)}
                      className="text-brand-600 hover:text-brand-700 font-semibold text-[11px] flex items-center gap-1"
                    >
                      {expandedReasoning[inc.incident_id] ? 'Hide Narrative' : 'Explanation Engine'}
                      {expandedReasoning[inc.incident_id] ? <FiChevronUp /> : <FiChevronDown />}
                    </button>
                  )}
                </div>

                <p className="text-slate-600 leading-relaxed">{inc.reason}</p>

                {/* Step-by-Step Narrative Array */}
                {expandedReasoning[inc.incident_id] && inc.reasoning && (
                  <div className="mt-2 pt-2 border-t border-slate-200 space-y-1.5 bg-white p-3 rounded-lg border">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Step-by-Step Reasoning Logic:
                    </span>
                    <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-700 font-mono">
                      {inc.reasoning.map((step, idx) => (
                        <li key={idx} className="leading-snug">{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>

              {/* Affected Poles Footer */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                <div className="flex items-center gap-1.5 text-slate-600">
                  <FiCpu className="w-4 h-4 text-slate-400" />
                  <span>
                    <strong>{inc.affected_poles_count}</strong> Affected Poles ({inc.estimated_households} est. households)
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">{formatDate(inc.detected_at)}</span>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-12 text-center space-y-3">
          <FiCheckCircle className="w-12 h-12 text-emerald-500 mx-auto" />
          <h3 className="font-bold text-slate-900 text-base">No Active Fault Incidents Detected</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            All distribution feeders, transformers, and line pole sensors report healthy energized power flow across the radial network.
          </p>
        </Card>
      )}

      {/* Telemetry Sensor Anomalies Panel */}
      {anomalies.length > 0 && (
        <Card className="p-6 space-y-4 border-l-4 border-l-amber-500 bg-amber-50/30">
          <div className="flex items-center justify-between border-b border-amber-200/60 pb-3">
            <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wider flex items-center gap-2">
              <FiAlertCircle className="w-4 h-4 text-amber-600" />
              Telemetry Sensor Glitch Anomalies ({anomalies.length})
            </h3>
            <span className="text-[11px] font-semibold text-amber-800 bg-amber-100 px-2.5 py-0.5 rounded-full border border-amber-200">
              Suppressed from Fault Generator
            </span>
          </div>

          <div className="space-y-2 text-xs">
            {anomalies.map((anom, idx) => (
              <div key={idx} className="p-3 bg-white border border-amber-200 rounded-lg flex items-center justify-between text-slate-700">
                <div className="space-y-0.5">
                  <span className="font-mono font-bold text-amber-900">{anom.pole_code}</span>
                  <p className="text-slate-500 text-[11px]">{anom.reason}</p>
                </div>
                <span className="font-mono text-[11px] text-slate-400">{anom.device_id}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default FaultsPage;
