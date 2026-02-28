import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { listFaculty, listAllStudents, assignMentor, scoreFaculty, listAllRepos, getDeptAnalytics } from '../services/api';

export default function HODPanel() {
  const [tab, setTab] = useState('overview');
  const [faculty, setFaculty] = useState([]);
  const [students, setStudents] = useState([]);
  const [repos, setRepos] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mentorModal, setMentorModal] = useState(null);
  const [mentorFacultyId, setMentorFacultyId] = useState('');
  const [scoreModal, setScoreModal] = useState(null);
  const [facultyScore, setFacultyScore] = useState({ mentoring: '', responsiveness: '', comments: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fRes, sRes, rRes, aRes] = await Promise.all([
        listFaculty(), listAllStudents(), listAllRepos(), getDeptAnalytics()
      ]);
      setFaculty(fRes.data.faculty || []);
      setStudents(sRes.data.students || []);
      setRepos(rRes.data.repositories || []);
      setAnalytics(aRes.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleAssignMentor = async () => {
    if (!mentorFacultyId) return;
    try {
      await assignMentor(mentorModal, mentorFacultyId);
      setMentorModal(null);
      setMentorFacultyId('');
      loadData();
    } catch { /* ignore */ }
  };

  const handleScoreFaculty = async () => {
    try {
      const scores = {};
      for (const [k, v] of Object.entries(facultyScore)) {
        if (k !== 'comments' && v) scores[k] = parseFloat(v);
        else if (v) scores[k] = v;
      }
      await scoreFaculty(scoreModal, scores);
      setScoreModal(null);
      setFacultyScore({ mentoring: '', responsiveness: '', comments: '' });
      loadData();
    } catch { /* ignore */ }
  };

  const StatCard = ({ label, value, color }) => (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${color || 'text-gray-900'}`}>{value}</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">HOD Dashboard</h1>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
          {['overview', 'faculty', 'students', 'repositories'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${tab === t ? 'bg-white shadow text-primary-600' : 'text-gray-600'}`}>
              {t}
            </button>
          ))}
        </div>

        {loading ? <p className="text-gray-500">Loading...</p> : (
          <>
            {/* Overview */}
            {tab === 'overview' && (
              <div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  <StatCard label="Total Faculty" value={faculty.length} color="text-blue-600" />
                  <StatCard label="Total Students" value={students.length} color="text-green-600" />
                  <StatCard label="Total Repositories" value={repos.length} color="text-purple-600" />
                  <StatCard label="Analyzed" value={repos.filter(r => r.analysis_status === 'completed').length} color="text-amber-600" />
                </div>
                {analytics && (
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h2 className="text-lg font-semibold mb-4">Department Analytics</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {analytics.top_languages && Object.entries(analytics.top_languages).slice(0, 8).map(([lang, count]) => (
                        <div key={lang} className="bg-gray-50 rounded-lg p-3">
                          <p className="text-sm font-medium text-gray-700">{lang}</p>
                          <p className="text-xl font-bold text-primary-600">{count}</p>
                        </div>
                      ))}
                    </div>
                    {analytics.top_frameworks && analytics.top_frameworks.length > 0 && (
                      <div className="mt-4">
                        <h3 className="text-sm font-medium text-gray-500 mb-2">Top Frameworks</h3>
                        <div className="flex flex-wrap gap-2">
                          {analytics.top_frameworks.map((fw, i) => (
                            <span key={i} className="bg-primary-50 text-primary-700 px-3 py-1 rounded-full text-sm">{fw}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Faculty Tab */}
            {tab === 'faculty' && (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Department</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Students</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {faculty.map((f, i) => (
                      <tr key={i}>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{f.username || f.email}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{f.email}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{f.department || '-'}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{f.student_count ?? 0}</td>
                        <td className="px-6 py-4">
                          <button onClick={() => setScoreModal(f.uid || f.id)}
                            className="text-xs bg-amber-50 text-amber-600 px-3 py-1 rounded-full hover:bg-amber-100 mr-2">Score</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Students Tab */}
            {tab === 'students' && (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Department</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Mentor</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {students.map((s, i) => (
                      <tr key={i}>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{s.username || s.email}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{s.email}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{s.department || '-'}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{s.mentor_name || s.mentor_id || 'Unassigned'}</td>
                        <td className="px-6 py-4">
                          <button onClick={() => setMentorModal(s.uid || s.id)}
                            className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full hover:bg-blue-100">Assign Mentor</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Repositories Tab */}
            {tab === 'repositories' && (
              <div className="space-y-3">
                {repos.length === 0 ? <p className="text-gray-500">No repositories in department.</p> :
                  repos.map((r, i) => (
                    <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 flex justify-between items-center">
                      <div>
                        <h3 className="font-medium text-gray-900">{r.name}</h3>
                        <p className="text-sm text-gray-500">{r.owner_name || r.owner_id} • {r.source || 'unknown'}</p>
                      </div>
                      <span className={`px-3 py-1 text-xs rounded-full ${
                        r.analysis_status === 'completed' ? 'bg-green-100 text-green-700'
                        : r.analysis_status === 'running' ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-600'
                      }`}>{r.analysis_status || 'pending'}</span>
                    </div>
                  ))
                }
              </div>
            )}
          </>
        )}
      </div>

      {/* Assign Mentor Modal */}
      {mentorModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold mb-4">Assign Mentor</h2>
            <select value={mentorFacultyId} onChange={e => setMentorFacultyId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg mb-4 outline-none focus:ring-2 focus:ring-primary-500">
              <option value="">Select Faculty</option>
              {faculty.map((f, i) => (
                <option key={i} value={f.uid || f.id}>{f.username || f.email}</option>
              ))}
            </select>
            <div className="flex justify-end gap-2">
              <button onClick={() => setMentorModal(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button onClick={handleAssignMentor} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Assign</button>
            </div>
          </div>
        </div>
      )}

      {/* Score Faculty Modal */}
      {scoreModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold mb-4">Score Faculty</h2>
            {['mentoring', 'responsiveness'].map(k => (
              <div key={k} className="mb-3">
                <label className="block text-sm text-gray-600 mb-1 capitalize">{k} (0-10)</label>
                <input type="number" min="0" max="10" step="0.5" value={facultyScore[k]}
                  onChange={e => setFacultyScore({ ...facultyScore, [k]: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
              </div>
            ))}
            <textarea placeholder="Comments" value={facultyScore.comments}
              onChange={e => setFacultyScore({ ...facultyScore, comments: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg mb-4 outline-none focus:ring-2 focus:ring-primary-500" rows="2" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setScoreModal(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button onClick={handleScoreFaculty} className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600">Submit</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
