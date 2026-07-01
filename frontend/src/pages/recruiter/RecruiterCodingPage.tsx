import { useEffect, useState } from 'react';
import { Plus, Trash2, Code2, X } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Template = { id: number; name: string; description?: string; difficulty: string; challenge_ids: number[]; time_limit_min: number; is_active: boolean; created_at: string; };

export default function RecruiterCodingPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', difficulty: 'Medium', challenge_ids: [] as number[], time_limit_min: 60 });
  const [challengeInput, setChallengeInput] = useState('');

  const fetchT = () => { setLoading(true); recruiterApi.getCodingTemplates().then(r => setTemplates(r.data)).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(() => { fetchT(); }, []);

  const handleCreate = async () => {
    await recruiterApi.createCodingTemplate(form);
    setShowCreate(false);
    setForm({ name: '', description: '', difficulty: 'Medium', challenge_ids: [], time_limit_min: 60 });
    fetchT();
  };

  const handleDelete = async (id: number) => { if (confirm('Delete template?')) { await recruiterApi.deleteCodingTemplate(id); fetchT(); } };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <p style={{ color: 'var(--rp-muted)', margin: 0 }}>{templates.length} template{templates.length !== 1 ? 's' : ''}</p>
        <button className="rp-btn rp-btn--primary" onClick={() => setShowCreate(true)}><Plus size={16} /> New Template</button>
      </div>

      {showCreate && (
        <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>New Coding Template</h3>
            <button className="rp-btn rp-btn--ghost" onClick={() => setShowCreate(false)}><X size={16} /></button>
          </div>
          <div className="rp-row rp-row--2">
            <div className="rp-field"><label className="rp-label">Name *</label><input className="rp-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="SDE Coding Assessment" /></div>
            <div className="rp-field"><label className="rp-label">Difficulty</label><select className="rp-select" value={form.difficulty} onChange={e => setForm({ ...form, difficulty: e.target.value })}>
              {['Easy', 'Medium', 'Hard'].map(d => <option key={d} value={d}>{d}</option>)}
            </select></div>
          </div>
          <div className="rp-row rp-row--2">
            <div className="rp-field"><label className="rp-label">Time Limit (min)</label><input className="rp-input" type="number" value={form.time_limit_min} onChange={e => setForm({ ...form, time_limit_min: parseInt(e.target.value) || 60 })} /></div>
            <div className="rp-field"><label className="rp-label">Challenge IDs</label>
              <div className="rp-tags">
                {form.challenge_ids.map((id, i) => <span key={i} className="rp-tag">#{id}<button className="rp-tag-remove" onClick={() => setForm({ ...form, challenge_ids: form.challenge_ids.filter((_, j) => j !== i) })}><X size={12} /></button></span>)}
                <input style={{ border: 'none', background: 'none', color: 'var(--rp-text)', outline: 'none', width: 80, fontSize: '0.85rem' }} value={challengeInput} onChange={e => setChallengeInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); const id = parseInt(challengeInput); if (id) { setForm({ ...form, challenge_ids: [...form.challenge_ids, id] }); setChallengeInput(''); } } }} placeholder="ID" />
              </div>
            </div>
          </div>
          <div className="rp-field"><label className="rp-label">Description</label><textarea className="rp-textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} /></div>
          <button className="rp-btn rp-btn--primary" onClick={handleCreate} disabled={!form.name.trim()}>Create Template</button>
        </div>
      )}

      {loading ? [1, 2].map(i => <div key={i} className="rp-skeleton" style={{ height: 80, marginBottom: 8 }} />) : templates.length === 0 ? (
        <div className="rp-card rp-empty"><div className="rp-empty-icon"><Code2 size={24} /></div><h3>No templates yet</h3><p>Create a coding template to assign assessments.</p></div>
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
                  <div style={{ fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{t.difficulty} | {t.time_limit_min}min | {t.challenge_ids.length} challenge{t.challenge_ids.length !== 1 ? 's' : ''}</div>
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
