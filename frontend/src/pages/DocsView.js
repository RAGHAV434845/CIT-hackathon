import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { generateReadme, generateApiDoc, generateReport, generateModuleBreakdown, listDocs, editDoc, exportDoc } from '../services/api';
import ReactMarkdown from 'react-markdown';
import toast from 'react-hot-toast';

export default function DocsView() {
  const { repoId } = useParams();
  const [docs, setDocs] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [generating, setGenerating] = useState('');

  useEffect(() => { loadDocs(); }, [repoId]);

  const loadDocs = async () => {
    try {
      const res = await listDocs(repoId);
      setDocs(res.data.documents || []);
    } catch {}
  };

  const generate = async (type, fn) => {
    setGenerating(type);
    try {
      const res = await fn(repoId);
      setActiveDoc({ id: res.data.doc_id, content: res.data.content, type: res.data.type });
      toast.success(`${type} generated!`);
      loadDocs();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Generation failed');
    }
    setGenerating('');
  };

  const handleSave = async () => {
    try {
      await editDoc(activeDoc.id, editContent);
      setActiveDoc({ ...activeDoc, content: editContent });
      setEditing(false);
      toast.success('Saved!');
    } catch {
      toast.error('Save failed');
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await exportDoc(activeDoc.id, format);
      const blob = new Blob([res.data], { type: format === 'pdf' ? 'application/pdf' : 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document.${format === 'markdown' ? 'md' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Export failed');
    }
  };

  const generators = [
    { label: 'README', type: 'readme', fn: generateReadme },
    { label: 'API Docs', type: 'api_doc', fn: generateApiDoc },
    { label: 'Tech Report', type: 'tech_report', fn: generateReport },
    { label: 'Module Breakdown', type: 'module_breakdown', fn: generateModuleBreakdown },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link to={`/repo/${repoId}`} className="text-sm text-primary-600 hover:underline mb-4 inline-block">← Back</Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Documentation</h1>

        {/* Generators */}
        <div className="flex flex-wrap gap-2 mb-6">
          {generators.map(g => (
            <button key={g.type} onClick={() => generate(g.label, g.fn)} disabled={!!generating}
              className="bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50">
              {generating === g.label ? '⏳ Generating...' : `📄 Generate ${g.label}`}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-4 gap-6">
          {/* Doc list */}
          <div className="md:col-span-1">
            <h3 className="font-semibold text-sm text-gray-500 mb-2 uppercase">Documents ({docs.length})</h3>
            <div className="space-y-1">
              {docs.map(doc => (
                <button key={doc.id} onClick={() => { setActiveDoc(doc); setEditing(false); }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm ${activeDoc?.id === doc.id ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-100 text-gray-600'}`}>
                  {doc.type?.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Doc content */}
          <div className="md:col-span-3">
            {activeDoc ? (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="flex justify-between items-center p-4 border-b border-gray-100">
                  <h3 className="font-semibold capitalize">{activeDoc.type?.replace('_', ' ')}</h3>
                  <div className="flex gap-2">
                    <button onClick={() => { setEditing(!editing); setEditContent(activeDoc.content); }}
                      className="text-xs px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200">
                      {editing ? 'Preview' : 'Edit'}
                    </button>
                    <button onClick={() => handleExport('markdown')}
                      className="text-xs px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200">
                      Export MD
                    </button>
                    <button onClick={() => handleExport('pdf')}
                      className="text-xs px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200">
                      Export PDF
                    </button>
                  </div>
                </div>
                <div className="p-6">
                  {editing ? (
                    <div>
                      <textarea value={editContent} onChange={(e) => setEditContent(e.target.value)}
                        rows={20} className="w-full font-mono text-sm border border-gray-200 rounded-lg p-3 focus:ring-2 focus:ring-primary-500 outline-none" />
                      <button onClick={handleSave}
                        className="mt-3 bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">
                        Save Changes
                      </button>
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown>{activeDoc.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl p-12 border border-gray-200 text-center text-gray-400">
                <p>Generate or select a document to view</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
