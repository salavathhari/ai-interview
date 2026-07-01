import { useAuth } from '../../contexts/AuthContext';
import { User, Mail, Shield } from 'lucide-react';
import './recruiter.css';

export default function RecruiterSettingsPage() {
  const { user, role } = useAuth();
  const displayName = user?.name || 'Recruiter';
  const displayEmail = user?.email || '';
  const initials = displayName.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);

  return (
    <div style={{ maxWidth: 600 }}>
      <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '1.5rem' }}>
          <div className="rp-avatar rp-avatar--lg">{initials}</div>
          <div>
            <h2 style={{ margin: 0 }}>{displayName}</h2>
            <p style={{ color: 'var(--rp-muted)', margin: '0.25rem 0' }}>{displayEmail}</p>
            <span className="rp-badge rp-badge--open">Recruiter</span>
          </div>
        </div>
      </div>

      <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ margin: '0 0 1rem' }}>Profile Information</h3>
        <div className="rp-field">
          <label className="rp-label"><User size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} /> Name</label>
          <input className="rp-input" value={displayName} readOnly />
        </div>
        <div className="rp-field">
          <label className="rp-label"><Mail size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} /> Email</label>
          <input className="rp-input" value={displayEmail} readOnly />
        </div>
        <div className="rp-field">
          <label className="rp-label"><Shield size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} /> Role</label>
          <input className="rp-input" value="Recruiter" readOnly />
        </div>
      </div>

      <div className="rp-card">
        <h3 style={{ margin: '0 0 1rem' }}>Account</h3>
        <p style={{ color: 'var(--rp-muted)', fontSize: '0.85rem', margin: 0 }}>
          Contact your administrator to update account details, change password, or manage permissions.
        </p>
      </div>
    </div>
  );
}
