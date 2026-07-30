import React from 'react';
import Card from '../ui/Card';

/**
 * Reusable Metric Stat Card Component
 */
const StatCard = ({ title, value, statusText, icon: Icon, colorTheme = 'blue' }) => {
  const themeStyles = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    red: 'bg-red-50 text-red-600 border-red-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="p-6 flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            {title}
          </p>
          <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
            {value}
          </h3>
          {statusText && (
            <p className="mt-2 text-xs font-medium text-slate-500 flex items-center gap-1">
              {statusText}
            </p>
          )}
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl border ${themeStyles[colorTheme] || themeStyles.blue}`}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </Card>
  );
};

export default StatCard;
