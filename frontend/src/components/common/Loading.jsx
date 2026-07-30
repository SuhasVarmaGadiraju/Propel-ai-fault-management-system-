import React from 'react';

/**
 * Reusable Loading Spinner Component
 */
const Loading = ({ message = 'Loading application resources...' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] w-full p-6 text-slate-500">
      <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
      <p className="mt-4 text-sm font-medium">{message}</p>
    </div>
  );
};

export default Loading;
