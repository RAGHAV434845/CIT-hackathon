import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { listRepos, createRepoFromGithub, uploadRepoZip, getDashboardStats, searchRepos, addCollaborator, getMyProjects, submitProject } from '../services/api';
import toast from 'react-hot-toast';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

export default function Dashboard() {
  const { profile } = useAuth();
  const [repos, setRepos] = useState([]);
  const [stats, setStats] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [tab, setTab] = useState('github');
  const [githubUrl, setGithubUrl] = useState('');
  const [repoName, setRepoName] = useState('');
  const [zipFile, setZipFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [collabModal, setCollabModal] = useState(null); // repo id for adding collaborator
  const [collabEmail, setCollabEmail] = useState('');
  const [myProjects, setMyProjects] = useState([]);
  const [submitModal, setSubmitModal] = useState(null); // project id for submitting
  const [submitUrl, setSubmitUrl] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [repoRes, statsRes] = await Promise.all([listRepos(), getDashboardStats()]);
      setRepos(repoRes.data.repositories || []);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Failed to load data', err);
    }
    // Load assigned projects / marks (student view) – non-blocking
    try {
      const projRes = await getMyProjects();
      setMyProjects(projRes.data.projects || []);
    } catch (err) {
      console.error('Failed to load assigned projects', err);
    }
  };

  const handleCreate = async () => {
    setLoading(true);
    try {
      if (tab === 'github') {
        if (!githubUrl) { toast.error('Enter a GitHub URL'); return; }
        await createRepoFromGithub(githubUrl, repoName || githubUrl.split('/').pop());
        toast.success('Repository cloned!');
      } else {
        if (!zipFile) { toast.error('Select a ZIP file'); return; }
        await uploadRepoZip(zipFile, repoName || zipFile.name.replace('.zip', ''));
        toast.success('Repository uploaded!');
      }
      setShowModal(false);
      setGithubUrl(''); setRepoName(''); setZipFile(null);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create repository');
    }
    setLoading(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await searchRepos(searchQuery);
      setSearchResults(res.data.results || []);
    } catch (err) {
      toast.error('Search failed');
    }
  };

  const handleAddCollaborator = async () => {
    if (!collabEmail.trim()) return;
    try {
      await addCollaborator(collabModal, collabEmail);
      toast.success(`Added ${collabEmail} as collaborator`);
      setCollabModal(null);
      setCollabEmail('');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to add collaborator');
    }
  };

  const handleSubmitProject = async () => {
    if (!submitUrl.trim()) { toast.error('Enter a GitHub URL'); return; }
    try {
      await submitProject(submitModal, submitUrl);
      toast.success('Project submitted!');
      setSubmitModal(null);
      setSubmitUrl('');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to submit');
    }
  };

  const statusBadge = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-700',
      analyzing: 'bg-yellow-100 text-yellow-700',
      pending: 'bg-gray-100 text-gray-600',
      failed: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || colors.pending}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 text-sm">Welcome back, {profile?.username}</p>
          </div>
          <button onClick={() => setShowModal(true)}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">
            + New Repository
          </button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Projects Analyzed', value: stats.projects_analyzed, color: 'text-blue-600' },
              { label: 'Documents Generated', value: stats.documents_generated, color: 'text-green-600' },
              { label: 'Diagrams Created', value: stats.diagrams_generated, color: 'text-purple-600' },
              { label: 'Security Issues', value: stats.security_issues_found, color: 'text-red-600' },
            ].map((s, i) => (
              <div key={i} className="bg-white rounded-xl p-4 border border-gray-200">
                <p className="text-sm text-gray-500">{s.label}</p>
                <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Charts */}
        {stats && (
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4">Activity Overview</h3>
              <Doughnut data={{
                labels: ['Analyzed', 'Docs', 'Diagrams', 'Security Issues'],
                datasets: [{
                  data: [stats.projects_analyzed, stats.documents_generated, stats.diagrams_generated, stats.security_issues_found],
                  backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#ef4444'],
                }],
              }} options={{ plugins: { legend: { position: 'bottom' } } }} />
            </div>
            {stats.projects_per_month && Object.keys(stats.projects_per_month).length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-4">Projects Per Month</h3>
                <Bar data={{
                  labels: Object.keys(stats.projects_per_month),
                  datasets: [{
                    label: 'Projects',
                    data: Object.values(stats.projects_per_month),
                    backgroundColor: '#3b82f6',
                  }],
                }} />
              </div>
            )}
          </div>
        )}

        {/* Search GitHub */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 mb-8">
          <h3 className="font-semibold text-gray-900 mb-3">Search Public Repositories</h3>
          <div className="flex gap-2">
            <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search GitHub repositories..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
            <button onClick={handleSearch}
              className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800">
              Search
            </button>
          </div>
          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              {searchResults.map((r, i) => (
                <div key={i} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{r.name}</p>
                    <p className="text-xs text-gray-500">{r.description?.substring(0, 80)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">⭐ {r.stars}</span>
                    <button onClick={() => { setGithubUrl(r.url); setRepoName(r.name.split('/').pop()); setShowModal(true); setTab('github'); }}
                      className="text-xs bg-primary-600 text-white px-3 py-1 rounded-lg hover:bg-primary-700">
                      Clone
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Repositories List */}
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Your Repositories ({repos.length})</h3>
          </div>
          {repos.length === 0 ? (
            <div className="p-12 text-center text-gray-400">
              <p className="text-lg mb-2">No repositories yet</p>
              <p className="text-sm">Upload a ZIP file or clone a GitHub repository to get started.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {repos.map((repo) => (
                <div key={repo.id} className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
                  <Link to={`/repo/${repo.id}`} className="flex-1">
                    <p className="font-medium text-gray-900">
                      {repo.name}
                      {repo.is_collaborator && (
                        <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">Shared</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-400">
                      {repo.source === 'github' ? `🔗 ${repo.github_url}` : '📦 Uploaded ZIP'}
                    </p>
                  </Link>
                  <div className="flex items-center gap-2">
                    {!repo.is_collaborator && (
                      <button onClick={(e) => { e.preventDefault(); setCollabModal(repo.id); }}
                        className="text-xs bg-purple-50 text-purple-600 px-3 py-1 rounded-full hover:bg-purple-100">
                        + Collaborator
                      </button>
                    )}
                    {statusBadge(repo.status)}
                    <Link to={`/repo/${repo.id}`} className="text-gray-300">→</Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Assigned Projects & Marks (Student View) */}
        {(profile?.role === 'student' || myProjects.length > 0) && (
          <div className="bg-white rounded-xl border border-gray-200 mt-8">
            <div className="p-6 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Assigned Projects & Marks</h3>
            </div>
            {myProjects.length === 0 && (
              <div className="p-8 text-center text-gray-400">
                <p>No projects assigned yet.</p>
                <p className="text-xs mt-1">When your teacher assigns a project, it will appear here.</p>
              </div>
            )}
            {myProjects.length > 0 && <div className="divide-y divide-gray-100">
              {myProjects.map((proj) => (
                <div key={proj.id} className="p-5">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{proj.title}</p>
                      {proj.description && <p className="text-sm text-gray-500 mt-1">{proj.description}</p>}
                      {proj.deadline && <p className="text-xs text-gray-400 mt-1">Deadline: {proj.deadline}</p>}

                      {/* Submission status */}
                      <div className="mt-3">
                        {proj.my_submission ? (
                          <div className="flex items-center gap-2">
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Submitted</span>
                            <a href={proj.my_submission.github_url} target="_blank" rel="noreferrer"
                              className="text-xs text-blue-600 hover:underline break-all">
                              {proj.my_submission.github_url}
                            </a>
                          </div>
                        ) : (
                          <button onClick={() => setSubmitModal(proj.id)}
                            className="text-xs bg-primary-600 text-white px-4 py-1.5 rounded-lg hover:bg-primary-700">
                            Submit Project (GitHub Link)
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Marks */}
                    <div className="text-right ml-4">
                      {proj.my_marks != null ? (
                        <div>
                          <span className={`text-2xl font-bold ${proj.my_marks >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                            {proj.my_marks}
                          </span>
                          <span className="text-sm text-gray-400">/100</span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400 italic">Not graded yet</span>
                      )}
                    </div>
                  </div>
                  {proj.my_comments && (
                    <p className="text-sm text-gray-600 mt-3 bg-gray-50 rounded-lg p-2">
                      💬 {proj.my_comments}
                    </p>
                  )}
                </div>
              ))}
            </div>}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Repository</h3>
            <div className="flex gap-2 mb-4">
              <button onClick={() => setTab('github')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === 'github' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
                GitHub URL
              </button>
              <button onClick={() => setTab('upload')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium ${tab === 'upload' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
                Upload ZIP
              </button>
            </div>
            <div className="space-y-3">
              <input value={repoName} onChange={(e) => setRepoName(e.target.value)}
                placeholder="Project name" className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none" />
              {tab === 'github' ? (
                <input value={githubUrl} onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/user/repo" className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none" />
              ) : (
                <input type="file" accept=".zip" onChange={(e) => setZipFile(e.target.files[0])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
              )}
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button onClick={handleCreate} disabled={loading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
                {loading ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Collaborator Modal */}
      {collabModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Collaborator</h3>
            <p className="text-sm text-gray-500 mb-3">Enter the email of a registered user to share this repository.</p>
            <input value={collabEmail} onChange={(e) => setCollabEmail(e.target.value)}
              placeholder="collaborator@email.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-purple-500 mb-4" />
            <div className="flex justify-end gap-2">
              <button onClick={() => { setCollabModal(null); setCollabEmail(''); }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button onClick={handleAddCollaborator}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700">
                Add
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Submit Project Modal */}
      {submitModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Submit Project</h3>
            <p className="text-sm text-gray-500 mb-3">Paste your GitHub repository URL to submit.</p>
            <input value={submitUrl} onChange={(e) => setSubmitUrl(e.target.value)}
              placeholder="https://github.com/username/repo"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-primary-500 mb-4" />
            <div className="flex justify-end gap-2">
              <button onClick={() => { setSubmitModal(null); setSubmitUrl(''); }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button onClick={handleSubmitProject}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
