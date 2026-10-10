import React from 'react';

interface ListeningScreenProps {
  elapsedSeconds: number;
  targetSeconds: number;
  onStop: () => void;
  onCancel: () => void;
}

export const ListeningScreen: React.FC<ListeningScreenProps> = ({
  elapsedSeconds,
  targetSeconds,
  onStop,
  onCancel,
}) => {
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const remaining = Math.max(0, targetSeconds - elapsedSeconds);

  return (
    <div className="dark-listening-screen" role="dialog" aria-modal="true" aria-label="Active listening session">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <span className="dark-pulsing-indicator" aria-hidden="true" />
        <span style={{ fontSize: '0.9rem', color: 'var(--dark-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Listening Session Active
        </span>
      </div>

      <div style={{ maxWidth: '480px' }}>
        <div className="dark-timer" aria-live="polite">
          {formatTime(elapsedSeconds)}
        </div>
        <p style={{ color: 'var(--dark-text-muted)', fontSize: '1rem', fontStyle: 'italic', marginBottom: '1.5rem' }}>
          Put your device aside. Notice the layers of sound around you.
        </p>
        <p style={{ fontSize: '0.85rem', color: '#6e776e' }}>
          Target: {formatTime(targetSeconds)} ({remaining > 0 ? `${formatTime(remaining)} remaining` : 'Target reached'})
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', width: '100%', maxWidth: '340px' }}>
        <button
          type="button"
          className="button-primary"
          onClick={onStop}
          style={{ width: '100%', padding: '0.9rem', backgroundColor: 'var(--dark-moss)' }}
        >
          Stop & Continue to Guess
        </button>
        <button
          type="button"
          onClick={onCancel}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--dark-text-muted)',
            cursor: 'pointer',
            fontSize: '0.88rem',
            padding: '0.5rem',
          }}
        >
          Cancel Session
        </button>
      </div>
    </div>
  );
};
