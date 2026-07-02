import { useState } from 'react';
import { Plus, X, Trophy, Medal } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Candidate = { application_id: number; user_id: number; name: string; email: string; status: string; ats_score?: number; resume_match?: number; interview_score?: number; coding_score?: number; career_readiness?: number; overall_avg?: number; };

export default function RecruiterComparePage() {
  const [ids, setIds] = useState<string>('');
  const [result, setResult] = useState<{ candidates: Candidate[]; rankings: Record<string, string[]> } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCompare = async () => {
    const idList = ids.split(',').map(s => parseInt(s.trim())).filter(n => n > 0);
    if (idList.length < 2) { setError('Enter at least 2 application IDs separated by commas'); return; }
    if (idList.length > 5) { setError('Maximum 5 candidates for comparison'); return; }
    setError('');
    setLoading(true);
    try {
      const r = await recruiterApi.compare(idList);
      setResult(r.data);
    } catch (e: any) { setError(e.response?.data?.detail || 'Comparison failed'); }
    finally { setLoading(false); }
  };

  const fmt = (v: number | null | undefined) => v == null ? '-' : v.toFixed(1);

  return (
    <div>
      <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 1rem' }}>Compare Candidates</h3>
        <p style={{ color: 'var(--rp-muted)', fontSize: '0.85rem', margin: '0 0 1rem' }}>
          Enter application IDs separated by commas (2-5 candidates).
        </p>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label className="rp-label">Application IDs</label>
            <input className="rp-input" value={ids} onChange={e => setIds(e.target.value)} placeholder="1, 2, 3" />
          </div>
          <button className="rp-btn rp-btn--primary" onClick={handleCompare} disabled={loading}>
            {loading ? 'Comparing...' : 'Compare'}
          </button>
        </div>
        {error && <p style={{ color: 'var(--rp-danger)', fontSize: '0.85rem', margin: '0.5rem 0 0' }}>{error}</p>}
      </div>

      {result && result.candidates.length > 0 && (
        <>
          <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem' }}>Rankings</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              {Object.entries(result.rankings).map(([metric, names]) => (
                <div key={metric} style={{ padding: '0.75rem', background: 'var(--rp-bg)', borderRadius: 8 }}>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.8rem', color: 'var(--rp-muted)', textTransform: 'uppercase', fontWeight: 600 }}>{metric.replace(/_/g, ' ')}</p>
                  {names.map((name, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0' }}>
                      {i === 0 && <Trophy size={14} style={{ color: 'var(--rp-warning)' }} />}
                      {i === 1 && <Medal size={14} style={{ color: 'var(--rp-muted)' }} />}
                      <span style={{ fontSize: '0.85rem', fontWeight: i === 0 ? 600 : 400 }}>{name}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          <div className="rp-card">
            <h3 style={{ margin: '0 0 1rem' }}>Side-by-Side</h3>
            <div className="rp-table-wrap">
              <table className="rp-compare-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    {result.candidates.map(c => <th key={c.application_id}>{c.name}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: 'ats_score', label: 'ATS Score' },
                    { key: 'resume_match', label: 'Resume Match' },
                    { key: 'interview_score', label: 'Interview Score' },
                    { key: 'coding_score', label: 'Coding Score' },
                    { key: 'career_readiness', label: 'Career Readiness' },
                    { key: 'overall_avg', label: 'Overall Average' },
                  ].map(({ key, label }) => {
                    const vals = result.candidates.map(c => (c as any)[key] ?? -1);
                    const maxVal = Math.max(...vals);
                    return (
                      <tr key={key}>
                        <td style={{ fontWeight: 500 }}>{label}</td>
                        {result.candidates.map((c, i) => (
                          <td key={c.application_id} className={vals[i] === maxVal && maxVal >= 0 ? 'rp-compare-best' : ''}>
                            {fmt(vals[i] >= 0 ? vals[i] : null)}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                  <tr>
                    <td style={{ fontWeight: 500 }}>Status</td>
                    {result.candidates.map(c => <td key={c.application_id}><span className={`rp-badge rp-badge--${c.status}`}>{c.status?.replace(/_/g, ' ')}</span></td>)}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
