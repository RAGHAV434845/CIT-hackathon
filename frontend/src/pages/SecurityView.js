import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getSecurityScan, resolveSecurityIssues } from '../services/api';
import toast from 'react-hot-toast';

export default function SecurityView() {
  const { repoId } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadScan(); }, [repoId]);

  const loadScan = async () => {
    try {
      const res = await getSecurityScan(repoId);
      setScan(res.data);
    } catch (err) {
      toast.error('Failed to load security scan');
    }
    setLoading(false);
  };

  const handleAction = async (action, indices) => {
    try {
      await resolveSecurityIssues(repoId, action, indices);
      toast.success(`Action "${action}" applied`);
      loadScan();
    } catch (err) {
      toast.error('Action failed');
    }
  };

  const severityColor = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-blue-100 text-blue-800 border-blue-200',
  };

  if (loading) return <div className="min-h-screen bg-gray-50"><Navbar /><p className="text-center pt-20 text-gray-400">Scanning...</p></div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <Link to={`/repo/${repoId}`} className="text-sm text-primary-600 hover:underline mb-4 inline-block">← Back</Link>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Security Scan</h1>
            <p className="text-sm text-gray-500">{scan?.total_issues || 0} issues found</p>
          </div>
          {scan?.issues?.length > 0 && (
            <div className="flex gap-2">
              <button onClick={() => handleAction('auto_remove')}
                className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700">
                🗑 Auto Remove All
              </button>
              <button onClick={() => handleAction('mask')}
                className="bg-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-yellow-700">
                🔒 Mask All
              </button>
            </div>
          )}
        </div>

        {(!scan?.issues || scan.issues.length === 0) ? (
          <div className="bg-white rounded-xl p-12 border border-gray-200 text-center">
            <div className="text-5xl mb-4">✅</div>
            <p className="text-lg font-medium text-gray-900">No security issues detected!</p>
            <p className="text-sm text-gray-400 mt-1">Your code appears clean.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {scan.issues.map((issue, i) => (
              <div key={i} className={`bg-white rounded-xl p-4 border ${issue.status === 'removed' ? 'opacity-50' : ''}`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${severityColor[issue.severity] || severityColor.low}`}>
                        {issue.severity}
                      </span>
                      <span className="font-medium text-sm">{issue.type}</span>
                      {issue.status !== 'detected' && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                          {issue.status}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">
                      <span className="font-mono">{issue.file}</span> : line {issue.line}
                    </p>
                    <p className="text-xs font-mono mt-1 text-gray-400 bg-gray-50 px-2 py-1 rounded">
                      {issue.snippet}
                    </p>
                  </div>
                  {issue.status === 'detected' && (
                    <div className="flex gap-1 ml-4">
                      <button onClick={() => handleAction('ignore', [i])}
                        className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1">
                        Ignore
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
