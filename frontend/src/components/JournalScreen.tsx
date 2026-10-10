import React from 'react';
import type { SavedSession } from '../types/index.ts';

interface JournalScreenProps {
  sessions: SavedSession[];
  onBack: () => void;
  onDeleteSession: (id: string) => void;
  onClearJournal: () => void;
  onExportJournal: () => void;
}

export const JournalScreen: React.FC<JournalScreenProps> = ({
  sessions,
  onBack,
  onDeleteSession,
  onClearJournal,
  onExportJournal,
}) => {
  return (
    <div>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <span className="badge badge-moss">Field Journal</span>
          <h2 style={{ fontSize: '1.75rem', marginTop: '0.4rem', marginBottom: '0.2rem' }}>
            Your Listening History
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {sessions.length} saved {sessions.length === 1 ? 'session' : 'sessions'} stored locally in your browser
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button type="button" className="button-primary" onClick={onBack}>
            + New Listening Session
          </button>
          {sessions.length > 0 && (
            <>
              <button type="button" className="button-secondary" onClick={onExportJournal}>
                Export All (.json)
              </button>
              <button
                type="button"
                className="button-danger"
                onClick={() => {
                  if (window.confirm('Are you sure you want to delete all saved journal entries?')) {
                    onClearJournal();
                  }
                }}
              >
                Clear Journal
              </button>
            </>
          )}
        </div>
      </div>

      {sessions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
          <h3 style={{ fontSize: '1.3rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            Your journal is empty
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
            Complete your first listening session to start building your personal field record.
          </p>
          <button type="button" className="button-primary" onClick={onBack}>
            Start First Session
          </button>
        </div>
      ) : (
        sessions.map((sess) => (
          <div key={sess.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <div>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {new Date(sess.timestamp).toLocaleDateString()} at {new Date(sess.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <h3 style={{ fontSize: '1.25rem', marginTop: '0.1rem' }}>
                  {Math.round(sess.duration_seconds)}s Outdoor Session
                </h3>
              </div>
              <button
                type="button"
                className="button-danger"
                style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}
                onClick={() => onDeleteSession(sess.id)}
              >
                Delete
              </button>
            </div>

            {/* Guesses */}
            {sess.user_guesses.length > 0 && (
              <div style={{ marginBottom: '0.6rem' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Your Guesses:{' '}
                </span>
                <span style={{ fontSize: '0.88rem', color: 'var(--moss-primary)' }}>
                  {sess.user_guesses.join(', ')}
                </span>
              </div>
            )}

            {/* Detections */}
            <div style={{ marginBottom: '0.6rem' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Detections ({sess.detections.length}):{' '}
              </span>
              {sess.detections.length > 0 ? (
                <span style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                  {Array.from(new Set(sess.detections.map((d) => d.label))).join(', ')}
                </span>
              ) : (
                <span style={{ fontSize: '0.88rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                  Quiet / Stillness
                </span>
              )}
            </div>

            {/* Reflection */}
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', backgroundColor: 'var(--bg-card-subtle)', padding: '0.6rem 0.8rem', borderRadius: '6px', marginBottom: sess.user_notes ? '0.6rem' : '0' }}>
              {sess.reflection}
            </p>

            {/* Notes */}
            {sess.user_notes && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.88rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                Notes: "{sess.user_notes}"
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};
