import React from 'react';
import { useNavigate } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
    const navigate = useNavigate();
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: '16px' }}>
            <h1 style={{ fontSize: '64px', fontWeight: '700', color: 'var(--ink)' }}>404</h1>
            <p style={{ fontSize: '18px', color: 'var(--muted)' }}>Page not found</p>
            <button className="solid" onClick={() => navigate('/dashboard')}>Go to Dashboard</button>
        </div>
    );
};

export default NotFoundPage;
