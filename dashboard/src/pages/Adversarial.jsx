export default function Adversarial() {
  const ATTACKS = [
    { query: "SELECT * FROM users WHERE username = '' OR '1'='1'", type: 'Tautology', obfuscation: 'None', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '98.4%' },
    { query: "SELECT * FROM users WHERE username = '' OR 'x'='x'", type: 'Tautology', obfuscation: 'Value variation', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '97.1%' },
    { query: "SELECT * FROM users WHERE username = '' OR 'abc'='abc'", type: 'Tautology', obfuscation: 'String variation', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '95.8%' },
    { query: "SELECT * FROM users WHERE id = CHAR(49) OR CHAR(49)=CHAR(49)", type: 'CHAR Encoding', obfuscation: 'CHAR() encoding', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '91.2%' },
    { query: "SELECT/**/ * /**/FROM users WHERE/**/id=1 OR 1=1", type: 'Comment Inject', obfuscation: 'Inline comments', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '89.7%' },
    { query: "SeLeCt * FrOm users WhErE id=1 oR 1=1", type: 'Case Mixing', obfuscation: 'Case variation', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '94.3%' },
    { query: "SELECT * FROM users WHERE id=1 OR 0x31=0x31", type: 'Hex Encoding', obfuscation: 'Hex values', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '88.9%' },
    { query: "SELECT id FROM users UNION%20SELECT id FROM admin", type: 'URL Encoded', obfuscation: 'URL encoding', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '92.6%' },
    { query: "SELECT * FROM users WHERE id=1 OR true", type: 'Boolean', obfuscation: 'None', waf: 'BLOCKED', sqlguard: 'BLOCKED', conf: '99.1%' },
    { query: "SELECT * FROM users WHERE id=1 OR 2>1", type: 'Tautology', obfuscation: 'Comparison variant', waf: 'BYPASSED', sqlguard: 'BLOCKED', conf: '93.4%' },
  ];

  const bypassed = ATTACKS.filter(a => a.waf === 'BYPASSED').length;
  const caught = ATTACKS.filter(a => a.sqlguard === 'BLOCKED').length;

  return (
    <>
      <div className="page-header">
        <div>
          <h2 className="page-title">Adversarial Benchmark</h2>
          <p className="page-subtitle">Obfuscated attack dataset — comparing SQLGuard vs signature-based WAF tools</p>
        </div>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: 6 }}>
          Paper — Table II
        </span>
      </div>

      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <div className="kpi-card red">
          <div className="kpi-icon">⚠️</div>
          <div className="kpi-label">WAF Bypassed</div>
          <div className="kpi-value">{bypassed}/10</div>
          <div className="kpi-sub">Signature tools failed</div>
        </div>
        <div className="kpi-card green">
          <div className="kpi-icon">🛡️</div>
          <div className="kpi-label">SQLGuard Caught</div>
          <div className="kpi-value">{caught}/10</div>
          <div className="kpi-sub">AST detection success</div>
        </div>
        <div className="kpi-card amber">
          <div className="kpi-icon">📈</div>
          <div className="kpi-label">Improvement</div>
          <div className="kpi-value">+{bypassed * 10}%</div>
          <div className="kpi-sub">Over signature baseline</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-icon">🎯</div>
          <div className="kpi-label">Avg Confidence</div>
          <div className="kpi-value">93.4%</div>
          <div className="kpi-sub">On obfuscated attacks</div>
        </div>
      </div>

      <div className="adv-table-card">
        <div className="table-header">
          <div className="table-title">Obfuscated Attack Test Cases</div>
        </div>
        <div className="adv-row adv-header">
          <span>Query</span>
          <span>Attack Type</span>
          <span>Obfuscation</span>
          <span>WAF Result</span>
          <span>SQLGuard</span>
        </div>
        {ATTACKS.map((a, i) => (
          <div key={i} className="adv-row">
            <span className="adv-query">{a.query}</span>
            <span className="adv-type">{a.type}</span>
            <span className="adv-type">{a.obfuscation}</span>
            <span><span className={`badge badge-${a.waf.toLowerCase()}`}>{a.waf}</span></span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="badge badge-blocked">{a.sqlguard}</span>
              <span style={{ fontSize: 10, color: 'var(--accent-green)' }}>{a.conf}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="finding-box">
        <strong>Key Finding:</strong> Signature-based WAF tools were bypassed on {bypassed}/10 obfuscated attacks — 0% detection on lexically varied tautologies like OR 'x'='x' and OR 'abc'='abc'.<br />
        SQLGuard's AST-layer detection blocked {caught}/10 attacks regardless of lexical form, because the syntax tree structure remains identical across all obfuscation variants.<br />
        <strong>Conclusion:</strong> Structural analysis is invariant to obfuscation — textual form changes, tree structure does not.
      </div>
    </>
  );
}