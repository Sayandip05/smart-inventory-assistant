/**
 * Vendor DataEntry Page — Excel delivery upload portal.
 *
 * Vendors can:
 * - Download a blank Excel template
 * - Upload delivery manifests (.xlsx/.xls)
 * - View their upload history
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { Upload, Download, FileSpreadsheet, History, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

export default function DataEntry() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [file, setFile] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch locations and upload history on mount
  useEffect(() => {
    fetchLocations();
    fetchUploadHistory();
  }, []);

  const fetchLocations = async () => {
    try {
      const response = await api.get('/inventory/locations');
      setLocations(response.data.data || []);
    } catch (err) {
      console.error('Failed to fetch locations:', err);
    }
  };

  const fetchUploadHistory = async () => {
    try {
      const response = await api.get('/vendor/my-uploads');
      setUploads(response.data.data || []);
    } catch (err) {
      console.error('Failed to fetch upload history:', err);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/vendor/template', {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'delivery_template.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download template. Please try again.');
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
        setError('Only .xlsx or .xls files are accepted');
        setFile(null);
        return;
      }
      if (selectedFile.size > 5 * 1024 * 1024) {
        setError('File size must be under 5MB');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!selectedLocation) {
      setError('Please select a location');
      return;
    }
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post(`/vendor/upload-delivery?location_id=${selectedLocation}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setSuccess('Delivery uploaded successfully!');
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById('file-upload');
      if (fileInput) fileInput.value = '';
      
      // Refresh upload history
      fetchUploadHistory();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Upload failed. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <FileSpreadsheet className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-semibold text-white">Vendor Portal</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-slate-400 text-sm">Welcome, {user?.username}</span>
              <button
                onClick={logout}
                className="text-sm text-slate-400 hover:text-white transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-500" />
              Upload Delivery
            </h2>

            {/* Download Template */}
            <div className="mb-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="text-slate-400 text-sm mb-3">
                Download the template file and fill in your delivery data.
              </p>
              <button
                onClick={handleDownloadTemplate}
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium rounded-lg transition-colors border border-slate-600"
              >
                <Download className="w-4 h-4" />
                Download Template
              </button>
            </div>

            {/* Upload Form */}
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Select Location
                </label>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Choose a location...</option>
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name} ({loc.type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Upload Excel File
                </label>
                <div className="relative">
                  <input
                    id="file-upload"
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="file-upload"
                    className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-slate-700 rounded-lg cursor-pointer hover:border-slate-600 hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="text-center">
                      <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                      <p className="text-sm text-slate-400">
                        {file ? file.name : 'Click to select file'}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        .xlsx or .xls up to 5MB
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg px-4 py-3">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {success && (
                <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-400 text-sm rounded-lg px-4 py-3">
                  <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{success}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !file || !selectedLocation}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload Delivery
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Upload History */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <History className="w-5 h-5 text-blue-500" />
              Upload History
            </h2>

            {uploads.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No uploads yet</p>
                <p className="text-sm mt-1">Your delivery uploads will appear here</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {uploads.map((upload, index) => (
                  <div
                    key={index}
                    className="p-4 bg-slate-800/50 rounded-lg border border-slate-700"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-white font-medium text-sm">
                          {upload.filename || 'Unknown file'}
                        </p>
                        <p className="text-slate-400 text-xs mt-1">
                          Location: {upload.location_name || `ID: ${upload.location_id}`}
                        </p>
                        <p className="text-slate-500 text-xs mt-1">
                          {formatDate(upload.created_at)}
                        </p>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${
                        upload.status === 'success' 
                          ? 'bg-green-500/10 text-green-400' 
                          : upload.status === 'partial'
                          ? 'bg-yellow-500/10 text-yellow-400'
                          : 'bg-red-500/10 text-red-400'
                      }`}>
                        {upload.status || 'completed'}
                      </div>
                    </div>
                    {upload.rows_processed && (
                      <p className="text-slate-400 text-xs mt-2">
                        {upload.rows_processed} rows processed
                        {upload.rows_failed > 0 && (
                          <span className="text-red-400">, {upload.rows_failed} failed</span>
                        )}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
