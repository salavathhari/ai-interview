import React, { useState, useEffect } from 'react';
import { useToast } from '../components/ui/Toast';
import { usePreferences } from '../contexts/PreferencesContext';
import { userApi } from '../services/api';
import {
  User, Shield, Settings, AlertTriangle, Mail, Lock, Eye, EyeOff,
  CheckCircle2, Copy, Key, Bell, Volume2, Trash2, ArrowRight,
} from 'lucide-react';
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
  const { emailNotif, setEmailNotif, soundAlerts, setSoundAlerts } = usePreferences();
  const [activeTab, setActiveTab] = useState<Tab>('profile');

  const [profile, setProfile] = useState<Profile | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    return saved;
  });
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
    document.documentElement.setAttribute('data-theme', theme);
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
    if (profile?.is_admin) return { label: 'Admin', cls: 'role-admin', color: '#dc2626' };
    if (profile?.is_recruiter) return { label: 'Recruiter', cls: 'role-recruiter', color: '#16a34a' };
    return { label: 'Candidate', cls: 'role-candidate', color: '#2563eb' };
  };

  const getPwStrength = () => {
    const len = newPassword.length;
    if (len === 0) return { score: 0, label: '', color: '' };
    if (len < 8) return { score: 1, label: 'Weak', color: '#ef4444' };
    if (len < 12) return { score: 2, label: 'Fair', color: '#f59e0b' };
    return { score: 3, label: 'Strong', color: '#22c55e' };
  };

  const copyUserId = () => {
    if (profile) {
      navigator.clipboard.writeText(String(profile.id));
      toast('success', 'User ID copied');
    }
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode; desc: string }[] = [
    { id: 'profile', label: 'Profile', icon: <User size={18} />, desc: 'Personal information' },
    { id: 'security', label: 'Security', icon: <Shield size={18} />, desc: 'Password & access' },
    { id: 'preferences', label: 'Preferences', icon: <Settings size={18} />, desc: 'Appearance & alerts' },
    { id: 'danger', label: 'Danger Zone', icon: <AlertTriangle size={18} />, desc: 'Account actions' },
  ];

  const pwStrength = getPwStrength();
  const role = getRoleBadge();

  return (
    <div className="sp">
      {/* Header */}
      <header className="sp-header">
        <div className="sp-header-left">
          <span className="sp-eyebrow">Account</span>
          <h1>Settings</h1>
          <p>Manage your account settings and preferences</p>
        </div>
        {profile && (
          <div className="sp-profile-card">
            <div className="sp-avatar">
              {(profile.name || profile.email).charAt(0).toUpperCase()}
            </div>
            <div className="sp-profile-info">
              <span className="sp-profile-name">{profile.name || 'User'}</span>
              <span className="sp-profile-email">{profile.email}</span>
            </div>
            <span className="sp-role-pill" style={{ background: `${role.color}14`, color: role.color, border: `1px solid ${role.color}30` }}>
              {role.label}
            </span>
          </div>
        )}
      </header>

      <div className="sp-body">
        {/* Sidebar Tabs */}
        <nav className="sp-sidebar">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`sp-nav-item ${activeTab === tab.id ? 'active' : ''} ${tab.id === 'danger' ? 'danger' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="sp-nav-icon">{tab.icon}</span>
              <div className="sp-nav-text">
                <span className="sp-nav-label">{tab.label}</span>
                <span className="sp-nav-desc">{tab.desc}</span>
              </div>
              {activeTab === tab.id && <ArrowRight size={14} className="sp-nav-arrow" />}
            </button>
          ))}
        </nav>

        {/* Content */}
        <main className="sp-content">
          {/* ─── Profile Tab ─── */}
          {activeTab === 'profile' && (
            <section className="sp-section">
              <div className="sp-section-head">
                <div className="sp-section-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><User size={20} /></div>
                <div>
                  <h2>Profile Settings</h2>
                  <p>Update your personal information and manage your account details</p>
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h3>Personal Information</h3>
                  <p>Update your name and email address</p>
                </div>
                <form onSubmit={handleProfileSave} className="sp-form">
                  <div className="sp-field">
                    <label htmlFor="sp-name">
                      <User size={14} /> Full Name
                    </label>
                    <input
                      id="sp-name"
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      placeholder="Enter your full name"
                    />
                  </div>

                  <div className="sp-field">
                    <label htmlFor="sp-email">
                      <Mail size={14} /> Email Address
                    </label>
                    <input
                      id="sp-email"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="your@email.com"
                    />
                  </div>

                  {profileMsg && (
                    <div className={`sp-alert ${profileMsg.type}`}>
                      {profileMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                      {profileMsg.text}
                    </div>
                  )}

                  <div className="sp-form-footer">
                    <button type="submit" className="sp-btn sp-btn-primary" disabled={profileLoading}>
                      {profileLoading ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h3>Account Details</h3>
                  <p>Read-only information about your account</p>
                </div>
                <div className="sp-details-grid">
                  <div className="sp-detail-item">
                    <span className="sp-detail-label">User ID</span>
                    <div className="sp-detail-value">
                      <code>#{profile?.id}</code>
                      <button type="button" className="sp-copy-btn" onClick={copyUserId} title="Copy ID">
                        <Copy size={13} />
                      </button>
                    </div>
                  </div>
                  <div className="sp-detail-item">
                    <span className="sp-detail-label">Account Type</span>
                    <span className="sp-detail-value sp-role-tag" style={{ color: role.color, background: `${role.color}10` }}>{role.label}</span>
                  </div>
                  <div className="sp-detail-item">
                    <span className="sp-detail-label">Status</span>
                    <span className="sp-detail-value">
                      <span className="sp-status-dot" /> Active
                    </span>
                  </div>
                  <div className="sp-detail-item">
                    <span className="sp-detail-label">Joined</span>
                    <span className="sp-detail-value">
                      {profile ? new Date(profile.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : '---'}
                    </span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* ─── Security Tab ─── */}
          {activeTab === 'security' && (
            <section className="sp-section">
              <div className="sp-section-head">
                <div className="sp-section-icon" style={{ background: '#f0fdf4', color: '#16a34a' }}><Shield size={20} /></div>
                <div>
                  <h2>Security</h2>
                  <p>Keep your account secure by updating your password regularly</p>
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h3>Change Password</h3>
                  <p>Ensure your account uses a strong, unique password</p>
                </div>
                <form onSubmit={handlePasswordChange} className="sp-form">
                  <div className="sp-field">
                    <label htmlFor="sp-cur-pw">
                      <Lock size={14} /> Current Password
                    </label>
                    <div className="sp-input-group">
                      <input
                        id="sp-cur-pw"
                        type={showCurrentPw ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={e => setCurrentPassword(e.target.value)}
                        placeholder="Enter current password"
                        required
                      />
                      <button type="button" className="sp-input-icon" onClick={() => setShowCurrentPw(!showCurrentPw)}>
                        {showCurrentPw ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>

                  <div className="sp-field">
                    <label htmlFor="sp-new-pw">
                      <Key size={14} /> New Password
                    </label>
                    <div className="sp-input-group">
                      <input
                        id="sp-new-pw"
                        type={showNewPw ? 'text' : 'password'}
                        value={newPassword}
                        onChange={e => setNewPassword(e.target.value)}
                        placeholder="Minimum 8 characters"
                        required
                      />
                      <button type="button" className="sp-input-icon" onClick={() => setShowNewPw(!showNewPw)}>
                        {showNewPw ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                    {newPassword.length > 0 && (
                      <div className="sp-pw-strength">
                        <div className="sp-pw-bars">
                          {[1, 2, 3].map(i => (
                            <div
                              key={i}
                              className="sp-pw-bar"
                              style={{
                                background: i <= pwStrength.score ? pwStrength.color : '#e2e8f0',
                              }}
                            />
                          ))}
                        </div>
                        <span style={{ color: pwStrength.color }}>{pwStrength.label}</span>
                      </div>
                    )}
                  </div>

                  <div className="sp-field">
                    <label htmlFor="sp-confirm-pw">
                      <Lock size={14} /> Confirm New Password
                    </label>
                    <input
                      id="sp-confirm-pw"
                      type="password"
                      value={confirmPassword}
                      onChange={e => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter new password"
                      required
                    />
                    {confirmPassword && newPassword !== confirmPassword && (
                      <span className="sp-field-error">Passwords do not match</span>
                    )}
                  </div>

                  {passwordMsg && (
                    <div className={`sp-alert ${passwordMsg.type}`}>
                      {passwordMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                      {passwordMsg.text}
                    </div>
                  )}

                  <div className="sp-form-footer">
                    <button type="submit" className="sp-btn sp-btn-primary" disabled={passwordLoading}>
                      {passwordLoading ? 'Updating...' : 'Update Password'}
                    </button>
                  </div>
                </form>
              </div>

              <div className="sp-card sp-card-muted">
                <div className="sp-tips-head">
                  <Shield size={16} />
                  <h3>Password Tips</h3>
                </div>
                <ul className="sp-tips-list">
                  <li>Use at least 12 characters for a strong password</li>
                  <li>Mix uppercase, lowercase, numbers, and symbols</li>
                  <li>Avoid reusing passwords from other services</li>
                  <li>Consider using a password manager</li>
                </ul>
              </div>
            </section>
          )}

          {/* ─── Preferences Tab ─── */}
          {activeTab === 'preferences' && (
            <section className="sp-section">
              <div className="sp-section-head">
                <div className="sp-section-icon" style={{ background: '#f5f3ff', color: '#8b5cf6' }}><Settings size={20} /></div>
                <div>
                  <h2>Preferences</h2>
                  <p>Customize your experience and notification settings</p>
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h3>Appearance</h3>
                  <p>Choose the visual style for the platform</p>
                </div>
                <div className="sp-theme-grid">
                  {(['light', 'dark'] as const).map(t => (
                    <button
                      key={t}
                      type="button"
                      className={`sp-theme-card ${theme === t ? 'active' : ''}`}
                      onClick={() => {
                        setTheme(t);
                        document.documentElement.setAttribute('data-theme', t);
                        localStorage.setItem('theme', t);
                      }}
                    >
                      <div className={`sp-theme-preview ${t}`}>
                        <div className="sp-theme-bar" />
                        <div className="sp-theme-dots">
                          <span /><span /><span />
                        </div>
                      </div>
                      <span className="sp-theme-label">{t === 'light' ? 'Light Mode' : 'Dark Mode'}</span>
                      {theme === t && <CheckCircle2 size={16} className="sp-theme-check" />}
                    </button>
                  ))}
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h3>Notifications</h3>
                  <p>Control how you receive updates and alerts</p>
                </div>
                <div className="sp-pref-list">
                  <div className="sp-pref-row">
                    <div className="sp-pref-info">
                      <div className="sp-pref-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><Bell size={16} /></div>
                      <div>
                        <strong>Email Notifications</strong>
                        <p>Receive updates about interview results and new challenges</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      className={`sp-toggle ${emailNotif ? 'on' : ''}`}
                      onClick={() => setEmailNotif(!emailNotif)}
                      aria-label="Toggle email notifications"
                    >
                      <span className="sp-toggle-knob" />
                    </button>
                  </div>

                  <div className="sp-pref-row">
                    <div className="sp-pref-info">
                      <div className="sp-pref-icon" style={{ background: '#f5f3ff', color: '#8b5cf6' }}><Volume2 size={16} /></div>
                      <div>
                        <strong>Sound Alerts</strong>
                        <p>Play audio cues for timer warnings and interview events</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      className={`sp-toggle ${soundAlerts ? 'on' : ''}`}
                      onClick={() => setSoundAlerts(!soundAlerts)}
                      aria-label="Toggle sound alerts"
                    >
                      <span className="sp-toggle-knob" />
                    </button>
                  </div>
                </div>
              </div>

              {prefMsg && (
                <div className={`sp-alert ${prefMsg.type}`}>
                  <CheckCircle2 size={16} />
                  {prefMsg.text}
                </div>
              )}

              <div className="sp-form-footer">
                <button type="button" className="sp-btn sp-btn-primary" onClick={handlePrefSave}>
                  Save Preferences
                </button>
              </div>
            </section>
          )}

          {/* ─── Danger Zone Tab ─── */}
          {activeTab === 'danger' && (
            <section className="sp-section">
              <div className="sp-section-head">
                <div className="sp-section-icon" style={{ background: '#fef2f2', color: '#dc2626' }}><AlertTriangle size={20} /></div>
                <div>
                  <h2>Danger Zone</h2>
                  <p>Irreversible actions that affect your account permanently</p>
                </div>
              </div>

              <div className="sp-card sp-card-danger">
                <div className="sp-danger-header">
                  <div className="sp-danger-icon-wrap">
                    <Trash2 size={20} />
                  </div>
                  <div>
                    <h3>Deactivate Account</h3>
                    <p>This will immediately lock your account. All your data and interview history will be preserved but inaccessible.</p>
                  </div>
                </div>

                <div className="sp-danger-body">
                  <label htmlFor="sp-delete-confirm">
                    Type <code>DELETE</code> below to confirm deactivation
                  </label>
                  <input
                    id="sp-delete-confirm"
                    type="text"
                    value={deleteConfirm}
                    onChange={e => setDeleteConfirm(e.target.value)}
                    placeholder="Type DELETE to confirm"
                    className="sp-danger-input"
                  />
                </div>

                <button
                  type="button"
                  className="sp-btn sp-btn-danger"
                  disabled={deleteConfirm !== 'DELETE' || dangerLoading}
                  onClick={handleDeleteAccount}
                >
                  <Trash2 size={15} />
                  {dangerLoading ? 'Deactivating...' : 'Deactivate My Account'}
                </button>
              </div>

              <div className="sp-card sp-card-warning">
                <div className="sp-tips-head">
                  <AlertTriangle size={16} />
                  <h3>Before you proceed</h3>
                </div>
                <ul className="sp-tips-list">
                  <li>All active interview sessions will be terminated</li>
                  <li>Your interview history and reports will be preserved</li>
                  <li>You will be logged out immediately after deactivation</li>
                  <li>To restore your account, contact the platform administrator</li>
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
