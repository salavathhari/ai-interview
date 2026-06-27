import React, { useState, useEffect } from 'react';
import { useToast } from '../components/ui/Toast';
import { userApi } from '../services/api';
import './SettingsPage.css';

type Tab = 'profile' | 'security' | 'preferences' | 'danger';

interface Profile {
  id: number;
  name: string;
  email: string;
  is_admin: boolean;
  is_recruiter: boolean;
  created_at: string;
}

const SettingsPage: React.FC = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('profile');

  const [profile, setProfile] = useState<Profile | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem('theme') as 'light' | 'dark') || 'light');
  const [emailNotif, setEmailNotif] = useState(() => localStorage.getItem('emailNotif') !== 'false');
  const [soundAlerts, setSoundAlerts] = useState(() => localStorage.getItem('soundAlerts') !== 'false');
  const [prefMsg, setPrefMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [dangerLoading, setDangerLoading] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const res = await userApi.getProfile();
      setProfile(res.data);
      setName(res.data.name || '');
      setEmail(res.data.email || '');
    } catch {
      toast('error', 'Failed to load profile');
    }
  };

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileMsg(null);
    try {
      const res = await userApi.updateProfile({ name, email });
      setProfile(res.data);
      setProfileMsg({ type: 'success', text: 'Profile updated successfully.' });
      toast('success', 'Profile updated');
    } catch (err: any) {
      setProfileMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to update profile.' });
      toast('error', err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'Password must be at least 8 characters.' });
      return;
    }
    setPasswordLoading(true);
    try {
      await userApi.changePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordMsg({ type: 'success', text: 'Password changed successfully.' });
      toast('success', 'Password changed');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPasswordMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to change password.' });
      toast('error', err.response?.data?.detail || 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handlePrefSave = () => {
    localStorage.setItem('theme', theme);
    localStorage.setItem('emailNotif', String(emailNotif));
    localStorage.setItem('soundAlerts', String(soundAlerts));
    setPrefMsg({ type: 'success', text: 'Preferences saved.' });
    toast('success', 'Preferences saved');
    setTimeout(() => setPrefMsg(null), 3000);
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== 'DELETE') return;
    setDangerLoading(true);
    try {
      await userApi.deleteAccount();
      localStorage.clear();
      window.location.href = '/';
    } catch (err: any) {
      toast('error', err.response?.data?.detail || 'Failed to delete account');
    } finally {
      setDangerLoading(false);
    }
  };

  const getRoleBadge = () => {
    if (profile?.is_admin) return { label: 'Admin', cls: 'role-admin' };
    if (profile?.is_recruiter) return { label: 'Recruiter', cls: 'role-recruiter' };
    return { label: 'Candidate', cls: 'role-candidate' };
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'profile', label: 'Profile', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> },
    { id: 'security', label: 'Security', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg> },
    { id: 'preferences', label: 'Preferences', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg> },
    { id: 'danger', label: 'Danger Zone', icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> },
  ];

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div>
          <h1>Settings</h1>
          <p className="settings-header-sub">Manage your account and preferences</p>
        </div>
        {profile && (
          <div className="settings-user-badge">
            <div className="settings-avatar-sm">
              {(profile.name || profile.email).charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="settings-user-name">{profile.name || 'User'}</p>
              <span className={`settings-role-badge ${getRoleBadge().cls}`}>{getRoleBadge().label}</span>
            </div>
          </div>
        )}
      </div>

      <div className="settings-layout">
        <nav className="settings-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`settings-tab ${activeTab === tab.id ? 'active' : ''} ${tab.id === 'danger' ? 'danger' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="settings-tab-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>

        <main className="settings-content">
          {activeTab === 'profile' && (
            <section className="settings-section">
              <div className="settings-section-header">
                <h2>Profile Settings</h2>
                <p>Manage your name and email address.</p>
              </div>

              <form onSubmit={handleProfileSave} className="settings-form">
                <div className="settings-form-group">
                  <label htmlFor="settings-name">Full Name</label>
                  <input
                    id="settings-name"
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Your full name"
                  />
                </div>

                <div className="settings-form-group">
                  <label htmlFor="settings-email">Email Address</label>
                  <input
                    id="settings-email"
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="your@email.com"
                  />
                </div>

                {profileMsg && (
                  <div className={`settings-msg ${profileMsg.type}`}>{profileMsg.text}</div>
                )}

                <div className="settings-form-actions">
                  <button type="submit" className="settings-btn-primary" disabled={profileLoading}>
                    {profileLoading ? 'Saving...' : 'Save Profile'}
                  </button>
                </div>
              </form>

              <div className="settings-info-card">
                <h3>Account Information</h3>
                <div className="settings-info-grid">
                  <div><span>User ID</span><strong>#{profile?.id}</strong></div>
                  <div><span>Account Type</span><strong>{getRoleBadge().label}</strong></div>
                  <div><span>Status</span><strong className="status-active">Active</strong></div>
                  <div><span>Joined</span><strong>{profile ? new Date(profile.created_at).toLocaleDateString() : '---'}</strong></div>
                </div>
              </div>
            </section>
          )}

          {activeTab === 'security' && (
            <section className="settings-section">
              <div className="settings-section-header">
                <h2>Security</h2>
                <p>Keep your account secure by updating your password regularly.</p>
              </div>

              <form onSubmit={handlePasswordChange} className="settings-form">
                <div className="settings-form-group">
                  <label htmlFor="current-password">Current Password</label>
                  <input
                    id="current-password"
                    type="password"
                    value={currentPassword}
                    onChange={e => setCurrentPassword(e.target.value)}
                    placeholder="Enter your current password"
                    required
                  />
                </div>

                <div className="settings-form-group">
                  <label htmlFor="new-password">New Password</label>
                  <input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    required
                  />
                  <div className="password-strength">
                    {[1, 2, 3, 4].map(i => (
                      <div
                        key={i}
                        className={`strength-bar ${newPassword.length >= i * 4 ? (newPassword.length >= 12 ? 'strong' : 'medium') : ''}`}
                      />
                    ))}
                    <span>{newPassword.length === 0 ? '' : newPassword.length < 8 ? 'Weak' : newPassword.length < 12 ? 'Fair' : 'Strong'}</span>
                  </div>
                </div>

                <div className="settings-form-group">
                  <label htmlFor="confirm-password">Confirm New Password</label>
                  <input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    required
                  />
                  {confirmPassword && newPassword !== confirmPassword && (
                    <p className="field-error">Passwords do not match</p>
                  )}
                </div>

                {passwordMsg && (
                  <div className={`settings-msg ${passwordMsg.type}`}>{passwordMsg.text}</div>
                )}

                <div className="settings-form-actions">
                  <button type="submit" className="settings-btn-primary" disabled={passwordLoading}>
                    {passwordLoading ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </form>

              <div className="settings-tip-card">
                <h3>Password Tips</h3>
                <ul>
                  <li>Use at least 12 characters for a strong password.</li>
                  <li>Mix uppercase, lowercase, numbers, and symbols.</li>
                  <li>Avoid reusing passwords from other services.</li>
                </ul>
              </div>
            </section>
          )}

          {activeTab === 'preferences' && (
            <section className="settings-section">
              <div className="settings-section-header">
                <h2>Preferences</h2>
                <p>Customize your interview experience.</p>
              </div>

              <div className="settings-form">
                <div className="settings-pref-card">
                  <div>
                    <strong>Theme</strong>
                    <p>Choose the visual style for the platform.</p>
                  </div>
                  <div className="theme-toggle-group">
                    {(['light', 'dark'] as const).map(t => (
                      <button
                        key={t}
                        type="button"
                        className={`theme-btn ${theme === t ? 'active' : ''}`}
                        onClick={() => setTheme(t)}
                      >
                        {t === 'light' ? 'Light' : 'Dark'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="settings-pref-card">
                  <div>
                    <strong>Email Notifications</strong>
                    <p>Receive updates about your interview results and new challenges.</p>
                  </div>
                  <button
                    type="button"
                    className={`toggle-switch ${emailNotif ? 'on' : 'off'}`}
                    onClick={() => setEmailNotif(v => !v)}
                    aria-label="Toggle email notifications"
                  >
                    <span className="toggle-knob" />
                  </button>
                </div>

                <div className="settings-pref-card">
                  <div>
                    <strong>Sound Alerts</strong>
                    <p>Play audio cues for timer warnings and interview events.</p>
                  </div>
                  <button
                    type="button"
                    className={`toggle-switch ${soundAlerts ? 'on' : 'off'}`}
                    onClick={() => setSoundAlerts(v => !v)}
                    aria-label="Toggle sound alerts"
                  >
                    <span className="toggle-knob" />
                  </button>
                </div>

                {prefMsg && (
                  <div className={`settings-msg ${prefMsg.type}`}>{prefMsg.text}</div>
                )}

                <div className="settings-form-actions">
                  <button type="button" className="settings-btn-primary" onClick={handlePrefSave}>
                    Save Preferences
                  </button>
                </div>
              </div>
            </section>
          )}

          {activeTab === 'danger' && (
            <section className="settings-section">
              <div className="settings-section-header">
                <h2>Danger Zone</h2>
                <p>Irreversible actions that affect your account permanently.</p>
              </div>

              <div className="danger-zone-card">
                <div className="danger-zone-header">
                  <span className="danger-icon">!</span>
                  <div>
                    <h3>Deactivate Account</h3>
                    <p>This will immediately lock your account. All your data and interview history will be preserved but inaccessible. Contact support to restore access.</p>
                  </div>
                </div>

                <div className="danger-confirm-area">
                  <label htmlFor="delete-confirm">
                    To confirm, type <code>DELETE</code> in the box below:
                  </label>
                  <input
                    id="delete-confirm"
                    type="text"
                    value={deleteConfirm}
                    onChange={e => setDeleteConfirm(e.target.value)}
                    placeholder="Type DELETE to confirm"
                    className="danger-input"
                  />
                </div>

                <button
                  type="button"
                  className="settings-btn-danger"
                  disabled={deleteConfirm !== 'DELETE' || dangerLoading}
                  onClick={handleDeleteAccount}
                >
                  {dangerLoading ? 'Deactivating...' : 'Deactivate My Account'}
                </button>
              </div>

              <div className="settings-tip-card warning">
                <h3>Before you proceed</h3>
                <ul>
                  <li>All active interview sessions will be terminated.</li>
                  <li>Your interview history and reports will be preserved.</li>
                  <li>You will be logged out immediately after deactivation.</li>
                  <li>To restore your account, contact the platform administrator.</li>
                </ul>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default SettingsPage;
