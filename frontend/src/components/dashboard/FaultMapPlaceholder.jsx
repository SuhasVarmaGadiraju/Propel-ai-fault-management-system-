import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { FiMap, FiNavigation, FiZap } from 'react-icons/fi';

/**
 * Geographical Fault Map Visualization Placeholder Component
 */
const FaultMapPlaceholder = () => {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center gap-2">
          <FiMap className="w-5 h-5 text-brand-600" />
          <CardTitle>Distribution Grid Map</CardTitle>
        </div>
        <span className="text-xs text-slate-500 font-medium">GIS Network Topology</span>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col items-center justify-center min-h-[260px] bg-slate-900 text-white rounded-b-xl relative overflow-hidden p-6">
        {/* Grid lines background effect */}
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(#3b82f6 1px, transparent 1px)`,
            backgroundSize: '24px 24px',
          }}
        ></div>

        {/* Dummy Grid Node Connections */}
        <div className="relative z-10 w-full max-w-xs flex flex-col items-center gap-6">
          <div className="flex items-center gap-12">
            <div className="flex flex-col items-center">
              <div className="w-10 h-10 bg-emerald-500/20 border-2 border-emerald-500 rounded-full flex items-center justify-center text-emerald-400 font-bold text-xs shadow-lg shadow-emerald-500/20">
                P-01
              </div>
              <span className="text-[10px] text-slate-400 mt-1">Feeder A</span>
            </div>

            <div className="h-0.5 w-16 bg-gradient-to-r from-emerald-500 to-amber-500"></div>

            <div className="flex flex-col items-center">
              <div className="w-10 h-10 bg-amber-500/20 border-2 border-amber-500 rounded-full flex items-center justify-center text-amber-400 font-bold text-xs shadow-lg shadow-amber-500/20">
                P-02
              </div>
              <span className="text-[10px] text-slate-400 mt-1">Warning</span>
            </div>
          </div>

          <div className="h-10 w-0.5 bg-gradient-to-b from-amber-500 to-red-500"></div>

          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-red-500/20 border-2 border-red-500 rounded-full flex items-center justify-center text-red-400 font-bold text-xs shadow-xl shadow-red-500/30 animate-pulse">
              <FiZap className="w-5 h-5 text-red-400" />
            </div>
            <span className="text-xs font-semibold text-red-400 mt-1">Fault Detected (Pole-103)</span>
          </div>
        </div>

        <p className="mt-6 text-xs text-slate-400 relative z-10 text-center">
          Interactive GIS Map integration placeholder. Leaflet/Mapbox maps will be rendered here.
        </p>
      </CardContent>
    </Card>
  );
};

export default FaultMapPlaceholder;
