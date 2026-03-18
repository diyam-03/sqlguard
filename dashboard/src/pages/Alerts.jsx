import { useState, useEffect } from 'react';
import { getAlerts } from '../api';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try { const res = await getAlerts(50); setAlerts(res.data.alerts); }
      catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    fetch();
    const i = setInterval(fetch, 15000);
    return () => clearInterval(i);
  }, []);

  return (
    <>
      <div className="page-header">
        <div>
          <h2 className="page-title">Alert Log</h2>
          <p className="page-subtitle">All blocked attack alerts · auto-refreshes every 15s</p>
        </div>
      </div>
      <div className="table-card">
        <div className="table-header">
          <div className="table-title">{alerts.length} alerts</div>
        </div>
        {loading ? <div className="loading"><div className="spinner"></div>Loading...</div>
          : alerts.length === 0 ? <div className="empty-state">No alerts — system is clean ✓</div>
          : (
            <table>
              <thead><tr><th>Alert ID</th><th>Query</th><th>Severity</th><th>Confidence</th><th>Status</th></tr></thead>
              <tbody>
                {alerts.map(a => (
                  <tr key={a.alert_id}>
                    <td style={{ color: 'var(--text-muted)' }}>#{a.alert_id}</td>
                    <td>{a.raw_sql_text}</td>
                    <td><span className={`badge badge-${(a.severity || 'high').toLowerCase()}`}>{a.severity || 'HIGH'}</span></td>
                    <td>{a.confidence_score ? `${(a.confidence_score * 100).toFixed(1)}%` : '—'}</td>
                    <td>{a.resolved_at ? <span className="badge badge-allow">Resolved</span> : <span className="badge badge-block">Open</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>
    </>
  );
}