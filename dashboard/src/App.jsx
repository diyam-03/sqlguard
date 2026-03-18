import { useState, useEffect } from 'react';
import Login from './pages/Login';
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

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span className="navbar-time">
      {time.toLocaleTimeString('en-GB')}
    </span>
  );
}

function Navbar({ active, setActive, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <div className="navbar-logo">
          <div className="navbar-logo-dot"></div>
          SQL<span>Guard</span>
        </div>
        <div className="navbar-nav">
          {NAV.map(n => (
            <button
              key={n.id}
              className={`nav-item ${active === n.id ? 'active' : ''}`}
              onClick={() => setActive(n.id)}
            >
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
        <Clock />
        <button className="logout-btn" onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [active, setActive] = useState('dashboard');

  const handleLogin = (t) => { localStorage.setItem('token', t); setToken(t); };
  const handleLogout = () => { localStorage.removeItem('token'); setToken(null); };

  if (!token) return <Login onLogin={handleLogin} />;

  const pages = {
    dashboard: <Dashboard />,
    detect: <Detect />,
    queries: <Queries />,
    alerts: <Alerts />,
    adversarial: <Adversarial />,
  };

  return (
    <div className="app">
      <Navbar active={active} setActive={setActive} onLogout={handleLogout} />
      <main className="main">
        {pages[active]}
      </main>
    </div>
  );
}