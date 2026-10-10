import React, { useRef, useState } from 'react';
import type { AnalysisResponse, Detection, ScoreBand } from '../types/index.ts';

interface ResultsScreenProps {
  analysis: AnalysisResponse;
  audioUrl: string | null;
  onSaveToJournal: (notes: string) => void;
  onNewSession: () => void;
  onDeleteSession: () => void;
}

export const ResultsScreen: React.FC<ResultsScreenProps> = ({
  analysis,
  audioUrl,
  onSaveToJournal,
  onNewSession,
  onDeleteSession,
}) => {
  const [personalNotes, setPersonalNotes] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const playSnippet = (startTime: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = startTime;
      audioRef.current.play();
    }
  };

  const getBandBadgeClass = (band: ScoreBand) => {
    switch (band) {
      case 'STRONG_SIGNAL':
        return 'badge-strong';
      case 'MODERATE_SIGNAL':
        return 'badge-moderate';
      case 'SUGGESTIVE_TRACE':
      default:
        return 'badge-suggestive';
    }
  };

  const handleSave = () => {
    onSaveToJournal(personalNotes);
    setSavedSuccess(true);
  };

  const downloadJson = () => {
    const payload = {
      ...analysis,
      user_notes: personalNotes,
      saved_at: new Date().toISOString(),
    };
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(payload, null, 2));
    const dl = document.createElement('a');
    dl.setAttribute('href', dataStr);
    dl.setAttribute('download', `sitspot_session_${analysis.session_id.slice(0, 8)}.json`);
    dl.click();
  };

  const downloadText = () => {
    const lines = [
      `SIT SPOT — FIELD OBSERVATION NOTEBOOK`,
      `Date: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
      `Duration: ${analysis.duration_seconds} seconds`,
      ``,
      `YOUR OBSERVATIONS:`,
      analysis.user_guesses.length > 0 ? analysis.user_guesses.map((g) => `• ${g}`).join('\n') : '• (None recorded)',
      ``,
      `AI ACOUSTIC DETECTIONS:`,
      analysis.detections.length > 0
        ? analysis.detections
            .map((d) => `• [${d.start_time}s - ${d.end_time}s] ${d.label} (raw activation: ${d.raw_score}, band: ${d.score_band})`)
            .join('\n')
        : '• No prominent acoustic signals crossed threshold.',
      ``,
      `FIELD REFLECTION:`,
      analysis.reflection,
      ``,
      `PERSONAL NOTES:`,
      personalNotes || '(None)',
      ``,
      `DISCLAIMER:`,
      analysis.scientific_disclaimer,
    ];
    const dataStr = 'data:text/plain;charset=utf-8,' + encodeURIComponent(lines.join('\n'));
    const dl = document.createElement('a');
    dl.setAttribute('href', dataStr);
    dl.setAttribute('download', `sitspot_notes_${analysis.session_id.slice(0, 8)}.txt`);
    dl.click();
  };

  return (
    <div>
      {/* Session Header Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <span className="badge badge-moss">Field Journal Result</span>
            <h2 style={{ fontSize: '1.75rem', marginTop: '0.4rem', marginBottom: '0.2rem' }}>
              Listening Session Complete
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Recorded duration: {analysis.duration_seconds}s · Local offline analysis
            </p>
          </div>
          {savedSuccess ? (
            <span className="badge badge-strong">✓ Saved to Field Journal</span>
          ) : (
            <button type="button" className="button-secondary" onClick={handleSave}>
              Save to Journal
            </button>
          )}
        </div>

        {/* Audio Player */}
        {audioUrl && (
          <div className="audio-player-container">
            <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Original Local Recording:
            </p>
            <audio ref={audioRef} controls src={audioUrl}>
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </div>

      {/* 1. Your Observations First */}
      <div className="card">
        <h3 style={{ fontSize: '1.3rem', marginBottom: '0.6rem' }}>
          1. What You Noticed First
        </h3>
        {analysis.user_guesses.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {analysis.user_guesses.map((guess, idx) => (
              <span
                key={idx}
                style={{
                  backgroundColor: 'var(--moss-surface)',
                  color: 'var(--moss-primary)',
                  border: '1px solid var(--moss-border)',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '999px',
                  fontWeight: 500,
                  fontSize: '0.92rem',
                }}
              >
                {guess}
              </span>
            ))}
          </div>
        ) : (
          <p style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
            No personal guesses recorded for this session.
          </p>
        )}
      </div>

      {/* 2. Model Detections Timeline */}
      <div className="card">
        <h3 style={{ fontSize: '1.3rem', marginBottom: '0.6rem' }}>
          2. Detected Acoustic Categories
        </h3>
        <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Raw scores reflect uncalibrated model activations, not biological species certainty.
        </p>

        {analysis.detections.length === 0 ? (
          <div style={{ padding: '1.5rem', textAlign: 'center', backgroundColor: 'var(--bg-card-subtle)', borderRadius: '8px' }}>
            <p style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
              No prominent acoustic signals crossed threshold.
            </p>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              A peaceful, still listening spot. Ambient wind and subtle environmental background remained quiet.
            </p>
          </div>
        ) : (
          <div>
            {analysis.detections.map((det: Detection, idx: number) => (
              <div key={idx} className="detection-item">
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                    <span className="detection-label">{det.label}</span>
                    <span className={`badge ${getBandBadgeClass(det.score_band)}`}>
                      {det.score_band.replace('_', ' ')} ({det.raw_score})
                    </span>
                  </div>
                  <span className="detection-time">
                    [{det.start_time.toFixed(1)}s – {det.end_time.toFixed(1)}s]
                  </span>
                </div>

                {audioUrl && (
                  <button
                    type="button"
                    className="button-secondary"
                    style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}
                    onClick={() => playSnippet(det.start_time)}
                  >
                    ▶ Play snippet
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fbfaf7', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            ⚠️ {analysis.scientific_disclaimer}
          </p>
        </div>
      </div>

      {/* 3. Field Reflection & Notes */}
      <div className="card">
        <h3 style={{ fontSize: '1.3rem', marginBottom: '0.6rem' }}>
          3. Observation Reflection
        </h3>
        <div style={{ padding: '1rem', backgroundColor: 'var(--moss-surface)', borderRadius: '8px', borderLeft: '4px solid var(--moss-primary)', marginBottom: '1.25rem' }}>
          <p style={{ fontSize: '0.96rem', color: 'var(--moss-primary)', lineHeight: 1.6 }}>
            {analysis.reflection}
          </p>
        </div>

        <div>
          <label htmlFor="user-personal-notes" style={{ display: 'block', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>
            Add field notes or thoughts:
          </label>
          <textarea
            id="user-personal-notes"
            className="textarea-notes"
            placeholder="Weather conditions, location details, personal impressions..."
            value={personalNotes}
            onChange={(e) => setPersonalNotes(e.target.value)}
          />
        </div>
      </div>

      {/* Action Controls */}
      <div className="card" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <button type="button" className="button-primary" onClick={onNewSession}>
            Start Another Session
          </button>
          {!savedSuccess && (
            <button type="button" className="button-secondary" onClick={handleSave}>
              Save to Journal
            </button>
          )}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button type="button" className="button-secondary" onClick={downloadJson}>
            Export (.json)
          </button>
          <button type="button" className="button-secondary" onClick={downloadText}>
            Export (.txt)
          </button>
          <button type="button" className="button-danger" onClick={onDeleteSession}>
            Delete Recording
          </button>
        </div>
      </div>
    </div>
  );
};
