import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Detect from './pages/Detect';
import Queries from './pages/Queries';
import Alerts from './pages/Alerts';
import Adversarial from './pages/Adversarial';

const NAV = [
  { id: 'dashboard', icon: '◈', label: 'Overview' },
  { id: 'detect', icon: '⬡', label: 'Detect' },
  { id: 'queries', icon: '≡', label: 'Query Log' },
  { id: 'alerts', icon: '⚠', label: 'Alerts' },
  { id: 'adversarial', icon: '⚔', label: 'Benchmark' },
];

function getUsername(token) {
  try {
    return JSON.parse(atob(token.split('.')[1])).sub || 'user';
  } catch { return 'user'; }
}

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return <span className="navbar-time">{time.toLocaleTimeString('en-GB')}</span>;
}

function Navbar({ active, setActive, onLogout, username }) {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <div className="navbar-logo">
          <div className="navbar-logo-dot"></div>
          SQL<span>Guard</span>
        </div>
        <div className="navbar-nav">
          {NAV.map(n => (
            <button key={n.id}
              className={`nav-item ${active === n.id ? 'active' : ''}`}
              onClick={() => setActive(n.id)}>
              <span className="nav-icon">{n.icon}</span>
              {n.label}
            </button>
          ))}
        </div>
      </div>
      <div className="navbar-right">
        <div className="navbar-status">
          <div className="status-dot"></div>
          System Active
        </div>
        <span style={{
          fontSize: 11, color: 'var(--text-muted)',
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          padding: '4px 10px', borderRadius: 6
        }}>
          {username}
        </span>
        <Clock />
        <button className="logout-btn" onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [showRegister, setShowRegister] = useState(false);
  const [active, setActive] = useState('dashboard');

  const handleLogin = (t) => {
    localStorage.setItem('token', t);
    setToken(t);
    setActive('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    if (showRegister) return <Register onSwitch={() => setShowRegister(false)} />;
    return <Login onLogin={handleLogin} onSwitch={() => setShowRegister(true)} />;
  }

  const username = getUsername(token);

  const pages = {
    dashboard: <Dashboard />,
    detect: <Detect />,
    queries: <Queries />,
    alerts: <Alerts />,
    adversarial: <Adversarial />,
  };

  return (
    <div className="app">
      <Navbar active={active} setActive={setActive}
        onLogout={handleLogout} username={username} />
      <main className="main">
        {pages[active]}
      </main>
    </div>
  );
}