import { useState } from 'react';
import axios from 'axios';

const API_BASE = 'https://sqlguard-7qgb.onrender.com';

export default function Register({ onSwitch }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) { setError('Passwords do not match'); return; }
    setLoading(true);
    setError('');
    try {
      await axios.post(`${API_BASE}/auth/register`, {
        username, password, role: 'viewer'
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  if (success) return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">SQL<span>Guard</span></div>
        <p className="login-sub">Account created successfully</p>
        <p style={{ color: 'var(--accent-green)', fontSize: 13, marginBottom: 20, lineHeight: 1.6 }}>
          Your account has been created. You can now log in with your credentials.
        </p>
        <button className="login-btn" onClick={onSwitch}>Go to Login</button>
      </div>
    </div>
  );

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">SQL<span>Guard</span></div>
        <p className="login-sub">Create a new account</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input className="form-input" type="text" value={username}
              onChange={e => setUsername(e.target.value)} placeholder="Choose a username" required />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" value={password}
              onChange={e => setPassword(e.target.value)} placeholder="Choose a password" required />
          </div>
          <div className="form-group">
            <label className="form-label">Confirm Password</label>
            <input className="form-input" type="password" value={confirm}
              onChange={e => setConfirm(e.target.value)} placeholder="Repeat password" required />
          </div>
          <button className="login-btn" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
          {error && <p className="error-msg">{error}</p>}
        </form>
        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 11, color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }} onClick={onSwitch}>
            Sign in
          </span>
        </p>
      </div>
    </div>
  );
}