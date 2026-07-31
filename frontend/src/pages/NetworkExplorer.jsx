import React, { useEffect, useState } from 'react';
import {
  FiGitBranch,
  FiRefreshCw,
  FiSearch,
  FiRadio,
  FiZap,
  FiCpu,
  FiLayers,
  FiCheckCircle,
  FiAlertTriangle,
  FiActivity,
  FiMapPin,
  FiInfo
} from 'react-icons/fi';
import apiClient from '../services/api';
import Card from '../components/ui/Card';
import StatCard from '../components/dashboard/StatCard';
import Loading from '../components/common/Loading';
import NetworkTreeNode from '../components/network/NetworkTreeNode';

/**
 * Developer Network Explorer Page for interactive graph tree navigation and node inspection.
 */
const NetworkExplorer = () => {
  const [stats, setStats] = useState(null);
  const [treeData, setTreeData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);

  // Inspector state
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [poleDetail, setPoleDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Search query
  const [searchQuery, setSearchQuery] = useState('');

  const fetchGraphData = async () => {
    setLoading(true);
    try {
      const [statsRes, treeRes] = await Promise.all([
        apiClient.get('/network/statistics'),
        apiClient.get('/network/tree')
      ]);
      setStats(statsRes);
      setTreeData(treeRes.feeders || []);
    } catch (err) {
      console.error('Failed to load network graph data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  const handleRebuildGraph = async () => {
    setRebuilding(true);
    try {
      await apiClient.post('/network/rebuild');
      await fetchGraphData();
    } catch (err) {
      console.error('Failed to rebuild graph cache:', err);
    } finally {
      setRebuilding(false);
    }
  };

  const handleSelectNode = async (node, type) => {
    setSelectedNode(node);
    setSelectedType(type);
    setPoleDetail(null);

    if (type === 'pole') {
      setLoadingDetail(true);
      try {
        const detail = await apiClient.get(`/network/pole/${node.code}`);
        setPoleDetail(detail);
      } catch (err) {
        console.error('Failed to load pole node detail:', err);
      } finally {
        setLoadingDetail(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FiGitBranch className="w-6 h-6 text-brand-600" />
            In-Memory Network Graph Explorer
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Hierarchical feeder tree topology, parent-child graph links, and real-time telemetry state
          </p>
        </div>

        <button
          onClick={handleRebuildGraph}
          disabled={rebuilding}
          className="inline-flex items-center gap-2 px-3.5 py-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl text-xs shadow-sm transition-colors disabled:opacity-50"
        >
          <FiRefreshCw className={`w-3.5 h-3.5 ${rebuilding ? 'animate-spin' : ''}`} />
          {rebuilding ? 'Rebuilding Graph Cache...' : 'Rebuild Graph Cache'}
        </button>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Feeders"
          value={stats ? stats.total_feeders : '---'}
          statusText="Trunk Circuit Lines"
          icon={FiRadio}
          colorTheme="purple"
        />
        <StatCard
          title="Transformers"
          value={stats ? stats.total_transformers : '---'}
          statusText="DTR Substation Units"
          icon={FiZap}
          colorTheme="amber"
        />
        <StatCard
          title="Total Poles"
          value={stats ? stats.total_poles.toLocaleString() : '---'}
          statusText="In-Memory Graph Nodes"
          icon={FiCpu}
          colorTheme="blue"
        />
        <StatCard
          title="Topology Known"
          value={stats ? `${stats.known_topology_percent}%` : '---'}
          statusText={`${stats ? stats.known_topology_count : 0} Poles Linked`}
          icon={FiCheckCircle}
          colorTheme="emerald"
        />
        <StatCard
          title="Max Tree Depth"
          value={stats ? `${stats.max_tree_depth} Hops` : '---'}
          statusText={`Branch Factor: ${stats ? stats.avg_branching_factor : 0}`}
          icon={FiLayers}
          colorTheme="blue"
        />
      </div>

      {/* Main Grid: Tree View & Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Tree View Navigator */}
        <Card className="lg:col-span-1 p-5 space-y-4 flex flex-col h-[650px]">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <FiGitBranch className="w-4 h-4 text-brand-600" />
              Network Tree Hierarchy
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              {stats ? `${stats.total_poles} Nodes` : ''}
            </span>
          </div>

          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search Feeder / Transformer / Pole..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto pr-1 space-y-2 border border-slate-100 rounded-xl p-3 bg-slate-50/50">
            {loading ? (
              <Loading message="Constructing network tree..." />
            ) : treeData.length > 0 ? (
              treeData.map((feederNode) => (
                <NetworkTreeNode
                  key={feederNode.id}
                  node={feederNode}
                  type="feeder"
                  onSelect={handleSelectNode}
                  selectedNodeId={selectedNode?.id}
                />
              ))
            ) : (
              <div className="text-center py-10 text-slate-400 text-xs italic">
                No network tree nodes loaded.
              </div>
            )}
          </div>
        </Card>

        {/* Right Panel: Selected Node Inspector */}
        <Card className="lg:col-span-2 p-6 space-y-6 flex flex-col h-[650px] overflow-y-auto">
          {selectedNode ? (
            <div className="space-y-6">
              {/* Header Badge */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-brand-50 text-brand-600 rounded-xl">
                    {selectedType === 'feeder' && <FiRadio className="w-6 h-6" />}
                    {selectedType === 'transformer' && <FiZap className="w-6 h-6" />}
                    {selectedType === 'pole' && <FiCpu className="w-6 h-6" />}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 font-mono">
                      {selectedNode.code || selectedNode.name}
                    </h2>
                    <span className="text-xs text-slate-400 uppercase font-semibold tracking-wider">
                      {selectedType} Node Inspector
                    </span>
                  </div>
                </div>

                {selectedType === 'pole' && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
                      selectedNode.topology_known
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}
                  >
                    {selectedNode.topology_known ? 'Topology Known' : 'Unknown Topology'}
                  </span>
                )}
              </div>

              {/* Node General Metadata */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 text-xs">
                <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <FiInfo className="w-3.5 h-3.5 text-brand-600" />
                  Structural Metadata
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-slate-700">
                  <div>
                    <span className="text-slate-400 block">Node UUID</span>
                    <span className="font-mono font-semibold text-slate-900 truncate block">{selectedNode.id}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Coordinates</span>
                    <span className="font-mono text-slate-900">
                      {selectedNode.latitude?.toFixed(4)}, {selectedNode.longitude?.toFixed(4)}
                    </span>
                  </div>
                  {selectedType === 'pole' && (
                    <>
                      <div>
                        <span className="text-slate-400 block">Sequence on Line</span>
                        <span className="font-mono font-bold text-slate-900">
                          {selectedNode.seq_on_line ? `#${selectedNode.seq_on_line}` : 'Unassigned'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Parent Pole</span>
                        <span className="font-mono font-bold text-brand-700">
                          {poleDetail?.parent_code || selectedNode.parent_code || 'Root Pole'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Direct Children</span>
                        <span className="font-mono text-slate-900 font-semibold">
                          {poleDetail?.children_count ?? selectedNode.children_count ?? 0} Poles
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Path to Transformer Root (for Pole nodes) */}
              {selectedType === 'pole' && poleDetail?.path_to_root && (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 text-xs">
                  <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                    Path to Root Transformer
                  </h3>
                  <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
                    {poleDetail.path_to_root.map((code, idx) => (
                      <React.Fragment key={code}>
                        <span
                          className={`px-2 py-0.5 rounded font-semibold ${
                            code === selectedNode.code
                              ? 'bg-brand-600 text-white'
                              : 'bg-white text-slate-700 border border-slate-200'
                          }`}
                        >
                          {code}
                        </span>
                        {idx < poleDetail.path_to_root.length - 1 && (
                          <span className="text-slate-400 font-bold">→</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {/* Hardware Device & Telemetry Operational State */}
              {selectedType === 'pole' && (
                <div className="bg-slate-900 text-slate-200 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
                  <h3 className="text-slate-400 uppercase tracking-wider text-[11px] font-bold flex items-center gap-1.5">
                    <FiActivity className="w-4 h-4 text-emerald-400" />
                    Attached Device & Live Telemetry State
                  </h3>

                  {selectedNode.device ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      <div>
                        <span className="text-slate-400 block">Device ID</span>
                        <span className="font-mono font-bold text-emerald-400">{selectedNode.device.device_id}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Energized State</span>
                        <span className={`font-bold ${selectedNode.telemetry?.energized ? 'text-emerald-400' : 'text-red-400 animate-pulse'}`}>
                          {selectedNode.telemetry?.energized ? 'POWERED (True)' : 'OUTAGE (False)'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Last Event</span>
                        <span className="font-mono text-slate-200">{selectedNode.telemetry?.last_event || '---'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Battery Voltage</span>
                        <span className="font-mono text-slate-200">{selectedNode.telemetry?.battery_mv ? `${selectedNode.telemetry.battery_mv} mV` : '---'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Signal RSSI</span>
                        <span className="font-mono text-slate-200">{selectedNode.telemetry?.last_rssi ? `${selectedNode.telemetry.last_rssi} dBm` : '---'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Firmware</span>
                        <span className="font-mono text-slate-200">{selectedNode.device.firmware_version || '1.0.0'}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No IoT telemetry sensor attached to this pole.</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-3 text-slate-400">
              <FiGitBranch className="w-12 h-12 text-slate-300 stroke-1" />
              <div>
                <h3 className="font-bold text-slate-700 text-sm">No Node Selected</h3>
                <p className="text-xs max-w-xs text-slate-500 mt-1">
                  Click any Feeder, Transformer, or Pole node in the hierarchy tree to inspect its parent/child graph pointers and telemetry status.
                </p>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default NetworkExplorer;
