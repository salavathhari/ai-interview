import { useEffect, useState } from 'react';
import { Plus, Trash2, Video, X } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Template = { id: number; name: string; description?: string; role: string; difficulty: string; interview_type: string; topics: string[]; num_questions: number; time_limit_min: number; is_active: boolean; created_at: string; };

export default function RecruiterInterviewsPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', role: '', difficulty: 'Medium', interview_type: 'Technical', topics: [] as string[], num_questions: 5, time_limit_min: 30 });
  const [topicInput, setTopicInput] = useState('');

  const fetch = () => { setLoading(true); recruiterApi.getInterviewTemplates().then(r => setTemplates(r.data)).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(() => { fetch(); }, []);

  const handleCreate = async () => {
    await recruiterApi.createInterviewTemplate(form);
    setShowCreate(false);
    setForm({ name: '', description: '', role: '', difficulty: 'Medium', interview_type: 'Technical', topics: [], num_questions: 5, time_limit_min: 30 });
    fetch();
  };

  const handleDelete = async (id: number) => { if (confirm('Delete template?')) { await recruiterApi.deleteInterviewTemplate(id); fetch(); } };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <p style={{ color: 'var(--rp-muted)', margin: 0 }}>{templates.length} template{templates.length !== 1 ? 's' : ''}</p>
        <button className="rp-btn rp-btn--primary" onClick={() => setShowCreate(true)}><Plus size={16} /> New Template</button>
      </div>

      {showCreate && (
        <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>New Interview Template</h3>
            <button className="rp-btn rp-btn--ghost" onClick={() => setShowCreate(false)}><X size={16} /></button>
          </div>
          <div className="rp-row rp-row--2">
            <div className="rp-field"><label className="rp-label">Name *</label><input className="rp-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Senior Engineer Technical" /></div>
            <div className="rp-field"><label className="rp-label">Role *</label><input className="rp-input" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} placeholder="Software Engineer" /></div>
          </div>
          <div className="rp-row rp-row--3">
            <div className="rp-field"><label className="rp-label">Type</label><select className="rp-select" value={form.interview_type} onChange={e => setForm({ ...form, interview_type: e.target.value })}>
              {['Technical', 'Behavioral', 'HR', 'DSA', 'DBMS', 'OS', 'CN', 'OOP', 'System Design', 'Frontend', 'Backend', 'Cloud', 'Machine Learning'].map(t => <option key={t} value={t}>{t}</option>)}
            </select></div>
            <div className="rp-field"><label className="rp-label">Difficulty</label><select className="rp-select" value={form.difficulty} onChange={e => setForm({ ...form, difficulty: e.target.value })}>
              {['Easy', 'Medium', 'Hard', 'Adaptive'].map(d => <option key={d} value={d}>{d}</option>)}
            </select></div>
            <div className="rp-field"><label className="rp-label">Questions</label><input className="rp-input" type="number" value={form.num_questions} onChange={e => setForm({ ...form, num_questions: parseInt(e.target.value) || 5 })} /></div>
          </div>
          <div className="rp-field"><label className="rp-label">Description</label><textarea className="rp-textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} /></div>
          <div className="rp-field"><label className="rp-label">Topics</label>
            <div className="rp-tags">
              {form.topics.map((t, i) => <span key={i} className="rp-tag">{t}<button className="rp-tag-remove" onClick={() => setForm({ ...form, topics: form.topics.filter((_, j) => j !== i) })}><X size={12} /></button></span>)}
              <input style={{ border: 'none', background: 'none', color: 'var(--rp-text)', outline: 'none', flex: 1, minWidth: 100, fontSize: '0.85rem' }} value={topicInput} onChange={e => setTopicInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); if (topicInput.trim()) { setForm({ ...form, topics: [...form.topics, topicInput.trim()] }); setTopicInput(''); } } }} placeholder="Add topic" />
            </div>
          </div>
          <button className="rp-btn rp-btn--primary" onClick={handleCreate} disabled={!form.name.trim() || !form.role.trim()}>Create Template</button>
        </div>
      )}

      {loading ? [1, 2].map(i => <div key={i} className="rp-skeleton" style={{ height: 80, marginBottom: 8 }} />) : templates.length === 0 ? (
        <div className="rp-card rp-empty"><div className="rp-empty-icon"><Video size={24} /></div><h3>No templates yet</h3><p>Create a template to streamline interview setup.</p></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {templates.map(t => (
            <div key={t.id} className="rp-card" style={{ padding: '1rem 1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <strong>{t.name}</strong>
                    <span className="rp-badge rp-badge--open" style={t.is_active ? {} : { opacity: 0.5 }}>{t.is_active ? 'Active' : 'Inactive'}</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{t.role} | {t.interview_type} | {t.difficulty} | {t.num_questions} questions | {t.time_limit_min}min</div>
                  {t.topics.length > 0 && <div className="rp-tags" style={{ marginTop: '0.5rem' }}>{t.topics.map((tp, i) => <span key={i} className="rp-tag">{tp}</span>)}</div>}
                </div>
                <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ color: 'var(--rp-danger)' }} onClick={() => handleDelete(t.id)}><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
