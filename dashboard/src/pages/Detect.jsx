import { useState } from 'react';
import axios from 'axios';

const API_BASE = 'https://sqlguard-7qgb.onrender.com';

const SAMPLES = [
  { label: 'Safe Query', query: "SELECT * FROM users WHERE username = 'alice'" },
  { label: 'Tautology', query: "SELECT * FROM users WHERE username = '' OR '1'='1'" },
  { label: 'UNION Attack', query: "SELECT id FROM users UNION SELECT id FROM admin" },
  { label: 'Stacked Query', query: "SELECT * FROM users; DROP TABLE users;" },
  { label: 'Comment Inject', query: "SELECT * FROM users WHERE id = 1 OR 1=1 --" },
];

const SIM_QUERIES = [
  "SELECT * FROM users WHERE id = '' OR '1'='1'",
  "SELECT * FROM users WHERE username = 'admin'",
  "SELECT id FROM users UNION SELECT password FROM admin",
  "SELECT * FROM products WHERE price > 100",
  "SELECT * FROM users; DROP TABLE sessions;",
  "SELECT name FROM employees WHERE dept = 'IT'",
  "SELECT * FROM users WHERE id = 1 OR 1=1 --",
  "SELECT COUNT(*) FROM orders WHERE status = 1",
  "SELECT 1 UNION SELECT username FROM users",
  "SELECT * FROM logs WHERE created_at > NOW()",
];

