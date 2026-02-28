import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { listStudents, createProject, listProjects, scoreProject, addStudentToProject, addRepoToProject } from '../services/api';

export default function FacultyPanel() {
  const [tab, setTab] = useState('projects');
  const [projects, setProjects] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', deadline: '' });
  const [scoreModal, setScoreModal] = useState(null);
  const [scoreForm, setScoreForm] = useState({ code_quality: '', innovation: '', documentation: '', presentation: '', comments: '' });
  const [addStudentModal, setAddStudentModal] = useState(null);
  const [studentEmail, setStudentEmail] = useState('');
  const [repoModal, setRepoModal] = useState(null);
  const [repoId, setRepoId] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pRes, sRes] = await Promise.all([listProjects(), listStudents()]);
      setProjects(pRes.data.projects || []);
      setStudents(sRes.data.students || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleCreateProject = async () => {
    if (!form.title.trim()) return;
    try {
      await createProject(form);
      setShowModal(false);
      setForm({ title: '', description: '', deadline: '' });
      loadData();
    } catch { /* ignore */ }
  };

  const handleScore = async () => {
    try {
      const scores = {};
      for (const [k, v] of Object.entries(scoreForm)) {
        if (k !== 'comments' && v) scores[k] = parseFloat(v);
        else if (v) scores[k] = v;
      }
      await scoreProject(scoreModal, scores);
      setScoreModal(null);
      setScoreForm({ code_quality: '', innovation: '', documentation: '', presentation: '', comments: '' });
      loadData();
    } catch { /* ignore */ }
  };

  const handleAddStudent = async () => {
    if (!studentEmail.trim()) return;
    try {
      await addStudentToProject(addStudentModal, studentEmail);
      setAddStudentModal(null);
      setStudentEmail('');
      loadData();
    } catch { /* ignore */ }
  };

  const handleAddRepo = async () => {
    if (!repoId.trim()) return;
    try {
      await addRepoToProject(repoModal, repoId);
      setRepoModal(null);
      setRepoId('');
      loadData();
    } catch { /* ignore */ }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Faculty Panel</h1>
          <button onClick={() => setShowModal(true)} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
            + New Project
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
          {['projects', 'students'].map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${tab === t ? 'bg-white shadow text-primary-600' : 'text-gray-600'}`}>
              {t}
            </button>
          ))}
        </div>

        {loading ? <p className="text-gray-500">Loading...</p> : tab === 'projects' ? (
          <div className="space-y-4">
            {projects.length === 0 ? <p className="text-gray-500">No projects yet. Create your first project.</p> :
              projects.map(p => (
                <div key={p.id} className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{p.title}</h3>
                    <div className="flex gap-2">
                      <button onClick={() => setAddStudentModal(p.id)} className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full hover:bg-blue-100">+ Student</button>
                      <button onClick={() => setRepoModal(p.id)} className="text-xs bg-green-50 text-green-600 px-3 py-1 rounded-full hover:bg-green-100">+ Repo</button>
                      <button onClick={() => setScoreModal(p.id)} className="text-xs bg-amber-50 text-amber-600 px-3 py-1 rounded-full hover:bg-amber-100">Score</button>
                    </div>
                  </div>
                  {p.description && <p className="text-sm text-gray-600 mb-3">{p.description}</p>}
                  <div className="flex gap-4 text-xs text-gray-500">
                    {p.deadline && <span>Deadline: {p.deadline}</span>}
                    <span>Students: {p.students?.length || 0}</span>
                    <span>Repos: {p.repositories?.length || 0}</span>
                    {p.score && <span className="text-amber-600 font-medium">Score: {typeof p.score === 'object' ? Object.values(p.score).filter(v => typeof v === 'number').reduce((a, b) => a + b, 0) : p.score}</span>}
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Department</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Repos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {students.length === 0 ? (
                  <tr><td colSpan="4" className="px-6 py-8 text-center text-gray-500">No students assigned yet.</td></tr>
                ) : students.map((s, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{s.username || s.email}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{s.email}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{s.department || '-'}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{s.repo_count ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold mb-4">New Project</h2>
            <input placeholder="Project Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg mb-3 outline-none focus:ring-2 focus:ring-primary-500" />
            <textarea placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg mb-3 outline-none focus:ring-2 focus:ring-primary-500" rows="3" />
            <input type="date" value={form.deadline} onChange={e => setForm({ ...form, deadline: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg mb-4 outline-none focus:ring-2 focus:ring-primary-500" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button onClick={handleCreateProject} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Create</button>
            </div>
          </div>
        </div>
      )}

      {/* Score Modal */}
      {scoreModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold mb-4">Score Project</h2>
            {['code_quality', 'innovation', 'documentation', 'presentation'].map(k => (
              <div key={k} className="mb-3">
                <label className="block text-sm text-gray-600 mb-1 capitalize">{k.replace('_', ' ')} (0-10)</label>
                <input type="number" min="0" max="10" step="0.5" value={scoreForm[k]} onChange={e => setScoreForm({ ...scoreForm, [k]: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
              </div>
            ))}
            <textarea placeholder="Comments" value={scoreForm.comments} onChange={e => setScoreForm({ ...scoreForm, comments: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg mb-4 outline-none focus:ring-2 focus:ring-primary-500" rows="2" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setScoreModal(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button onClick={handleScore} className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600">Submit Score</button>
            </div>
          </div>
        </div>
      )}

      {/* Add Student Modal */}
      {addStudentModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold mb-4">Add Student</h2>
            <input placeholder="Student UID or Email" value={studentEmail} onChange={e => setStudentEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg mb-4 outline-none focus:ring-2 focus:ring-primary-500" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setAddStudentModal(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button onClick={handleAddStudent} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Add</button>
            </div>
          </div>
        </div>
      )}

      {/* Add Repo Modal */}
      {repoModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold mb-4">Add Repository</h2>
            <input placeholder="Repository ID" value={repoId} onChange={e => setRepoId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg mb-4 outline-none focus:ring-2 focus:ring-primary-500" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setRepoModal(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button onClick={handleAddRepo} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">Add</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
