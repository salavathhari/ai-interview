import { useEffect, useState } from 'react';
import { FileText, Download, RefreshCw, FileBarChart } from 'lucide-react';
import { reportsApi, recruiterApi } from '../../services/api';
import './recruiter.css';

type Report = { id: number; title: string; report_type: string; status: string; created_at: string; is_outdated: boolean; };

export default function RecruiterReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = () => { setLoading(true); reportsApi.list().then(r => setReports(r.data.reports || [])).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(() => { fetchReports(); }, []);

  const handleDownload = async (id: number) => {
    try {
      const r = await reportsApi.download(id, 'pdf');
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url; a.download = `report-${id}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch {}
  };

  const handleDownloadHiringReport = async () => {
    try {
      const r = await recruiterApi.downloadHiringReport();
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url; a.download = 'hiring-report.pdf'; a.click();
      URL.revokeObjectURL(url);
    } catch {}
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <p style={{ color: 'var(--rp-muted)', margin: 0 }}>{reports.length} report{reports.length !== 1 ? 's' : ''}</p>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="rp-btn rp-btn--primary rp-btn--sm" onClick={handleDownloadHiringReport}><FileBarChart size={14} /> Download Hiring Report</button>
          <button className="rp-btn rp-btn--secondary rp-btn--sm" onClick={fetchReports}><RefreshCw size={14} /> Refresh</button>
        </div>
      </div>

      {loading ? [1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 60, marginBottom: 8 }} />) : reports.length === 0 ? (
        <div className="rp-card rp-empty"><div className="rp-empty-icon"><FileText size={24} /></div><h3>No reports yet</h3><p>Reports will be generated as you use the platform.</p></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {reports.map(r => (
            <div key={r.id} className="rp-card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <FileText size={18} style={{ color: 'var(--rp-primary)' }} />
                <div>
                  <strong style={{ fontSize: '0.9rem' }}>{r.title || r.report_type}</strong>
                  <div style={{ fontSize: '0.8rem', color: 'var(--rp-muted)' }}>{new Date(r.created_at).toLocaleDateString()} {r.is_outdated && <span className="rp-badge rp-badge--pending" style={{ marginLeft: 8 }}>Outdated</span>}</div>
                </div>
              </div>
              <button className="rp-btn rp-btn--ghost rp-btn--sm" onClick={() => handleDownload(r.id)}><Download size={14} /></button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