export default function Detect() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [simRunning, setSimRunning] = useState(false);
  const [simFeed, setSimFeed] = useState([]);

  const handleDetect = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API_BASE}/detect`,
        { sql_query: query, user_id: 2, session_id: 'dashboard' },
        { headers: { Authorization: `Bearer ${token}` } });
      setResult(res.data);
    } catch {
      setError('Detection failed — make sure the API is running');
    } finally {
      setLoading(false);
    }
  };

  const runSimulator = async () => {
    setSimRunning(true);
    setSimFeed([]);
    const token = localStorage.getItem('token');
    for (const q of SIM_QUERIES) {
      try {
        const res = await axios.post(`${API_BASE}/detect`,
          { sql_query: q, user_id: 2, session_id: 'simulator' },
          { headers: { Authorization: `Bearer ${token}` } });
        const d = res.data;
        setSimFeed(prev => [...prev, { query: q, decision: d.decision, risk: d.risk_level, confidence: d.confidence }]);
        await new Promise(r => setTimeout(r, 500));
      } catch { }
    }
    setSimRunning(false);
  };

  const features = result?.features;
  const keyFeatures = features ? [
    { name: 'OR Branch Count', val: features.or_branch_count, triggered: features.or_branch_count > 0 },
    { name: 'Tautology Score', val: features.tautology_score?.toFixed(2), triggered: features.tautology_score > 0.3 },
    { name: 'UNION Select', val: features.union_select_flag ? 'YES' : 'NO', triggered: features.union_select_flag === 1 },
    { name: 'Stacked Query', val: features.stacked_query_flag ? 'YES' : 'NO', triggered: features.stacked_query_flag === 1 },
    { name: 'Comment Inject', val: features.comment_inject_flag ? 'YES' : 'NO', triggered: features.comment_inject_flag === 1 },
    { name: 'DROP Flag', val: features.drop_flag ? 'YES' : 'NO', triggered: features.drop_flag === 1 },
    { name: 'Keyword Density', val: features.keyword_density?.toFixed(2), triggered: features.keyword_density > 0.4 },
    { name: 'Bool Expressions', val: features.bool_expr_count, triggered: features.bool_expr_count > 1 },
    { name: 'Always True', val: features.always_true_flag ? 'YES' : 'NO', triggered: features.always_true_flag === 1 },
  ] : [];

  return (
    <>
      <div className="page-header">
        <div>
          <h2 className="page-title">Query Detection</h2>
          <p className="page-subtitle">Analyze any SQL query against the detection engine</p>
        </div>
      </div>

      <div className="detect-grid">
        <div className="detect-card">
          <div className="detect-title">Submit Query</div>
          <div className="sample-btns">
            {SAMPLES.map((s, i) => (
              <button key={i} className="sample-btn" onClick={() => setQuery(s.query)}>{s.label}</button>
            ))}
          </div>
          <textarea className="query-textarea" value={query}
            onChange={e => setQuery(e.target.value)} placeholder="Enter SQL query to analyze..." />
          <button className="detect-btn" onClick={handleDetect} disabled={loading || !query.trim()}>
            {loading ? 'Analyzing...' : '⬡ Analyze Query'}
          </button>
          {error && <p style={{ color: 'var(--accent-red)', fontSize: 11, marginTop: 8 }}>{error}</p>}
        </div>

        <div className="detect-card">
          <div className="detect-title">Detection Result</div>
          <div className="result-box">
            {!result && !loading && <div className="empty-state">Submit a query to see results</div>}
            {loading && <div className="loading"><div className="spinner"></div>Analyzing...</div>}
            {result && (
              <>
                <div className={`result-verdict ${result.is_malicious ? 'malicious' : 'safe'}`}>
                  {result.is_malicious ? '- BLOCKED' : '- ALLOWED'}
                </div>
                <div className="result-row"><span className="result-key">Decision</span><span className={`badge badge-${result.decision.toLowerCase()}`}>{result.decision}</span></div>
                <div className="result-row"><span className="result-key">Risk Level</span><span className={`badge badge-${result.risk_level.toLowerCase()}`}>{result.risk_level}</span></div>
                <div className="result-row"><span className="result-key">Confidence</span><span className="result-val">{(result.confidence * 100).toFixed(1)}%</span></div>
                <div className="result-row"><span className="result-key">Latency</span><span className="result-val">{result.latency_ms}ms</span></div>
                <div className="result-row"><span className="result-key">Query ID</span><span className="result-val">#{result.query_id}</span></div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Feature Explainer — paper Figure 3 */}
      {result && features && (
        <div className="feature-section">
          <div className="detect-title">
            AST Feature Analysis
            <span style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 400, marginLeft: 8 }}>
              — why this verdict was reached
            </span>
          </div>
          <div className="feature-grid">
            {keyFeatures.map((f, i) => (
              <div key={i} className={`feature-item ${f.triggered ? 'triggered' : 'clean'}`}>
                <div className="feature-name">{f.name}</div>
                <div className={`feature-val ${f.triggered ? 'triggered' : 'clean'}`}>{String(f.val)}</div>
                <div className={`feature-tag ${f.triggered ? 'triggered' : 'clean'}`}>
                  {f.triggered ? '⚑ triggered' : '✓ normal'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Simulator */}
      <div className="simulator-section">
        <div className="sim-header">
          <div>
            <div className="detect-title">Live Attack Simulator</div>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              Fires 10 queries — mix of safe and malicious — through the detection pipeline in real time
            </p>
          </div>
          <button className="sim-btn" onClick={runSimulator} disabled={simRunning}>
            {simRunning ? '⟳ Simulating...' : '▶ Run Simulation'}
          </button>
        </div>
        {simFeed.length === 0 && !simRunning && (
          <div className="empty-state" style={{ padding: 24 }}>Click Run Simulation to fire queries at the system</div>
        )}
        <div className="sim-feed">
          {simFeed.map((r, i) => (
            <div key={i} className="sim-row">
              <span className={`badge badge-${r.decision.toLowerCase()}`}>{r.decision}</span>
              <span className="sim-query">{r.query}</span>
              <span className={`badge badge-${r.risk.toLowerCase()}`}>{r.risk}</span>
              <span className="sim-conf">{(r.confidence * 100).toFixed(1)}%</span>
            </div>
          ))}
          {simRunning && (
            <div className="sim-row">
              <div className="spinner"></div>
              <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>Analyzing next query...</span>
            </div>
          )}
        </div>
      </div>
    </>
  );
}