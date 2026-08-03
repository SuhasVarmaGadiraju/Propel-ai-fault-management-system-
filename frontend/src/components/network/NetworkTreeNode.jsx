import React, { useState, useEffect } from 'react';
import {
  FiChevronRight,
  FiChevronDown,
  FiCpu,
  FiZap,
  FiRadio,
  FiAlertCircle,
  FiCheckCircle,
  FiFolder
} from 'react-icons/fi';

/**
 * Recursive collapsible Tree Node component for the Network Explorer graph visualization.
 */
const NetworkTreeNode = ({ node, type, onSelect, selectedNodeId, isSearchActive }) => {
  const [isExpanded, setIsExpanded] = useState(type === 'feeder' || type === 'transformer');
  const [searchCollapsed, setSearchCollapsed] = useState(false);

  // Reset search collapse override whenever search active status changes
  useEffect(() => {
    if (isSearchActive) {
      setSearchCollapsed(false);
    }
  }, [isSearchActive]);

  // When search query is active, automatically expand ancestor nodes; restore pre-search state when cleared
  const expanded = isSearchActive ? !searchCollapsed : isExpanded;

  const handleToggle = (e) => {
    e.stopPropagation();
    if (isSearchActive) {
      setSearchCollapsed(!searchCollapsed);
    } else {
      setIsExpanded(!isExpanded);
    }
  };

  const isSelected = Boolean(node?.id && selectedNodeId === node.id);

  // Determine icon & theme color based on node type
  let icon = <FiFolder className="w-4 h-4 text-brand-600" />;
  let badgeColor = 'bg-brand-50 text-brand-700 border-brand-200';
  let title = node?.code || node?.name || 'Unnamed Node';

  if (type === 'feeder') {
    icon = <FiRadio className="w-4 h-4 text-purple-600" />;
    badgeColor = 'bg-purple-50 text-purple-700 border-purple-200';
  } else if (type === 'transformer') {
    icon = <FiZap className="w-4 h-4 text-amber-600" />;
    badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (type === 'pole') {
    icon = <FiCpu className="w-4 h-4 text-slate-700" />;
    badgeColor = node?.topology_known
      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
      : 'bg-slate-100 text-slate-600 border-slate-200';
  }

  // Children array based on type
  const children =
    type === 'feeder'
      ? (Array.isArray(node?.transformers) ? node.transformers : [])
      : type === 'transformer'
      ? (Array.isArray(node?.root_poles) ? node.root_poles : [])
      : (Array.isArray(node?.children) ? node.children : []);

  const hasChildren = Array.isArray(children) && children.length > 0;

  return (
    <div className="select-none text-xs">
      {/* Node Row */}
      <div
        onClick={() => onSelect && onSelect(node, type)}
        className={`flex items-center justify-between py-1.5 px-2.5 rounded-lg cursor-pointer transition-colors ${
          isSelected
            ? 'bg-brand-500 text-white font-semibold shadow-xs'
            : 'hover:bg-slate-100/80 text-slate-800'
        }`}
      >
        <div className="flex items-center gap-2 overflow-hidden">
          {hasChildren ? (
            <button
              onClick={handleToggle}
              className="p-0.5 rounded hover:bg-slate-200/60"
            >
              {expanded ? (
                <FiChevronDown className="w-3.5 h-3.5" />
              ) : (
                <FiChevronRight className="w-3.5 h-3.5" />
              )}
            </button>
          ) : (
            <span className="w-3.5 inline-block"></span>
          )}

          <div className="shrink-0">{icon}</div>
          <span className="truncate font-mono">{title}</span>
        </div>

        {/* Status Badges */}
        <div className="flex items-center gap-1.5 shrink-0 ml-2">
          {type === 'pole' && (
            <>
              {node?.topology_known ? (
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  KNOWN
                </span>
              ) : (
                <span className="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                  UNKNOWN
                </span>
              )}

              {node?.device && (
                <span
                  className={`w-2 h-2 rounded-full ${
                    node?.telemetry?.energized ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'
                  }`}
                  title={node?.telemetry?.energized ? 'Powered' : 'Outage'}
                ></span>
              )}
            </>
          )}

          {hasChildren && (
            <span
              className={`px-1.5 py-0.2 rounded text-[10px] font-mono ${
                isSelected ? 'bg-brand-600 text-white' : 'bg-slate-200 text-slate-700'
              }`}
            >
              {children.length}
            </span>
          )}
        </div>
      </div>

      {/* Render Subtree Children recursively */}
      {expanded && hasChildren && (
        <div className="pl-4 ml-2 border-l border-slate-200 space-y-0.5 mt-0.5">
          {children.map((childNode) => {
            const nextType =
              type === 'feeder' ? 'transformer' : 'pole';
            return (
              <NetworkTreeNode
                key={childNode?.id || childNode?.code}
                node={childNode}
                type={nextType}
                onSelect={onSelect}
                selectedNodeId={selectedNodeId}
                isSearchActive={isSearchActive}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default NetworkTreeNode;
