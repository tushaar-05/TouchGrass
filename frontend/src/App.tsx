import React, { useEffect, useState } from 'react';
import type { BackendHealth } from './types/index.ts';

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) throw new Error(`Status ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="container">
      <header style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
        <span className="badge badge-moss">Sit Spot · Milestone 1</span>
        <h1 style={{ fontSize: '2.75rem', marginTop: '0.75rem', marginBottom: '0.25rem' }}>
          Sit Spot
        </h1>
        <p style={{ fontStyle: 'italic', color: 'var(--text-secondary)', fontSize: '1.15rem' }}>
          "Listen first. Then check."
        </p>
      </header>

      <main>
        <section className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.35rem', marginBottom: '0.75rem' }}>
            System & Engine Status
          </h2>

          {loading && <p style={{ color: 'var(--text-muted)' }}>Checking local backend...</p>}

          {error && (
            <div
              style={{
                background: '#fdf2f2',
                border: '1px solid #f0b4b4',
                color: '#991b1b',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.9rem',
              }}
            >
              Backend offline or connecting: {error}
            </div>
          )}

          {health && (
            <div style={{ fontSize: '0.92rem', color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span>Backend Service</span>
                <strong style={{ color: 'var(--moss-primary)' }}>{health.status.toUpperCase()} (v{health.version})</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span>Host Platform</span>
                <span>{health.platform.system} ({health.platform.machine}, Python {health.platform.python_version})</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span>Configured Model</span>
                <span>{health.local_model.configured_model} ({health.local_model.license})</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span>Local Weights</span>
                <span>{health.local_model.weights_present ? 'Present on disk' : 'Pending download via smoke test'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0' }}>
                <span>Max Session Bound</span>
                <span>{health.limits.max_duration_seconds}s ({health.limits.max_file_size_bytes / (1024 * 1024)} MB cap)</span>
              </div>
            </div>
          )}
        </section>

        <section className="card">
          <h2 style={{ fontSize: '1.35rem', marginBottom: '0.5rem' }}>
            Privacy Guarantee
          </h2>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
            All audio recordings remain entirely on your local machine. No external network requests
            or telemetry are ever transmitted. Detections reflect raw acoustic model activations
            and do not represent species certainty.
          </p>
        </section>
      </main>
    </div>
  );
};

export default App;
