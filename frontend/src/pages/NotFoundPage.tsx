import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const NotFoundPage: React.FC = () => {
    const navigate = useNavigate();
    return (
        <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            minHeight: '100vh', gap: '16px', padding: '24px'
        }}>
            <h1 style={{ fontSize: '72px', fontWeight: '700', color: 'var(--ink)', margin: 0 }}>404</h1>
            <p style={{ fontSize: '18px', color: 'var(--muted)', margin: 0 }}>Page not found</p>
            <button
                onClick={() => navigate('/dashboard')}
                style={{
                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                    background: 'var(--accent-strong)', color: '#fff',
                    border: 'none', borderRadius: '10px', padding: '10px 20px',
                    fontWeight: '600', fontSize: '13px', cursor: 'pointer'
                }}
            >
                <ArrowLeft size={16} /> Go to Dashboard
            </button>
        </div>
    );
};

export default NotFoundPage;
