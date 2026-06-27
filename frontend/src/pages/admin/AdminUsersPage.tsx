import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Search, Ban, CheckCircle, Trash2, KeyRound } from 'lucide-react';

const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getUsers({ search, status: statusFilter, role: roleFilter });
      setUsers(res.data.users);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [search, statusFilter, roleFilter]);

  const toggleStatus = async (userId: number) => {
    try {
      await adminApi.toggleUserActive(userId);
      fetchUsers();
    } catch (error) {
      console.error('Failed to toggle status:', error);
      alert('Error updating user status');
    }
  };

  const deleteUser = async (userId: number) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    try {
      await adminApi.deleteUser(userId);
      fetchUsers();
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      alert(error.response?.data?.detail || 'Error deleting user');
    }
  };

  const resetPassword = async (userId: number) => {
    if (!window.confirm("Are you sure you want to reset this user's password?")) return;
    try {
      const res = await adminApi.resetUserPassword(userId);
      alert(`Password reset successfully.\nTemporary password: ${res.data.temp_password}\n\nPlease share this with the user.`);
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('Error resetting password');
    }
  };

  return (
    <div className="admin-card">
      <div className="admin-flex-between admin-mb-6">
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-muted)' }} />
          <input 
            type="text" 
            placeholder="Search users by name or email..." 
            className="admin-input"
            style={{ paddingLeft: '32px' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <select 
            className="admin-input" 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="disabled">Disabled</option>
          </select>
          <select 
            className="admin-input" 
            value={roleFilter} 
            onChange={(e) => setRoleFilter(e.target.value)}
          >
            <option value="">All Roles</option>
            <option value="candidate">Candidate</option>
            <option value="recruiter">Recruiter</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      <div className="admin-table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading users...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>User Details</th>
                <th>Role</th>
                <th>Status</th>
                <th>Interviews</th>
                <th>Avg Score</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length > 0 ? users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{user.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--admin-muted)' }}>{user.email}</div>
                  </td>
                  <td>
                    {user.is_admin ? (
                      <span className="admin-badge neutral">Admin</span>
                    ) : user.is_recruiter ? (
                      <span className="admin-badge primary">Recruiter</span>
                    ) : (
                      <span className="admin-badge">Candidate</span>
                    )}
                  </td>
                  <td>
                    {user.is_active ? (
                      <span className="admin-badge success">Active</span>
                    ) : (
                      <span className="admin-badge danger">Disabled</span>
                    )}
                  </td>
                  <td>{user.total_interviews}</td>
                  <td>{user.avg_score !== null ? user.avg_score.toFixed(1) : '-'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        className="admin-icon-btn" 
                        title={user.is_active ? "Disable User" : "Enable User"}
                        onClick={() => toggleStatus(user.id)}
                        disabled={user.is_admin}
                      >
                        {user.is_active ? <Ban size={16} color="var(--admin-warning)" /> : <CheckCircle size={16} color="var(--admin-success)" />}
                      </button>
                      <button 
                        className="admin-icon-btn" 
                        title="Reset Password"
                        onClick={() => resetPassword(user.id)}
                      >
                        <KeyRound size={16} />
                      </button>
                      <button 
                        className="admin-icon-btn" 
                        title="Delete User"
                        onClick={() => deleteUser(user.id)}
                        disabled={user.is_admin}
                      >
                        <Trash2 size={16} color="var(--admin-danger)" />
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center' }}>No users found matching criteria.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AdminUsersPage;
