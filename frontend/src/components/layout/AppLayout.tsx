import React, { useState } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './AppLayout.css';

const NAV_SECTIONS = [
  {
    label: 'Main',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1' },
      { path: '/interview-setup', label: 'New Interview', icon: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
      { path: '/coding', label: 'Coding', icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' },
      { path: '/resume', label: 'Resumes', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { path: '/analytics', label: 'Analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
      { path: '/reports', label: 'Reports', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
      { path: '/ml-insights', label: 'ML Insights', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
    ],
  },
  {
    label: 'Career',
    items: [
      { path: '/career/dashboard', label: 'Career Hub', icon: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
      { path: '/career/ats-report', label: 'ATS Report', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
      { path: '/career/skill-gap', label: 'Skill Gap', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
      { path: '/career/resume-optimizer', label: 'Resume Optimizer', icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' },
      { path: '/career/learning-roadmap', label: 'Roadmap', icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7' },
      { path: '/career/readiness', label: 'Readiness', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
    ],
  },
];

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, role, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  const displayName = user?.name || localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user') || '{}').name || 'User' : 'User';
  const initials = displayName.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`app-layout ${collapsed ? 'app-layout--collapsed' : ''}`}>
      {/* Mobile overlay */}
      {mobileOpen && <div className="app-layout__overlay" onClick={() => setMobileOpen(false)} />}

      {/* Sidebar */}
      <aside className={`app-sidebar ${mobileOpen ? 'app-sidebar--open' : ''}`}>
        <div className="app-sidebar__brand">
          <div className="app-sidebar__brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          {!collapsed && (
            <div className="app-sidebar__brand-text">
              <span className="app-sidebar__brand-name">Interview Studio</span>
              <span className="app-sidebar__brand-role">{role === 'admin' ? 'Admin Portal' : role === 'recruiter' ? 'Recruiter Portal' : 'Candidate Portal'}</span>
            </div>
          )}
        </div>

        <nav className="app-sidebar__nav">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="app-sidebar__section">
              {!collapsed && <p className="app-sidebar__section-label">{section.label}</p>}
              {section.items.map((item) => (
                <button
                  key={item.path}
                  type="button"
                  className={`app-sidebar__item ${isActive(item.path) ? 'app-sidebar__item--active' : ''}`}
                  onClick={() => { navigate(item.path); setMobileOpen(false); }}
                  title={collapsed ? item.label : undefined}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d={item.icon} />
                  </svg>
                  {!collapsed && <span>{item.label}</span>}
                </button>
              ))}
            </div>
          ))}

          {(role === 'recruiter' || role === 'admin') && (
            <div className="app-sidebar__section">
              {!collapsed && <p className="app-sidebar__section-label">Recruiter</p>}
              <button
                type="button"
                className={`app-sidebar__item ${isActive('/recruiter') ? 'app-sidebar__item--active' : ''}`}
                onClick={() => { navigate('/recruiter'); setMobileOpen(false); }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
                </svg>
                {!collapsed && <span>Pipeline</span>}
              </button>
            </div>
          )}

          {role === 'admin' && (
            <div className="app-sidebar__section">
              {!collapsed && <p className="app-sidebar__section-label">Admin</p>}
              <button
                type="button"
                className={`app-sidebar__item ${isActive('/admin') ? 'app-sidebar__item--active' : ''}`}
                onClick={() => { navigate('/admin/dashboard'); setMobileOpen(false); }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                {!collapsed && <span>Admin Panel</span>}
              </button>
            </div>
          )}
        </nav>

        <div className="app-sidebar__footer">
          <button
            type="button"
            className={`app-sidebar__item ${isActive('/settings') ? 'app-sidebar__item--active' : ''}`}
            onClick={() => { navigate('/settings'); setMobileOpen(false); }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
            </svg>
            {!collapsed && <span>Settings</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="app-layout__main">
        {/* Top header */}
        <header className="app-header">
          <div className="app-header__left">
            <button type="button" className="app-header__menu-btn" onClick={() => setMobileOpen(!mobileOpen)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></svg>
            </button>
            <button type="button" className="app-header__collapse-btn" onClick={() => setCollapsed(!collapsed)}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transform: collapsed ? 'rotate(180deg)' : undefined }}>
                <polyline points="11 17 6 12 11 7" /><polyline points="18 17 13 12 18 7" />
              </svg>
            </button>
          </div>

          <div className="app-header__right">
            <div className="app-header__user" onClick={handleLogout} title="Click to logout">
              <div className="app-header__avatar">{initials}</div>
              <span className="app-header__name">{displayName}</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="app-layout__content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
