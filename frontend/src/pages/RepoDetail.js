import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getRepo, startAnalysis, deleteRepo } from '../services/api';
import toast from 'react-hot-toast';

export default function RepoDetail() {
  const { repoId } = useParams();
  const navigate = useNavigate();
  const [repo, setRepo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadRepo();
  }, [repoId]);

  const loadRepo = async () => {
    try {
      const res = await getRepo(repoId);
      setRepo(res.data);
    } catch {
      toast.error('Failed to load repository');
    }
    setLoading(false);
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await startAnalysis(repoId);
      setRepo({ ...repo, status: 'completed', analysis_result: res.data.analysis });
      toast.success('Analysis complete!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Analysis failed');
    }
    setAnalyzing(false);
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this repository?')) return;
    try {
      await deleteRepo(repoId);
      toast.success('Repository deleted');
      navigate('/dashboard');
    } catch {
      toast.error('Delete failed');
    }
  };

  if (loading) return <div className="min-h-screen bg-gray-50"><Navbar /><div className="flex items-center justify-center pt-20"><p className="text-gray-400">Loading...</p></div></div>;
  if (!repo) return <div className="min-h-screen bg-gray-50"><Navbar /><div className="flex items-center justify-center pt-20"><p className="text-gray-400">Repository not found</p></div></div>;

  const hasAnalysis = repo.status === 'completed' && repo.analysis_result;
  const analysis = repo.analysis_result || {};

  const actions = [
    { label: 'Analysis Results', path: `/repo/${repoId}/analysis`, icon: '🔍', enabled: hasAnalysis },
    { label: 'Security Scan', path: `/repo/${repoId}/security`, icon: '🛡️', enabled: true },
    { label: 'Documentation', path: `/repo/${repoId}/docs`, icon: '📄', enabled: hasAnalysis },
    { label: 'Diagrams', path: `/repo/${repoId}/diagrams`, icon: '📊', enabled: hasAnalysis },
    { label: 'AI Chat', path: `/repo/${repoId}/chat`, icon: '🤖', enabled: hasAnalysis },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <Link to="/dashboard" className="text-sm text-primary-600 hover:underline mb-2 inline-block">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">{repo.name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              {repo.source === 'github' ? `🔗 ${repo.github_url}` : '📦 Uploaded ZIP'}
            </p>
          </div>
          <div className="flex gap-2">
            {!hasAnalysis && (
              <button onClick={handleAnalyze} disabled={analyzing}
                className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
                {analyzing ? '⏳ Analyzing...' : '▶ Run Analysis'}
              </button>
            )}
            <button onClick={handleDelete}
              className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-100">
              Delete
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        {hasAnalysis && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
            <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
              <p className="text-xs text-gray-500">Framework</p>
              <p className="font-semibold text-sm">{analysis.framework?.join(', ') || 'Unknown'}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
              <p className="text-xs text-gray-500">Architecture</p>
              <p className="font-semibold text-sm">{analysis.architecture_type || 'Unknown'}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
              <p className="text-xs text-gray-500">Files</p>
              <p className="font-semibold text-sm">{analysis.total_files || 0}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
              <p className="text-xs text-gray-500">Lines</p>
              <p className="font-semibold text-sm">{(analysis.total_lines || 0).toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
              <p className="text-xs text-gray-500">Endpoints</p>
              <p className="font-semibold text-sm">{analysis.api_endpoints?.length || 0}</p>
            </div>
          </div>
        )}

        {/* Action Cards */}
        <div className="grid md:grid-cols-3 gap-4">
          {actions.map((action, i) => (
            <div key={i} className={`bg-white rounded-xl p-5 border border-gray-200 ${action.enabled ? 'hover:shadow-md cursor-pointer' : 'opacity-50'}`}>
              {action.enabled ? (
                <Link to={action.path} className="block">
                  <div className="text-3xl mb-3">{action.icon}</div>
                  <p className="font-semibold text-gray-900">{action.label}</p>
                  <p className="text-xs text-gray-400 mt-1">Click to view →</p>
                </Link>
              ) : (
                <div>
                  <div className="text-3xl mb-3">{action.icon}</div>
                  <p className="font-semibold text-gray-900">{action.label}</p>
                  <p className="text-xs text-gray-400 mt-1">Run analysis first</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Tech Stack */}
        {hasAnalysis && analysis.tech_stack?.length > 0 && (
          <div className="bg-white rounded-xl p-6 border border-gray-200 mt-6">
            <h3 className="font-semibold text-gray-900 mb-3">Tech Stack</h3>
            <div className="flex flex-wrap gap-2">
              {analysis.tech_stack.map((tech, i) => (
                <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                  {tech}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Languages */}
        {hasAnalysis && analysis.languages && (
          <div className="bg-white rounded-xl p-6 border border-gray-200 mt-4">
            <h3 className="font-semibold text-gray-900 mb-3">Languages</h3>
            <div className="space-y-2">
              {Object.entries(analysis.languages)
                .sort(([, a], [, b]) => b - a)
                .map(([lang, lines]) => {
                  const total = Object.values(analysis.languages).reduce((a, b) => a + b, 0);
                  const pct = ((lines / total) * 100).toFixed(1);
                  return (
                    <div key={lang} className="flex items-center gap-3">
                      <span className="text-sm font-medium w-24">{lang}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div className="bg-primary-500 rounded-full h-2" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-xs text-gray-500 w-16 text-right">{pct}%</span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
