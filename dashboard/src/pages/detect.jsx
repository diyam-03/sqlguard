import { useState } from 'react';
import { detectQuery } from '../api';

const SAMPLE_QUERIES = [
  { label: 'Safe Query', query: "SELECT * FROM users WHERE username = 'alice'" },
  { label: 'Tautology Attack', query: "SELECT * FROM users WHERE username = '' OR '1'='1'" },
  { label: 'UNION Attack', query: "SELECT id FROM users UNION SELECT id FROM admin" },
  { label: 'Stacked Query', query: "SELECT * FROM users; DROP TABLE users;" },
  { label: 'Comment Injection', query: "SELECT * FROM users WHERE id = 1 OR 1=1 --" },
];

export default function Detect() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDetect = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await detectQuery(query);
      setResult(res.data);
    } catch (err) {
      setError('Detection failed — make sure the API is running');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2 className="page-title">Query Detection</h2>
          <p className="page-subtitle">Test any SQL query against the detection engine</p>
        </div>
      </div>

      <div className="detect-grid">
        <div className="detect-card">
          <div className="detect-title">Submit Query</div>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
            {SAMPLE_QUERIES.map((s, i) => (
              <button
                key={i}
                onClick={() => setQuery(s.query)}
                style={{
                  padding: '4px 10px',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                  borderRadius: '4px',
                  color: 'var(--text-muted)',
                  fontSize: '10px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
          <textarea
            className="query-textarea"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Enter SQL query to analyze..."
          />
          <button
            className="detect-btn"
            onClick={handleDetect}
            disabled={loading || !query.trim()}
          >
            {loading ? 'Analyzing...' : '⬡ Analyze Query'}
          </button>
          {error && <p style={{ color: 'var(--accent-red)', fontSize: '12px', marginTop: '8px' }}>{error}</p>}
        </div>

        <div className="detect-card">
          <div className="detect-title">Detection Result</div>
          <div className="result-box">
            {!result && !loading && (
              <div className="empty-state">Submit a query to see results</div>
            )}
            {loading && (
              <div className="loading">
                <div className="spinner"></div>
                Analyzing...
              </div>
            )}
            {result && (
              <>
                <div className={`result-verdict ${result.is_malicious ? 'malicious' : 'safe'}`}>
                  {result.is_malicious ? '🚫 BLOCKED' : '✅ ALLOWED'}
                </div>
                <div className="result-row">
                  <span className="result-key">Decision</span>
                  <span className={`badge badge-${result.decision.toLowerCase()}`}>{result.decision}</span>
                </div>
                <div className="result-row">
                  <span className="result-key">Risk Level</span>
                  <span className={`badge badge-${result.risk_level.toLowerCase()}`}>{result.risk_level}</span>
                </div>
                <div className="result-row">
                  <span className="result-key">Confidence</span>
                  <span className="result-val">{(result.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="result-row">
                  <span className="result-key">Latency</span>
                  <span className="result-val">{result.latency_ms}ms</span>
                </div>
                <div className="result-row">
                  <span className="result-key">Query ID</span>
                  <span className="result-val">#{result.query_id}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}