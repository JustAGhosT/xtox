import React, { useState, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [autoFix, setAutoFix] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (file && file.name.endsWith('.tex')) {
      setSelectedFile(file);
      setResult(null);
    } else {
      alert('Please select a .tex file');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('auto_fix', autoFix);

      const response = await axios.post(`${API}/convert`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      setResult({
        success: false,
        errors: [error.response?.data?.detail || 'Upload failed. Please try again.'],
        warnings: []
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!result || !result.success) return;

    try {
      const response = await axios.get(`${API}/download/${result.id}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${result.filename}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF. Please try again.');
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setResult(null);
    setAutoFix(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            XToPDF
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Convert LaTeX files to PDF with intelligent error detection and auto-fix capabilities
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Upload Section */}
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">Upload LaTeX File</h2>
            
            {/* File Upload Area */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
                dragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="mb-4">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <p className="text-lg text-gray-600 mb-2">
                {selectedFile ? selectedFile.name : 'Drop your .tex file here, or click to browse'}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Maximum file size: 10MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".tex"
                onChange={handleFileInputChange}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
              >
                Choose File
              </button>
            </div>

            {/* Auto-fix Option */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoFix}
                  onChange={(e) => setAutoFix(e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700">
                    Auto-fix common LaTeX errors
                  </span>
                  <p className="text-xs text-gray-500 mt-1">
                    Automatically add missing \\documentclass, \\begin{document}, and \\end{document} if needed
                  </p>
                </div>
              </label>
            </div>

            {/* Convert Button */}
            <div className="mt-6 text-center">
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isProcessing}
                className={`px-8 py-3 rounded-lg font-medium text-lg transition-all duration-200 ${
                  !selectedFile || isProcessing
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700 shadow-lg hover:shadow-xl'
                }`}
              >
                {isProcessing ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Converting...
                  </span>
                ) : (
                  'Convert to PDF'
                )}
              </button>
            </div>
          </div>

          {/* Results Section */}
          {result && (
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">Conversion Results</h2>
              
              {result.success ? (
                <div className="text-center">
                  <div className="mb-6">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-2">
                      Conversion Successful!
                    </h3>
                    {result.auto_fix_applied && (
                      <p className="text-sm text-blue-600 mb-4">
                        ✨ Auto-fix was applied to your LaTeX file
                      </p>
                    )}
                  </div>
                  
                  <button
                    onClick={handleDownload}
                    className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium text-lg shadow-lg hover:shadow-xl mr-4"
                  >
                    Download PDF
                  </button>
                  
                  <button
                    onClick={resetForm}
                    className="bg-gray-600 text-white px-8 py-3 rounded-lg hover:bg-gray-700 transition-colors duration-200 font-medium text-lg"
                  >
                    Convert Another File
                  </button>
                </div>
              ) : (
                <div>
                  <div className="mb-6">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-2">
                      Conversion Failed
                    </h3>
                  </div>
                  
                  {result.errors && result.errors.length > 0 && (
                    <div className="mb-6">
                      <h4 className="text-lg font-medium text-red-600 mb-3">Errors:</h4>
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        {result.errors.map((error, index) => (
                          <div key={index} className="text-sm text-red-700 mb-2 font-mono">
                            {error}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {result.warnings && result.warnings.length > 0 && (
                    <div className="mb-6">
                      <h4 className="text-lg font-medium text-yellow-600 mb-3">Warnings:</h4>
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        {result.warnings.map((warning, index) => (
                          <div key={index} className="text-sm text-yellow-700 mb-2 font-mono">
                            {warning}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="text-center">
                    <p className="text-gray-600 mb-4">
                      Try enabling auto-fix or correct the errors above and upload again.
                    </p>
                    <button
                      onClick={resetForm}
                      className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;