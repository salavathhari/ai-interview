import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../services/api';


interface User {
  id: number;
  email: string;
  name: string;
  is_recruiter?: boolean;
  is_admin?: boolean;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  role: string;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string, role: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    // #6: Try cookie first, then fall back to localStorage for migration
    const cookieToken = document.cookie.split('; ').find(row => row.startsWith('access_token='));
    if (cookieToken) return cookieToken.split('=')[1];
    return localStorage.getItem('token');
  });
  const [role, setRole] = useState<string>(() => localStorage.getItem('role') || '');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try { setUser(JSON.parse(storedUser)); } catch { /* ignore */ }
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || '';
    const resp = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
      body: JSON.stringify({ email, password }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await resp.json();
    const userRole = data.user?.is_admin ? 'admin' : data.user?.is_recruiter ? 'recruiter' : 'candidate';
    // #6: Tokens are set as httpOnly cookies by the backend.
    // Store access token in memory for Authorization header and WebSocket usage.
    // Store role/user in localStorage for page refresh recovery.
    localStorage.setItem('role', userRole);
    localStorage.setItem('user', JSON.stringify(data.user));
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    setRole(userRole);
    setUser(data.user);
  }, []);

  const signup = useCallback(async (name: string, email: string, password: string, role: string) => {
    const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || '';
    const resp = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
      body: JSON.stringify({ name, email, password, role }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(err.detail || 'Signup failed');
    }
    const data = await resp.json();
    const userRole = role === 'recruiter' ? 'recruiter' : 'candidate';
    // #6: Tokens are set as httpOnly cookies by the backend.
    localStorage.setItem('role', userRole);
    localStorage.setItem('user', JSON.stringify(data.user));
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    setRole(userRole);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    // #6: Clear localStorage (cookies are cleared by the backend /logout endpoint)
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user');
    // Also clear the access_token cookie set by the backend (non-httpOnly)
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    setToken(null);
    setRole('');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, role, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
