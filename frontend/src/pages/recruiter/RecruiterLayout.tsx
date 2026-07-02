import React from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Briefcase, Users, GitCompare, Video, Code2,
  Bell, Settings, LineChart, FileText, LogOut, Menu
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL, getAccessToken } from '../../services/api';
import './recruiter.css';

const RecruiterLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getAccessToken()}` },
      }).catch(() => {});
    } finally {
      logout();
      navigate('/login');
    }
  };

  const navGroups = [
    {
      title: 'Overview',
      items: [
        { name: 'Dashboard', path: '/recruiter/dashboard', icon: <LayoutDashboard size={18} /> },
        { name: 'Analytics', path: '/recruiter/analytics', icon: <LineChart size={18} /> },
        { name: 'Reports', path: '/recruiter/reports', icon: <FileText size={18} /> },
      ]
    },
    {
      title: 'Hiring',
      items: [
        { name: 'Jobs', path: '/recruiter/jobs', icon: <Briefcase size={18} /> },
        { name: 'Applications', path: '/recruiter/applications', icon: <Users size={18} /> },
        { name: 'Compare', path: '/recruiter/compare', icon: <GitCompare size={18} /> },
      ]
    },
    {
      title: 'Assessments',
      items: [
        { name: 'Interviews', path: '/recruiter/interviews', icon: <Video size={18} /> },
        { name: 'Coding', path: '/recruiter/coding', icon: <Code2 size={18} /> },
      ]
    },
    {
      title: 'System',
      items: [
        { name: 'Notifications', path: '/recruiter/notifications', icon: <Bell size={18} /> },
        { name: 'Settings', path: '/recruiter/settings', icon: <Settings size={18} /> },
      ]
    }
  ];

  const getPageTitle = () => {
    const currentPath = location.pathname;
    for (const group of navGroups) {
      const item = group.items.find(i => currentPath.startsWith(i.path));
      if (item) return item.name;
    }
    return 'Recruiter Portal';
  };

  const initials = (user?.name || 'R').split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);

  return (
    <div className="recruiter-layout">
      {sidebarOpen && <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9 }} onClick={() => setSidebarOpen(false)} />}

      <aside className={`rp-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="rp-brand">
          <div className="rp-brand-icon">RP</div>
          <div className="rp-brand-text">Recruiter Portal</div>
        </div>

        <nav className="rp-nav">
          {navGroups.map((group, idx) => (
            <div key={idx} className="rp-nav-group">
              <div className="rp-nav-title">{group.title}</div>
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `rp-nav-item ${isActive ? 'active' : ''}`}
                  onClick={() => setSidebarOpen(false)}
                >
                  {item.icon}
                  {item.name}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <main className="rp-main">
        <header className="rp-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button className="rp-btn rp-btn--ghost" style={{ display: 'none' }} onClick={() => setSidebarOpen(!sidebarOpen)}>
              <Menu size={20} />
            </button>
            <h1 className="rp-header-title">{getPageTitle()}</h1>
          </div>

          <div className="rp-header-actions">
            <button className="rp-btn rp-btn--ghost" onClick={() => navigate('/recruiter/notifications')}>
              <Bell size={18} />
            </button>
            <div className="rp-avatar">{initials}</div>
            <button className="rp-btn rp-btn--ghost" onClick={handleLogout} title="Logout">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <div className="rp-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default RecruiterLayout;
