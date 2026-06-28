import React from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Briefcase, 
  Video, 
  Mic, 
  Cpu, 
  Code2,
  FileText, 
  LineChart, 
  Activity, 
  ShieldAlert, 
  Settings, 
  Bell,
  LogOut,
  Search
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL, getAccessToken } from '../../services/api';
import './admin.css';

const AdminLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();

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
      title: 'Platform',
      items: [
        { name: 'Dashboard', path: '/admin/dashboard', icon: <LayoutDashboard size={18} /> },
        { name: 'Analytics', path: '/admin/analytics', icon: <LineChart size={18} /> },
        { name: 'Reports', path: '/admin/reports', icon: <FileText size={18} /> },
      ]
    },
    {
      title: 'Users & Roles',
      items: [
        { name: 'Users', path: '/admin/users', icon: <Users size={18} /> },
        { name: 'Recruiters', path: '/admin/recruiters', icon: <Briefcase size={18} /> },
      ]
    },
    {
      title: 'Monitoring',
      items: [
        { name: 'Interviews', path: '/admin/interviews', icon: <Video size={18} /> },
        { name: 'Voice Sessions', path: '/admin/voice', icon: <Mic size={18} /> },
        { name: 'AI Usage', path: '/admin/ai-usage', icon: <Cpu size={18} /> },
        { name: 'Coding Module', path: '/admin/coding', icon: <Code2 size={18} /> },
      ]
    },
    {
      title: 'System',
      items: [
        { name: 'System Health', path: '/admin/system-health', icon: <Activity size={18} /> },
        { name: 'Audit Logs', path: '/admin/audit-logs', icon: <ShieldAlert size={18} /> },
        { name: 'Notifications', path: '/admin/notifications', icon: <Bell size={18} /> },
        { name: 'Settings', path: '/admin/settings', icon: <Settings size={18} /> },
      ]
    }
  ];

  const getPageTitle = () => {
    const currentPath = location.pathname;
    for (const group of navGroups) {
      const item = group.items.find(i => i.path === currentPath);
      if (item) return item.name;
    }
    return 'Admin Control Center';
  };

  return (
    <div className="admin-layout">
      {/* Sidebar */}
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-icon">AI</div>
          <div className="admin-brand-text">Admin Studio</div>
        </div>

        <div className="admin-nav">
          {navGroups.map((group, idx) => (
            <div key={idx} className="admin-nav-group">
              <div className="admin-nav-title">{group.title}</div>
              {group.items.map((item) => (
                <NavLink 
                  key={item.path} 
                  to={item.path} 
                  className={({ isActive }) => `admin-nav-item ${isActive ? 'active' : ''}`}
                >
                  {item.icon}
                  {item.name}
                </NavLink>
              ))}
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="admin-main">
        {/* Top Header */}
        <header className="admin-header">
          <h1 className="admin-header-title">{getPageTitle()}</h1>
          
          <div className="admin-header-actions">
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-muted)' }} />
              <input 
                type="text" 
                placeholder="Global search..." 
                className="admin-input"
                style={{ paddingLeft: '32px', width: '250px' }}
              />
            </div>
            
            <button className="admin-icon-btn" onClick={() => navigate('/admin/notifications')}>
              <Bell size={20} />
            </button>
            
            <div className="admin-avatar">A</div>
            
            <button className="admin-icon-btn" onClick={handleLogout} title="Logout">
              <LogOut size={20} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="admin-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
