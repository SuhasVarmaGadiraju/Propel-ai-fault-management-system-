import React from 'react';
import { FiMenu, FiBell, FiSearch, FiZap } from 'react-icons/fi';

/**
 * Top Navbar Navigation Header
 */
const Navbar = ({ onToggleSidebar }) => {
  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 h-16 flex items-center justify-between px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg lg:hidden"
          aria-label="Toggle Navigation"
        >
          <FiMenu className="w-5 h-5" />
        </button>

        {/* Search Placeholder */}
        <div className="relative hidden md:block w-72">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search poles, telemetry, tickets..."
            className="w-full pl-9 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent text-slate-800 placeholder-slate-400"
            disabled
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* System Health Status Indicator */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-xs font-semibold text-emerald-700">System Online</span>
        </div>

        {/* Notification Bell Placeholder */}
        <button
          className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
          aria-label="Notifications"
        >
          <FiBell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand-600 rounded-full"></span>
        </button>

        <div className="h-6 w-px bg-slate-200"></div>

        {/* User Profile Chip */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-brand-700 text-white rounded-full flex items-center justify-center font-bold text-sm shadow-sm">
            PE
          </div>
          <div className="hidden lg:block">
            <p className="text-xs font-semibold text-slate-800 leading-tight">Product Engineer</p>
            <p className="text-[11px] text-slate-500">Propel AI Operations</p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
