import React, { useState } from 'react';

interface GuessingScreenProps {
  durationSeconds: number;
  onAnalyze: (guesses: string[]) => void;
  onDiscard: () => void;
}

const COMMON_NATURE_TAGS = [
  'Bird song / chirping',
  'Wind in trees',
  'Rustling leaves',
  'Running water / stream',
  'Rain drops',
  'Insects / crickets',
  'Animal movement',
  'Distant footsteps',
];

export const GuessingScreen: React.FC<GuessingScreenProps> = ({
  durationSeconds,
  onAnalyze,
  onDiscard,
}) => {
  const [guesses, setGuesses] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState('');

  const addGuess = (text: string) => {
    const trimmed = text.trim();
    if (trimmed && !guesses.includes(trimmed)) {
      setGuesses([...guesses, trimmed]);
    }
    setCustomInput('');
  };

  const removeGuess = (index: number) => {
    setGuesses(guesses.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addGuess(customInput);
    }
  };

  return (
    <div className="card">
      <div style={{ marginBottom: '1.25rem' }}>
        <span className="badge badge-moss">Listen First</span>
        <h2 style={{ fontSize: '1.75rem', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
          What did you notice?
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Before checking the AI detections, record the acoustic textures you paid attention to
          during your {Math.round(durationSeconds)}s listening session.
        </p>
      </div>

      <div style={{ marginBottom: '1.25rem' }}>
        <label htmlFor="custom-guess-input" style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>
          Type an observation:
        </label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            id="custom-guess-input"
            type="text"
            className="input-text"
            placeholder="e.g. sharp high chirp, dry leaves rustling..."
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            type="button"
            className="button-secondary"
            onClick={() => addGuess(customInput)}
            disabled={!customInput.trim()}
          >
            Add
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '1.25rem' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          Quick suggestions:
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {COMMON_NATURE_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              className="button-secondary"
              style={{
                fontSize: '0.82rem',
                padding: '0.3rem 0.65rem',
                borderRadius: '999px',
                borderColor: guesses.includes(tag) ? 'var(--moss-primary)' : 'var(--border-subtle)',
                backgroundColor: guesses.includes(tag) ? 'var(--moss-surface)' : 'transparent',
              }}
              onClick={() => (guesses.includes(tag) ? setGuesses(guesses.filter((g) => g !== tag)) : addGuess(tag))}
            >
              {guesses.includes(tag) ? `✓ ${tag}` : `+ ${tag}`}
            </button>
          ))}
        </div>
      </div>

      {guesses.length > 0 && (
        <div style={{ marginBottom: '1.5rem', padding: '0.75rem', backgroundColor: 'var(--bg-card-subtle)', borderRadius: '8px' }}>
          <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
            Your notes ({guesses.length}):
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {guesses.map((g, i) => (
              <span
                key={i}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-accent)',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '6px',
                  fontSize: '0.88rem',
                }}
              >
                {g}
                <button
                  type="button"
                  onClick={() => removeGuess(i)}
                  style={{ background: 'none', border: 'none', color: '#991b1b', cursor: 'pointer', fontWeight: 'bold' }}
                  aria-label={`Remove ${g}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem' }}>
        <button
          type="button"
          className="button-primary"
          onClick={() => onAnalyze(guesses)}
        >
          {guesses.length > 0 ? 'Analyze Recording & Compare' : 'Skip Guessing & Analyze'}
        </button>
        <button
          type="button"
          className="button-danger"
          onClick={onDiscard}
        >
          Discard Session
        </button>
      </div>
    </div>
  );
};
