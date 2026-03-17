import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import { getStats, getTrends, getDistribution } from '../api';
import { format } from 'date-fns';

const COLORS = ['#ff3b4e', '#ff7c20', '#ffb020', '#00d4a0'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState([]);
  const [distribution, setDistribution] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const fetchData = async () => {
    try {
      const [statsRes, trendsRes, distRes] = await Promise.all([
        getStats(),
        getTrends(),
        getDistribution(),
      ]);
      setStats(statsRes.data);
      setTrends(trendsRes.data.trends.reverse());
      setDistribution(distRes.data.distribution);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading dashboard...
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h2 className="page-title">Security Overview</h2>
          <p className="page-subtitle">
            Auto-refreshes every 15s · Last updated {format(lastRefresh, 'HH:mm:ss')}
          </p>
        </div>
        <button className="refresh-btn" onClick={fetchData}>
          ↻ Refresh Now
        </button>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card red">
          <div className="kpi-label">Total Blocked</div>
          <div className="kpi-value">{stats?.total_blocked ?? 0}</div>
          <div className="kpi-sub">Malicious queries stopped</div>
        </div>
        <div className="kpi-card green">
          <div className="kpi-label">Total Allowed</div>
          <div className="kpi-value">{stats?.total_allowed ?? 0}</div>
          <div className="kpi-sub">Safe queries passed</div>
        </div>
        <div className="kpi-card amber">
          <div className="kpi-label">Block Rate</div>
          <div className="kpi-value">{stats?.block_rate ?? 0}%</div>
          <div className="kpi-sub">Of all queries analyzed</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-label">Avg Latency</div>
          <div className="kpi-value">{stats?.avg_latency_ms ?? 0}ms</div>
          <div className="kpi-sub">Detection speed</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">Attack Trends</div>
          <div className="chart-subtitle">Blocked vs total queries over time</div>
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d40" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#4a6080', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  tickFormatter={(d) => d ? format(new Date(d), 'MMM d') : ''}
                />
                <YAxis tick={{ fill: '#4a6080', fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                <Tooltip
                  contentStyle={{
                    background: '#111827',
                    border: '1px solid #1e2d40',
                    borderRadius: '8px',
                    fontFamily: 'JetBrains Mono',
                    fontSize: '12px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="total_queries"
                  stroke="#3b9eff"
                  strokeWidth={2}
                  dot={false}
                  name="Total"
                />
                <Line
                  type="monotone"
                  dataKey="blocked"
                  stroke="#ff3b4e"
                  strokeWidth={2}
                  dot={false}
                  name="Blocked"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">No trend data yet — run some queries</div>
          )}
        </div>

        <div className="chart-card">
          <div className="chart-title">Risk Distribution</div>
          <div className="chart-subtitle">Breakdown by severity level</div>
          {distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={distribution}
                  dataKey="count"
                  nameKey="risk_level"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                >
                  {distribution.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#111827',
                    border: '1px solid #1e2d40',
                    borderRadius: '8px',
                    fontFamily: 'JetBrains Mono',
                    fontSize: '12px',
                  }}
                />
                <Legend
                  formatter={(value) => (
                    <span style={{ color: '#8ba3c1', fontSize: '11px', fontFamily: 'JetBrains Mono' }}>
                      {value}
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">No blocked queries yet</div>
          )}
        </div>
      </div>
    </>
  );
}