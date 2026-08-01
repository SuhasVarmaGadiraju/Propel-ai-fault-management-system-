import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Dashboard from '../pages/Dashboard';
import PoleRegistry from '../pages/PoleRegistry';
import NetworkExplorer from '../pages/NetworkExplorer';
import TelemetryPage from '../pages/Telemetry';
import TelemetryTester from '../pages/TelemetryTester';
import FaultsPage from '../pages/FaultsPage';
import TicketsPage from '../pages/TicketsPage';
import FaultSimulator from '../pages/FaultSimulator';
import AnalyticsPage from '../pages/AnalyticsPage';
import SystemSettings from '../pages/SystemSettings';
import NotFound from '../pages/NotFound';

/**
 * Centralized Application Routes Component
 */
const AppRoutes = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/poles" element={<PoleRegistry />} />
        <Route path="/network-explorer" element={<NetworkExplorer />} />
        <Route path="/telemetry" element={<TelemetryPage />} />
        <Route path="/telemetry-tester" element={<TelemetryTester />} />
        <Route path="/faults" element={<FaultsPage />} />
        <Route path="/tickets" element={<TicketsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/simulator" element={<FaultSimulator />} />
        <Route path="/settings" element={<SystemSettings />} />
        {/* Fallback 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </MainLayout>
  );
};

export default AppRoutes;
