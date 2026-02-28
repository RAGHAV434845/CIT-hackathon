import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { generateDiagrams, listDiagrams, updateDiagram } from '../services/api';
import mermaid from 'mermaid';
import toast from 'react-hot-toast';

mermaid.initialize({ startOnLoad: false, theme: 'base', securityLevel: 'loose' });

function MermaidDiagram({ code, id }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current && code) {
      mermaid.render(`mermaid-${id}`, code).then(({ svg }) => {
        ref.current.innerHTML = svg;
      }).catch(err => {
        ref.current.innerHTML = `<pre class="text-red-500 text-xs">${err.message}</pre>`;
      });
    }
  }, [code, id]);

  return <div ref={ref} className="overflow-auto" />;
}

export default function DiagramView() {
  const { repoId } = useParams();
  const [diagrams, setDiagrams] = useState([]);
  const [active, setActive] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editCode, setEditCode] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => { loadDiagrams(); }, [repoId]);

  const loadDiagrams = async () => {
    try {
      const res = await listDiagrams(repoId);
      const d = res.data.diagrams || [];
      setDiagrams(d);
      if (d.length > 0 && !active) setActive(d[0]);
    } catch {}
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await generateDiagrams(repoId, 'all');
      const newDiagrams = res.data.diagrams || [];
      setDiagrams(newDiagrams);
      if (newDiagrams.length > 0) setActive(newDiagrams[0]);
      toast.success('Diagrams generated!');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    try {
      await updateDiagram(active.diagram_id || active.id, { mermaid_code: editCode });
      setActive({ ...active, mermaid_code: editCode });
      setEditMode(false);
      toast.success('Diagram saved!');
    } catch {
      toast.error('Save failed');
    }
  };

  const handleExport = () => {
    const svg = document.querySelector('.mermaid svg') || document.querySelector('[id^="mermaid-"] svg');
    if (!svg) { toast.error('No diagram to export'); return; }
    const data = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([data], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${active?.type || 'diagram'}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link to={`/repo/${repoId}`} className="text-sm text-primary-600 hover:underline mb-4 inline-block">← Back</Link>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Diagrams</h1>
          <button onClick={handleGenerate} disabled={generating}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
            {generating ? '⏳ Generating...' : '📊 Generate All Diagrams'}
          </button>
        </div>

        {diagrams.length === 0 ? (
          <div className="bg-white rounded-xl p-12 border border-gray-200 text-center text-gray-400">
            <p className="text-lg mb-2">No diagrams yet</p>
            <p className="text-sm">Click "Generate All Diagrams" to create architecture, flow, and dependency diagrams.</p>
          </div>
        ) : (
          <div>
            {/* Diagram type tabs */}
            <div className="flex gap-2 mb-4">
              {diagrams.map((d, i) => (
                <button key={i} onClick={() => { setActive(d); setEditMode(false); }}
                  className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${
                    active === d ? 'bg-primary-600 text-white' : 'bg-white border border-gray-200 text-gray-600'
                  }`}>
                  {d.type}
                </button>
              ))}
            </div>

            {/* Diagram viewer */}
            {active && (
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="flex justify-between items-center p-4 border-b border-gray-100">
                  <h3 className="font-semibold capitalize">{active.type} Diagram</h3>
                  <div className="flex gap-2">
                    <button onClick={() => { setEditMode(!editMode); setEditCode(active.mermaid_code); }}
                      className="text-xs px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200">
                      {editMode ? 'Preview' : 'Edit Code'}
                    </button>
                    <button onClick={handleExport}
                      className="text-xs px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200">
                      Export SVG
                    </button>
                  </div>
                </div>
                <div className="p-6">
                  {editMode ? (
                    <div>
                      <textarea value={editCode} onChange={(e) => setEditCode(e.target.value)}
                        rows={15} className="w-full font-mono text-sm border border-gray-200 rounded-lg p-3 focus:ring-2 focus:ring-primary-500 outline-none mb-3" />
                      <div className="flex gap-2">
                        <button onClick={handleSave}
                          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">
                          Save
                        </button>
                        <button onClick={() => setEditMode(false)}
                          className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2">
                          Cancel
                        </button>
                      </div>
                      {/* Live preview */}
                      <div className="mt-4 border-t border-gray-100 pt-4">
                        <p className="text-xs text-gray-400 mb-2">Live Preview:</p>
                        <MermaidDiagram code={editCode} id={`edit-${active.type}`} />
                      </div>
                    </div>
                  ) : (
                    <MermaidDiagram code={active.mermaid_code} id={active.type} />
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
