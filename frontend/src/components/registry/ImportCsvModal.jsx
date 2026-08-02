import React, { useState } from 'react';
import { FiX, FiUploadCloud, FiCheckCircle, FiAlertTriangle, FiFileText } from 'react-icons/fi';
import apiClient from '../../services/api';

/**
 * Modal dialog component for importing electricity department CSV pole registry files.
 */
const ImportCsvModal = ({ isOpen, onClose, onImportSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [importSummary, setImportSummary] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setErrorMsg(null);
      } else {
        setErrorMsg('Please select a valid .csv file.');
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setErrorMsg(null);
    setImportSummary(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const summary = await apiClient.post('/pole-registry/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImportSummary(summary || null);
      if (onImportSuccess) {
        onImportSuccess();
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload and import CSV file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setImportSummary(null);
    setErrorMsg(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <FiUploadCloud className="w-5 h-5 text-brand-600" />
            Import Official Pole Registry CSV
          </h3>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 rounded-lg"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {!importSummary ? (
            <>
              {/* Dropzone */}
              <div className="border-2 border-dashed border-slate-200 hover:border-brand-500 rounded-xl p-8 text-center transition-colors bg-slate-50/50">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="hidden"
                  id="csv-upload-input"
                />
                <label htmlFor="csv-upload-input" className="cursor-pointer block">
                  <FiFileText className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm font-semibold text-slate-700">
                    {selectedFile ? selectedFile.name : 'Click to choose a CSV file'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Supports official department format (pole_id, lat, lon, feeder_id, dt_id...)
                  </p>
                </label>
              </div>

              {errorMsg && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                  <FiAlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}
            </>
          ) : (
            /* Result Summary */
            <div className="space-y-4">
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3">
                <FiCheckCircle className="w-6 h-6 text-emerald-600 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-emerald-900">Import Completed</h4>
                  <p className="text-xs text-emerald-700 mt-0.5">
                    Processed {importSummary?.total_rows ?? 0} total CSV records.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="text-xs text-slate-500 block">Inserted</span>
                  <span className="text-lg font-bold text-emerald-600">{importSummary?.imported_count ?? 0}</span>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="text-xs text-slate-500 block">Updated</span>
                  <span className="text-lg font-bold text-brand-600">{importSummary?.updated_count ?? 0}</span>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="text-xs text-slate-500 block">Skipped</span>
                  <span className="text-lg font-bold text-amber-600">{importSummary?.skipped_count ?? 0}</span>
                </div>
              </div>

              {Array.isArray(importSummary?.errors) && importSummary.errors.length > 0 && (
                <div className="max-h-40 overflow-y-auto p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                  <p className="font-semibold text-slate-700 mb-1">Validation Errors ({importSummary.errors.length}):</p>
                  {importSummary.errors.map((err, i) => (
                    <p key={i} className="text-red-600 font-mono">
                      Row {err?.row} [{err?.pole_id}]: {err?.error}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
          {!importSummary ? (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow transition-colors flex items-center gap-2"
              >
                {isUploading ? 'Importing...' : 'Start Import'}
              </button>
            </>
          ) : (
            <button
              onClick={() => {
                handleReset();
                onClose();
              }}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportCsvModal;
