import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Search, Download, Trash2 } from 'lucide-react';

const AdminReportsPage: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getReports({ search });
      setReports(res.data.reports);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [search]);

  const deleteReport = async (sessionId: number) => {
    if (!window.confirm('Are you sure you want to delete this report? The interview session will be permanently removed.')) return;
    try {
      await adminApi.deleteReport(sessionId);
      fetchReports();
    } catch (error) {
      console.error('Failed to delete report:', error);
      alert('Error deleting report');
    }
  };

  return (
    <div className="admin-card">
      <div className="admin-flex-between admin-mb-6">
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-muted)' }} />
          <input 
            type="text" 
            placeholder="Search candidate reports..." 
            className="admin-input"
            style={{ paddingLeft: '32px' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="admin-table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading reports...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Role</th>
                <th>Type</th>
                <th>Score</th>
                <th>Generated At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.length > 0 ? reports.map((report) => (
                <tr key={report.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{report.candidate_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--admin-muted)' }}>{report.candidate_email}</div>
                  </td>
                  <td>{report.role}</td>
                  <td>{report.interview_type}</td>
                  <td>{report.score !== null ? report.score.toFixed(1) : '-'}</td>
                  <td>{new Date(report.generated_at).toLocaleString()}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        className="admin-btn outline" 
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => window.open(`/report/${report.id}`, '_blank')}
                      >
                        <Download size={14} style={{ color: 'var(--admin-text)' }} />
                        View
                      </button>
                      <button 
                        className="admin-btn outline" 
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', borderColor: 'rgba(239, 68, 68, 0.5)' }}
                        onClick={() => deleteReport(report.id)}
                      >
                        <Trash2 size={14} style={{ color: 'var(--admin-danger)' }} />
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center' }}>No reports found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AdminReportsPage;
