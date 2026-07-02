import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, X } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

const EMPLOYMENT_TYPES = ['full_time', 'part_time', 'contract', 'intern'];
const EXPERIENCE_LEVELS = ['junior', 'mid', 'senior', 'lead'];
const STATUSES = ['draft', 'open'];

export default function RecruiterJobCreatePage() {
  const nav = useNavigate();
  const { jobId } = useParams();
  const isEdit = !!jobId;

  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', requirements: '',
    department: '', location: '', employment_type: 'full_time',
    experience_level: '', salary_min: '', salary_max: '',
    required_skills: [] as string[], preferred_skills: [] as string[],
    education: '', responsibilities: [] as string[], benefits: [] as string[],
    status: 'draft',
  });
  const [skillInput, setSkillInput] = useState('');
  const [prefSkillInput, setPrefSkillInput] = useState('');
  const [respInput, setRespInput] = useState('');
  const [benefitInput, setBenefitInput] = useState('');

  const set = (k: string, v: any) => setForm(prev => ({ ...prev, [k]: v }));

  const addTag = (field: 'required_skills' | 'preferred_skills' | 'responsibilities' | 'benefits', val: string, setter: (v: string) => void) => {
    if (val.trim() && !form[field].includes(val.trim())) {
      set(field, [...form[field], val.trim()]);
    }
    setter('');
  };

  const removeTag = (field: 'required_skills' | 'preferred_skills' | 'responsibilities' | 'benefits', idx: number) => {
    set(field, form[field].filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    setSaving(true);
    try {
      const payload = {
        ...form,
        salary_min: form.salary_min ? parseInt(form.salary_min as string) : null,
        salary_max: form.salary_max ? parseInt(form.salary_max as string) : null,
      };
      if (isEdit) {
        await recruiterApi.updateJob(parseInt(jobId!), payload);
      } else {
        await recruiterApi.createJob(payload);
      }
      nav('/recruiter/jobs');
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 720 }}>
      <button className="rp-btn rp-btn--ghost" onClick={() => nav(-1)} style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={16} /> Back
      </button>

      <h2 style={{ margin: '0 0 0.5rem' }}>{isEdit ? 'Edit Job' : 'Create Job Posting'}</h2>
      <p style={{ color: 'var(--rp-muted)', margin: '0 0 1.5rem', fontSize: '0.85rem' }}>
        Step {step} of 3
      </p>

      {/* Steps indicator */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        {[1, 2, 3].map(s => (
          <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s <= step ? 'var(--rp-primary)' : 'var(--rp-border)' }} />
        ))}
      </div>

      <div className="rp-card">
        {step === 1 && (
          <>
            <h3 style={{ margin: '0 0 1.25rem' }}>Basics</h3>
            <div className="rp-field">
              <label className="rp-label">Job Title *</label>
              <input className="rp-input" value={form.title} onChange={e => set('title', e.target.value)} placeholder="Senior Backend Engineer" />
            </div>
            <div className="rp-row rp-row--2">
              <div className="rp-field">
                <label className="rp-label">Department</label>
                <input className="rp-input" value={form.department} onChange={e => set('department', e.target.value)} placeholder="Engineering" />
              </div>
              <div className="rp-field">
                <label className="rp-label">Location</label>
                <input className="rp-input" value={form.location} onChange={e => set('location', e.target.value)} placeholder="San Francisco, CA" />
              </div>
            </div>
            <div className="rp-row rp-row--2">
              <div className="rp-field">
                <label className="rp-label">Employment Type</label>
                <select className="rp-select" value={form.employment_type} onChange={e => set('employment_type', e.target.value)}>
                  {EMPLOYMENT_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
              <div className="rp-field">
                <label className="rp-label">Experience Level</label>
                <select className="rp-select" value={form.experience_level} onChange={e => set('experience_level', e.target.value)}>
                  <option value="">Select level</option>
                  {EXPERIENCE_LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            </div>
            <div className="rp-field">
              <label className="rp-label">Description</label>
              <textarea className="rp-textarea" value={form.description} onChange={e => set('description', e.target.value)} placeholder="Role overview and team context..." rows={4} />
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h3 style={{ margin: '0 0 1.25rem' }}>Details</h3>
            <div className="rp-row rp-row--2">
              <div className="rp-field">
                <label className="rp-label">Salary Min ($)</label>
                <input className="rp-input" type="number" value={form.salary_min} onChange={e => set('salary_min', e.target.value)} placeholder="80000" />
              </div>
              <div className="rp-field">
                <label className="rp-label">Salary Max ($)</label>
                <input className="rp-input" type="number" value={form.salary_max} onChange={e => set('salary_max', e.target.value)} placeholder="150000" />
              </div>
            </div>
            <div className="rp-field">
              <label className="rp-label">Education</label>
              <input className="rp-input" value={form.education} onChange={e => set('education', e.target.value)} placeholder="BS in Computer Science or equivalent" />
            </div>
            <div className="rp-field">
              <label className="rp-label">Requirements</label>
              <textarea className="rp-textarea" value={form.requirements} onChange={e => set('requirements', e.target.value)} placeholder="Job requirements..." rows={3} />
            </div>
            <div className="rp-field">
              <label className="rp-label">Required Skills</label>
              <div className="rp-tags">
                {form.required_skills.map((s, i) => (
                  <span key={i} className="rp-tag">{s}<button className="rp-tag-remove" onClick={() => removeTag('required_skills', i)}><X size={12} /></button></span>
                ))}
                <input style={{ border: 'none', background: 'none', color: 'var(--rp-text)', outline: 'none', flex: 1, minWidth: 100, fontSize: '0.85rem' }}
                  value={skillInput} onChange={e => setSkillInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag('required_skills', skillInput, setSkillInput); } }}
                  placeholder="Type and press Enter" />
              </div>
            </div>
            <div className="rp-field">
              <label className="rp-label">Preferred Skills</label>
              <div className="rp-tags">
                {form.preferred_skills.map((s, i) => (
                  <span key={i} className="rp-tag">{s}<button className="rp-tag-remove" onClick={() => removeTag('preferred_skills', i)}><X size={12} /></button></span>
                ))}
                <input style={{ border: 'none', background: 'none', color: 'var(--rp-text)', outline: 'none', flex: 1, minWidth: 100, fontSize: '0.85rem' }}
                  value={prefSkillInput} onChange={e => setPrefSkillInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag('preferred_skills', prefSkillInput, setPrefSkillInput); } }}
                  placeholder="Type and press Enter" />
              </div>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h3 style={{ margin: '0 0 1.25rem' }}>Finalize</h3>
            <div className="rp-field">
              <label className="rp-label">Responsibilities</label>
              <div className="rp-tags">
                {form.responsibilities.map((s, i) => (
                  <span key={i} className="rp-tag">{s}<button className="rp-tag-remove" onClick={() => removeTag('responsibilities', i)}><X size={12} /></button></span>
                ))}
                <input style={{ border: 'none', background: 'none', color: 'var(--rp-text)', outline: 'none', flex: 1, minWidth: 100, fontSize: '0.85rem' }}
                  value={respInput} onChange={e => setRespInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag('responsibilities', respInput, setRespInput); } }}
                  placeholder="Add responsibility and press Enter" />
              </div>
            </div>
            <div className="rp-field">
              <label className="rp-label">Benefits</label>
              <div className="rp-tags">
                {form.benefits.map((s, i) => (
                  <span key={i} className="rp-tag">{s}<button className="rp-tag-remove" onClick={() => removeTag('benefits', i)}><X size={12} /></button></span>
                ))}
                <input style={{ border: 'none', background: 'none', color: 'var(--rp-text)', outline: 'none', flex: 1, minWidth: 100, fontSize: '0.85rem' }}
                  value={benefitInput} onChange={e => setBenefitInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag('benefits', benefitInput, setBenefitInput); } }}
                  placeholder="Add benefit and press Enter" />
              </div>
            </div>
            <div className="rp-field">
              <label className="rp-label">Status</label>
              <select className="rp-select" value={form.status} onChange={e => set('status', e.target.value)}>
                {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
          </>
        )}
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
        {step > 1 ? (
          <button className="rp-btn rp-btn--secondary" onClick={() => setStep(step - 1)}>Previous</button>
        ) : <div />}
        {step < 3 ? (
          <button className="rp-btn rp-btn--primary" onClick={() => setStep(step + 1)}>Next</button>
        ) : (
          <button className="rp-btn rp-btn--primary" onClick={handleSubmit} disabled={saving || !form.title.trim()}>
            {saving ? 'Saving...' : isEdit ? 'Update Job' : 'Create Job'}
          </button>
        )}
      </div>
    </div>
  );
}
