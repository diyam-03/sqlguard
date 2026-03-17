import { useState, useEffect } from 'react';
import Login from './pages/login';
import Dashboard from './pages/dashboard';
import Detect from './pages/detect';
import Queries from './pages/Queries';
import Alerts from './pages/Alerts';

function Sidebar({ activePage, setActivePage, onLogout }) {
  const navItems = [
    { id: 'dashboard', icon: '◈', label: 'Dashboard' },
    { id: 'detect', icon: '⬡', label: 'Detect Query' },
    { id: 'queries', icon: '≡', label: 'Query Log' },
    { id: 'alerts', icon: '⚠', label: 'Alerts' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>SQL<span>Guard</span></h1>
        <p>Security Monitor v1.0</p>
      </div>
      <nav className="sidebar-nav">
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => setActivePage(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar-status">
        <div className="status-dot">System Active</div>
        <button
          onClick={onLogout}
          style={{
            marginTop: '12px',
            width: '100%',
            padding: '8px',
            background: 'transparent',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            color: 'var(--text-muted)',
            fontSize: '11px',
            cursor: 'pointer',
            fontFamily: 'var(--font-mono)',
          }}
        >
          Logout
        </button>
      </div>
    </aside>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activePage, setActivePage] = useState('dashboard');

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  const pages = {
    dashboard: <Dashboard />,
    detect: <Detect />,
    queries: <Queries />,
    alerts: <Alerts />,
  };

  return (
    <div className="app">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        onLogout={handleLogout}
      />
      <main className="main">
        {pages[activePage]}
      </main>
    </div>
  );
}