import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Search, CheckCircle, XCircle } from 'lucide-react';

const AdminRecruitersPage: React.FC = () => {
  const [recruiters, setRecruiters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchRecruiters = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getRecruiters({ search });
      setRecruiters(res.data.recruiters);
    } catch (error) {
      console.error('Failed to fetch recruiters:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecruiters();
  }, [search]);

  const approveRecruiter = async (id: number) => {
    try {
      await adminApi.approveRecruiter(id);
      fetchRecruiters();
    } catch (error) {
      console.error('Failed to approve:', error);
    }
  };

  const rejectRecruiter = async (id: number) => {
    try {
      await adminApi.rejectRecruiter(id);
      fetchRecruiters();
    } catch (error) {
      console.error('Failed to reject:', error);
    }
  };

  return (
    <div className="admin-card">
      <div className="admin-flex-between admin-mb-6">
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-muted)' }} />
          <input 
            type="text" 
            placeholder="Search recruiters..." 
            className="admin-input"
            style={{ paddingLeft: '32px' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="admin-table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading recruiters...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Recruiter</th>
                <th>Status</th>
                <th>Active Jobs</th>
                <th>Candidates Processed</th>
                <th>Interviews Conducted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recruiters.length > 0 ? recruiters.map((recruiter) => (
                <tr key={recruiter.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{recruiter.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--admin-muted)' }}>{recruiter.email}</div>
                  </td>
                  <td>
                    {recruiter.is_active ? (
                      <span className="admin-badge success">Approved</span>
                    ) : (
                      <span className="admin-badge warning">Pending / Rejected</span>
                    )}
                  </td>
                  <td>{recruiter.total_jobs}</td>
                  <td>{recruiter.total_candidates}</td>
                  <td>{recruiter.interviews_conducted}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        className="admin-btn outline" 
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => approveRecruiter(recruiter.id)}
                        disabled={recruiter.is_active}
                      >
                        <CheckCircle size={14} style={{ color: 'var(--admin-success)' }} />
                        Approve
                      </button>
                      <button 
                        className="admin-btn outline" 
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => rejectRecruiter(recruiter.id)}
                        disabled={!recruiter.is_active}
                      >
                        <XCircle size={14} style={{ color: 'var(--admin-danger)' }} />
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center' }}>No recruiters found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AdminRecruitersPage;
