import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Save, RefreshCw } from 'lucide-react';

const AdminSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await adminApi.getSettings();
      setSettings(res.data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await adminApi.updateSettings(settings);
      setSettings(res.data);
      alert('Settings updated successfully');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const val = type === 'checkbox' ? (e.target as HTMLInputElement).checked : 
                type === 'number' ? Number(value) : value;
    
    setSettings((prev: any) => ({ ...prev, [name]: val }));
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading settings...</div>;
  if (!settings) return <div className="admin-card">Error loading settings.</div>;

  return (
    <div className="admin-grid-2">
      <div className="admin-card">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', fontWeight: 600 }}>Platform Configuration</h2>
        
        <form onSubmit={handleSave}>
          <div className="admin-form-group">
            <label className="admin-label">Platform Name</label>
            <input 
              type="text" 
              name="platform_name" 
              className="admin-input" 
              value={settings.platform_name} 
              onChange={handleChange}
              required
            />
          </div>

          <div className="admin-form-group">
            <label className="admin-label">Max Interviews per User</label>
            <input 
              type="number" 
              name="max_interviews_per_user" 
              className="admin-input" 
              value={settings.max_interviews_per_user} 
              onChange={handleChange}
              min="1"
              required
            />
          </div>

          <div className="admin-form-group">
            <label className="admin-label">Max Tokens per Interview (API Limit)</label>
            <input 
              type="number" 
              name="max_tokens_per_interview" 
              className="admin-input" 
              value={settings.max_tokens_per_interview} 
              onChange={handleChange}
              min="1000"
              step="1000"
              required
            />
          </div>

          <div className="admin-form-group">
            <label className="admin-label">Default AI Model</label>
            <select 
              name="ai_model" 
              className="admin-input" 
              value={settings.ai_model} 
              onChange={handleChange}
            >
              <option value="gemini-2.0-flash">Gemini 2.0 Flash (Fast & Cheap)</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="claude-3-haiku">Claude 3 Haiku</option>
            </select>
          </div>

          <div className="admin-form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '2rem' }}>
            <input 
              type="checkbox" 
              name="voice_enabled" 
              id="voice_enabled"
              checked={settings.voice_enabled} 
              onChange={handleChange}
              style={{ width: '18px', height: '18px', accentColor: 'var(--admin-primary)' }}
            />
            <label htmlFor="voice_enabled" style={{ cursor: 'pointer', fontWeight: 500 }}>Enable Voice Interviews Platform-wide</label>
          </div>

          <div className="admin-form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--admin-warning-bg)', borderRadius: '0.5rem', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
            <input 
              type="checkbox" 
              name="maintenance_mode" 
              id="maintenance_mode"
              checked={settings.maintenance_mode} 
              onChange={handleChange}
              style={{ width: '18px', height: '18px', accentColor: 'var(--admin-warning)' }}
            />
            <label htmlFor="maintenance_mode" style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--admin-warning)' }}>
              Maintenance Mode (Disables login for non-admins)
            </label>
          </div>

          <div style={{ marginTop: '2.5rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="admin-btn primary" disabled={saving}>
              {saving ? <RefreshCw size={18} className="spin" /> : <Save size={18} />}
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      </div>

      <div className="admin-card">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', fontWeight: 600 }}>Danger Zone</h2>
        <div style={{ border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '0.5rem', padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--admin-danger)' }}>Purge Analytics Data</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--admin-muted)', marginBottom: '1rem' }}>
            Permanently delete all anonymous tracking and AI usage logs older than 90 days. This will free up database space but reduce historical chart data.
          </p>
          <button className="admin-btn danger">Purge Old Logs</button>
          
          <div style={{ margin: '2rem 0', height: '1px', backgroundColor: 'var(--admin-border)' }}></div>
          
          <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--admin-danger)' }}>Reset AI Quotas</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--admin-muted)', marginBottom: '1rem' }}>
            Reset the API usage tokens and cost trackers back to zero for the current billing cycle.
          </p>
          <button className="admin-btn outline" style={{ color: 'var(--admin-danger)', borderColor: 'rgba(239, 68, 68, 0.5)' }}>Reset Quotas</button>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}} />
    </div>
  );
};

export default AdminSettingsPage;
