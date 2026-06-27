import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Search } from 'lucide-react';

const AdminInterviewsPage: React.FC = () => {
  const [interviews, setInterviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const fetchInterviews = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getInterviews({ 
        search, 
        status: statusFilter,
        interview_type: typeFilter
      });
      setInterviews(res.data.interviews);
    } catch (error) {
      console.error('Failed to fetch interviews:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterviews();
  }, [search, statusFilter, typeFilter]);

  const getStatusBadge = (status: string) => {
    if (status === 'completed') return 'success';
    if (status === 'in-progress') return 'warning';
    return 'neutral';
  };

  return (
    <div className="admin-card">
      <div className="admin-flex-between admin-mb-6">
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-muted)' }} />
          <input 
            type="text" 
            placeholder="Search candidates or roles..." 
            className="admin-input"
            style={{ paddingLeft: '32px' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <select 
            className="admin-input" 
            value={typeFilter} 
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="Technical">Technical</option>
            <option value="Voice">Voice</option>
          </select>
          <select 
            className="admin-input" 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="in-progress">In Progress</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      <div className="admin-table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading interviews...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Role</th>
                <th>Type</th>
                <th>Score</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {interviews.length > 0 ? interviews.map((interview) => (
                <tr key={interview.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{interview.candidate_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--admin-muted)' }}>{interview.candidate_email}</div>
                  </td>
                  <td>{interview.role}</td>
                  <td>{interview.interview_type}</td>
                  <td>{interview.score !== null ? interview.score.toFixed(1) : '-'}</td>
                  <td>{interview.duration_minutes !== null ? `${interview.duration_minutes} min` : '-'}</td>
                  <td>
                    <span className={`admin-badge ${getStatusBadge(interview.status)}`}>
                      {interview.status}
                    </span>
                  </td>
                  <td>{new Date(interview.started_at).toLocaleString()}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center' }}>No interviews found matching criteria.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AdminInterviewsPage;
