import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  User, Settings, LogOut, ChevronDown, LayoutDashboard,
  Play, Code2, FileText, BarChart3, Brain,
  Briefcase, FileCheck, Zap, FileSearch, Map, CheckCircle,
  Users, Shield, FileBarChart
} from 'lucide-react';
import './AppLayout.css';

const NAV_SECTIONS = [
  {
    label: 'Main',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/interview-setup', label: 'New Interview', icon: Play },
      { path: '/coding', label: 'Coding', icon: Code2 },
      { path: '/resume', label: 'Resumes', icon: FileText },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { path: '/analytics', label: 'Analytics', icon: BarChart3 },
      { path: '/reports', label: 'Reports', icon: FileBarChart },
      { path: '/ml-insights', label: 'ML Insights', icon: Brain },
    ],
  },
  {
    label: 'Career',
    items: [
      { path: '/career/dashboard', label: 'Career Hub', icon: Briefcase },
      { path: '/career/ats-report', label: 'ATS Report', icon: FileCheck },
      { path: '/career/skill-gap', label: 'Skill Gap', icon: Zap },
      { path: '/career/resume-optimizer', label: 'Resume Optimizer', icon: FileSearch },
      { path: '/career/learning-roadmap', label: 'Roadmap', icon: Map },
      { path: '/career/readiness', label: 'Readiness', icon: CheckCircle },
    ],
  },
];

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, role, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  const displayName = user?.name || 'User';
  const displayEmail = user?.email || '';
  const initials = displayName.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    navigate('/login');
  };

  const roleLabel = role === 'admin' ? 'Admin' : role === 'recruiter' ? 'Recruiter' : 'Candidate';

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
              <span className="app-sidebar__brand-role">{roleLabel} Portal</span>
            </div>
          )}
        </div>

        <nav className="app-sidebar__nav">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="app-sidebar__section">
              {!collapsed && <p className="app-sidebar__section-label">{section.label}</p>}
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.path}
                    type="button"
                    className={`app-sidebar__item ${isActive(item.path) ? 'app-sidebar__item--active' : ''}`}
                    onClick={() => { navigate(item.path); setMobileOpen(false); }}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon size={18} />
                    {!collapsed && <span>{item.label}</span>}
                  </button>
                );
              })}
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
                <Users size={18} />
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
                <Shield size={18} />
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
            <Settings size={18} />
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
            <div className="app-header__user-wrapper" ref={menuRef}>
              <button
                type="button"
                className={`app-header__user ${menuOpen ? 'app-header__user--open' : ''}`}
                onClick={() => setMenuOpen(!menuOpen)}
              >
                <div className="app-header__avatar">{initials}</div>
                <span className="app-header__name">{displayName}</span>
                <ChevronDown size={14} className={`app-header__chevron ${menuOpen ? 'app-header__chevron--open' : ''}`} />
              </button>

              {menuOpen && (
                <div className="app-header__dropdown">
                  <div className="app-header__dropdown-header">
                    <div className="app-header__dropdown-avatar">{initials}</div>
                    <div className="app-header__dropdown-info">
                      <span className="app-header__dropdown-name">{displayName}</span>
                      <span className="app-header__dropdown-email">{displayEmail}</span>
                      <span className={`app-header__dropdown-role app-header__dropdown-role--${role}`}>{roleLabel}</span>
                    </div>
                  </div>
                  <div className="app-header__dropdown-divider" />
                  <button
                    type="button"
                    className="app-header__dropdown-item"
                    onClick={() => { setMenuOpen(false); navigate('/settings'); }}
                  >
                    <User size={16} />
                    <span>Profile</span>
                  </button>
                  <div className="app-header__dropdown-divider" />
                  <button
                    type="button"
                    className="app-header__dropdown-item app-header__dropdown-item--danger"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} />
                    <span>Log out</span>
                  </button>
                </div>
              )}
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
