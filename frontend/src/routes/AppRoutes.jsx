import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Dashboard from '../pages/Dashboard';
import PoleRegistry from '../pages/PoleRegistry';
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
        {/* Fallback 404 Route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </MainLayout>
  );
};

export default AppRoutes;
