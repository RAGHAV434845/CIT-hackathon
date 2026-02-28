import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getAnalysis } from '../services/api';

export default function AnalysisView() {
  const { repoId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    getAnalysis(repoId).then(res => setAnalysis(res.data.analysis)).catch(() => {});
  }, [repoId]);

  if (!analysis) return <div className="min-h-screen bg-gray-50"><Navbar /><p className="text-center pt-20 text-gray-400">Loading analysis...</p></div>;

  const tabs = ['overview', 'components', 'endpoints', 'entry_points', 'dependencies'];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link to={`/repo/${repoId}`} className="text-sm text-primary-600 hover:underline mb-4 inline-block">← Back</Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Analysis Results</h1>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
          {tabs.map(t => (
            <button key={t} onClick={() => setActiveTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium capitalize ${activeTab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}>
              {t.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Overview */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-semibold mb-4">Project Overview</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div><span className="text-gray-500 text-sm">Framework:</span><p className="font-medium">{analysis.framework?.join(', ')}</p></div>
                <div><span className="text-gray-500 text-sm">Architecture:</span><p className="font-medium">{analysis.architecture_type}</p></div>
                <div><span className="text-gray-500 text-sm">Total Files:</span><p className="font-medium">{analysis.total_files}</p></div>
                <div><span className="text-gray-500 text-sm">Total Lines:</span><p className="font-medium">{analysis.total_lines?.toLocaleString()}</p></div>
              </div>
            </div>
            {analysis.tech_stack?.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-semibold mb-3">Tech Stack</h3>
                <div className="flex flex-wrap gap-2">
                  {analysis.tech_stack.map((t, i) => <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">{t}</span>)}
                </div>
              </div>
            )}
            {analysis.database_usage?.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-semibold mb-3">Database Usage</h3>
                {analysis.database_usage.map((db, i) => (
                  <div key={i} className="flex items-center gap-2 py-1">
                    <span className="font-medium text-sm">{db.database}</span>
                    <span className="text-xs text-gray-400">in {db.file}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Components */}
        {activeTab === 'components' && (
          <div className="space-y-4">
            {Object.entries(analysis.components || {}).filter(([k]) => k !== 'other').map(([cat, files]) => (
              <div key={cat} className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-semibold capitalize mb-3">{cat} ({files.length})</h3>
                <div className="space-y-1">
                  {files.slice(0, 20).map((f, i) => (
                    <p key={i} className="text-sm text-gray-600 font-mono">{f}</p>
                  ))}
                  {files.length > 20 && <p className="text-xs text-gray-400">...and {files.length - 20} more</p>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Endpoints */}
        {activeTab === 'endpoints' && (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Method</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Route</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">File</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">Framework</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(analysis.api_endpoints || []).map((ep, i) => (
                  <tr key={i}>
                    <td className="px-4 py-2"><span className={`text-xs font-bold px-2 py-0.5 rounded ${ep.method === 'GET' ? 'bg-green-100 text-green-700' : ep.method === 'POST' ? 'bg-blue-100 text-blue-700' : ep.method === 'DELETE' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{ep.method}</span></td>
                    <td className="px-4 py-2 text-sm font-mono">{ep.route}</td>
                    <td className="px-4 py-2 text-sm text-gray-500">{ep.file}</td>
                    <td className="px-4 py-2 text-sm text-gray-500">{ep.framework}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!analysis.api_endpoints || analysis.api_endpoints.length === 0) && (
              <p className="p-6 text-center text-gray-400">No API endpoints detected</p>
            )}
          </div>
        )}

        {/* Entry Points */}
        {activeTab === 'entry_points' && (
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="font-semibold mb-4">Entry Points</h3>
            {(analysis.entry_points || []).map((ep, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
                <span className="text-sm font-mono text-primary-600">{ep.file}</span>
                <span className="text-xs text-gray-400">{ep.reason}</span>
              </div>
            ))}
            {(!analysis.entry_points || analysis.entry_points.length === 0) && (
              <p className="text-gray-400 text-sm">No entry points detected</p>
            )}
          </div>
        )}

        {/* Dependencies */}
        {activeTab === 'dependencies' && (
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="font-semibold mb-4">Import Dependencies (Top Files)</h3>
            <div className="space-y-3">
              {Object.entries(analysis.dependency_graph || {}).slice(0, 20).map(([file, deps]) => (
                <div key={file} className="border-b border-gray-100 pb-3">
                  <p className="text-sm font-mono font-medium text-gray-900">{file}</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {deps.slice(0, 10).map((d, i) => (
                      <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{d}</span>
                    ))}
                    {deps.length > 10 && <span className="text-xs text-gray-400">+{deps.length - 10} more</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
