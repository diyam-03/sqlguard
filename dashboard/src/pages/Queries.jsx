import { useState, useEffect } from 'react';
import { getQueries } from '../api';
import { format } from 'date-fns';

export default function Queries() {
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetch = async () => {
      try { const res = await getQueries(100); setQueries(res.data.queries); }
      catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    fetch();
    const i = setInterval(fetch, 15000);
    return () => clearInterval(i);
  }, []);

  const filtered = queries.filter(q => {
    const mf = filter === 'all' || (filter === 'blocked' && q.is_malicious) || (filter === 'allowed' && !q.is_malicious);
    const ms = !search || q.raw_sql_text?.toLowerCase().includes(search.toLowerCase());
    return mf && ms;
  });

  return (
    <>
      <div className="page-header">
        <div>
          <h2 className="page-title">Query Log</h2>
          <p className="page-subtitle">All analyzed queries · auto-refreshes every 15s</p>
        </div>
      </div>
      <div className="table-card">
        <div className="table-header">
          <div className="table-title">{filtered.length} records</div>
          <div className="filter-row">
            <input className="filter-input" placeholder="Search queries..." value={search} onChange={e => setSearch(e.target.value)} />
            <select className="filter-select" value={filter} onChange={e => setFilter(e.target.value)}>
              <option value="all">All</option>
              <option value="blocked">Blocked</option>
              <option value="allowed">Allowed</option>
            </select>
          </div>
        </div>
        {loading ? <div className="loading"><div className="spinner"></div>Loading...</div>
          : filtered.length === 0 ? <div className="empty-state">No records found</div>
          : (
            <table>
              <thead><tr><th>ID</th><th>Query</th><th>Decision</th><th>Risk</th><th>Confidence</th><th>Time</th></tr></thead>
              <tbody>
                {filtered.map(q => (
                  <tr key={q.query_id}>
                    <td style={{ color: 'var(--text-muted)' }}>#{q.query_id}</td>
                    <td>{q.raw_sql_text}</td>
                    <td><span className={`badge badge-${(q.decision || 'allow').toLowerCase()}`}>{q.decision || 'ALLOW'}</span></td>
                    <td>{q.risk_level && <span className={`badge badge-${q.risk_level.toLowerCase()}`}>{q.risk_level}</span>}</td>
                    <td>{q.confidence_score ? `${(q.confidence_score * 100).toFixed(1)}%` : '—'}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{q.timestamp ? format(new Date(q.timestamp), 'MMM d, HH:mm:ss') : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>
    </>
  );
}