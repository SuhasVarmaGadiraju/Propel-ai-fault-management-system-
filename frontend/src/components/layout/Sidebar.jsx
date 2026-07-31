import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  FiGrid,
  FiZap,
  FiAlertTriangle,
  FiClipboard,
  FiBarChart2,
  FiSettings,
  FiX,
  FiCpu,
  FiTerminal,
  FiGitBranch
} from 'react-icons/fi';

const navItems = [
  { name: 'Dashboard', path: '/', icon: FiGrid },
  { name: 'Pole Registry', path: '/poles', icon: FiCpu },
  { name: 'Network Explorer', path: '/network-explorer', icon: FiGitBranch, badge: 'Graph' },
  { name: 'Telemetry', path: '/telemetry', icon: FiZap, badge: 'Live' },
  { name: 'Telemetry Tester', path: '/telemetry-tester', icon: FiTerminal, badge: 'Dev' },
  { name: 'Fault Detection', path: '/faults', icon: FiAlertTriangle, badge: '3' },
  { name: 'Repair Tickets', path: '/tickets', icon: FiClipboard },
  { name: 'Analytics', path: '/analytics', icon: FiBarChart2 },
  { name: 'System Settings', path: '/settings', icon: FiSettings },
];

/**
 * Enterprise Sidebar Navigation Component
 */
const Sidebar = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
        ></div>
      )}

      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-slate-900 text-white border-r border-slate-800 transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-brand-600 rounded-lg text-white">
              <FiCpu className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-wide text-white leading-none">PROPEL AI</h1>
              <span className="text-[10px] text-brand-300 font-medium tracking-wider uppercase">Fault System</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg lg:hidden"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <div className="px-3 py-6 space-y-1">
          <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Navigation Menu
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 text-slate-400 group-hover:text-white" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 text-[10px] font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30 rounded-full">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Footer Info Box */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800 bg-slate-950/50">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Environment</span>
            <span className="font-mono text-emerald-400">Production</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
