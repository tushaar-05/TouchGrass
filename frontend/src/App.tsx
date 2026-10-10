import React, { useEffect, useState } from 'react';
import { useAudioRecorder } from './hooks/useAudioRecorder.ts';
import { useJournal } from './hooks/useJournal.ts';
import { ListeningScreen } from './components/ListeningScreen.tsx';
import { GuessingScreen } from './components/GuessingScreen.tsx';
import { ResultsScreen } from './components/ResultsScreen.tsx';
import { JournalScreen } from './components/JournalScreen.tsx';
import type { AnalysisResponse, BackendHealth, SavedSession } from './types/index.ts';

type AppScreen = 'welcome' | 'listening' | 'guessing' | 'analyzing' | 'results' | 'journal';

export const App: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState<AppScreen>('welcome');
  const [targetDurationSeconds, setTargetDurationSeconds] = useState<number>(60);
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  const [currentGuesses, setCurrentGuesses] = useState<string[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const {
    elapsedSeconds,
    audioBlob,
    audioUrl,
    error: recorderError,
    startRecording,
    stopRecording,
    resetRecording,
  } = useAudioRecorder();

  const {
    sessions,
    saveSession,
    deleteSession,
    clearJournal,
    exportJournalJson,
  } = useJournal();

  // Check local backend health on mount
  useEffect(() => {
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) throw new Error(`Backend status HTTP ${res.status}`);
        return res.json();
      })
      .then((data: BackendHealth) => {
        setBackendHealth(data);
        setBackendError(null);
      })
      .catch((err: Error) => {
        setBackendError(err.message);
      });
  }, []);

  const handleStartListening = async () => {
    setAnalysisError(null);
    setAnalysisResult(null);
    setCurrentGuesses([]);
    await startRecording();
    setCurrentScreen('listening');
  };

  const handleStopListening = () => {
    stopRecording();
    setCurrentScreen('guessing');
  };

  const handleCancelListening = () => {
    resetRecording();
    setCurrentScreen('welcome');
  };

  const handleAnalyze = async (guesses: string[]) => {
    setCurrentGuesses(guesses);
    setCurrentScreen('analyzing');
    setAnalysisError(null);

    if (!audioBlob) {
      setAnalysisError('No recorded audio blob found to analyze.');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      formData.append('guesses', JSON.stringify(guesses));

      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(errJson.detail || `Analysis failed with status ${res.status}`);
      }

      const result: AnalysisResponse = await res.json();
      setAnalysisResult(result);
      setCurrentScreen('results');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis request failed.';
      setAnalysisError(msg);
    }
  };

  const handleSaveToJournal = (notes: string) => {
    if (!analysisResult) return;
    const newSession: SavedSession = {
      id: analysisResult.session_id,
      timestamp: new Date().toISOString(),
      duration_seconds: analysisResult.duration_seconds,
      user_guesses: analysisResult.user_guesses,
      detections: analysisResult.detections,
      reflection: analysisResult.reflection,
      user_notes: notes,
      is_silent: analysisResult.is_silent,
    };
    saveSession(newSession);
  };

  const handleNewSession = () => {
    resetRecording();
    setAnalysisResult(null);
    setCurrentGuesses([]);
    setCurrentScreen('welcome');
  };

  const handleDeleteSession = () => {
    resetRecording();
    setAnalysisResult(null);
    setCurrentGuesses([]);
    setCurrentScreen('welcome');
  };

  return (
    <div className="container">
      {/* Top Navigation */}
      <header className="top-nav">
        <div>
          <h1 style={{ fontSize: '1.75rem', lineHeight: 1.1 }}>Sit Spot</h1>
          <p style={{ fontStyle: 'italic', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Listen first. Then check.
            {backendHealth?.local_model && (
              <span style={{ fontStyle: 'normal', marginLeft: '0.5rem', fontSize: '0.78rem' }}>
                · <span className="badge badge-moss" style={{ fontSize: '0.72rem' }}>{backendHealth.local_model.configured_model}</span>
              </span>
            )}
          </p>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {currentScreen !== 'welcome' && (
            <button
              type="button"
              className="button-minimal"
              onClick={handleNewSession}
            >
              Start New
            </button>
          )}
          <button
            type="button"
            className="button-secondary"
            style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
            onClick={() => setCurrentScreen(currentScreen === 'journal' ? 'welcome' : 'journal')}
          >
            {currentScreen === 'journal' ? '← Back to Listening' : `Field Journal (${sessions.length})`}
          </button>
        </nav>
      </header>

      {/* Backend connection banner if offline */}
      {backendError && (
        <div
          style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #f87171',
            color: '#991b1b',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            fontSize: '0.88rem',
            marginBottom: '1.25rem',
          }}
        >
          <strong>Backend Service Offline:</strong> {backendError}. Ensure <code>uvicorn app.main:app</code> is running on localhost:8000.
        </div>
      )}

      {/* Screen 1: Welcome & Setup */}
      {currentScreen === 'welcome' && (
        <div>
          <section className="card">
            <span className="badge badge-moss">Nature Listening Companion</span>
            <h2 style={{ fontSize: '1.85rem', marginTop: '0.5rem', marginBottom: '0.5rem' }}>
              Outdoor Observation
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '1.25rem' }}>
              Sit Spot is a screen-minimal outdoor listening experience. Step outside, choose a duration,
              and put your device away to listen attentively to your natural surroundings. Afterward,
              write down what you observed before revealing on-device AI sound detections.
            </p>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.95rem' }}>
                Select listening duration:
              </label>
              <div className="duration-grid">
                {[
                  { label: '30s (Test)', sec: 30 },
                  { label: '1 min', sec: 60 },
                  { label: '3 min', sec: 180 },
                  { label: '5 min', sec: 300 },
                ].map((dur) => (
                  <button
                    key={dur.sec}
                    type="button"
                    className={`duration-pill ${targetDurationSeconds === dur.sec ? 'active' : ''}`}
                    onClick={() => setTargetDurationSeconds(dur.sec)}
                  >
                    {dur.label}
                  </button>
                ))}
              </div>
            </div>

            {recorderError && (
              <div
                style={{
                  backgroundColor: '#fef2f2',
                  border: '1px solid #fca5a5',
                  color: '#991b1b',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  marginBottom: '1rem',
                  fontSize: '0.88rem',
                }}
              >
                {recorderError}
              </div>
            )}

            <button
              type="button"
              className="button-primary"
              style={{ width: '100%', padding: '1rem', fontSize: '1.05rem' }}
              onClick={handleStartListening}
            >
              Start Listening Session
            </button>
          </section>

          <section className="card">
            <h3 style={{ fontSize: '1.15rem', marginBottom: '0.4rem' }}>
              Privacy & Calibration Notice
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              • Audio recordings stay strictly on your local device and are never sent to external servers.<br />
              • The classifier produces experimental activation scores, not biological species certainty.<br />
              • Always listen from a safe location and avoid disturbing wildlife.
            </p>
          </section>
        </div>
      )}

      {/* Screen 2: Active Dark Listening Screen */}
      {currentScreen === 'listening' && (
        <ListeningScreen
          elapsedSeconds={elapsedSeconds}
          targetSeconds={targetDurationSeconds}
          onStop={handleStopListening}
          onCancel={handleCancelListening}
        />
      )}

      {/* Screen 3: Enter Guesses First */}
      {currentScreen === 'guessing' && (
        <GuessingScreen
          durationSeconds={elapsedSeconds || targetDurationSeconds}
          onAnalyze={handleAnalyze}
          onDiscard={handleNewSession}
        />
      )}

      {/* Screen 4: Analyzing with local AI */}
      {currentScreen === 'analyzing' && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
          <div className="dark-pulsing-indicator" style={{ width: '20px', height: '20px', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.6rem', marginBottom: '0.5rem' }}>
            Analyzing Recording
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', maxWidth: '420px', margin: '0 auto 1.5rem auto' }}>
            Executing local Google YAMNet AI inference on your Apple Silicon hardware.
            No data is being transmitted over the network.
          </p>

          {analysisError && (
            <div
              style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #f87171',
                color: '#991b1b',
                padding: '1rem',
                borderRadius: '8px',
                marginBottom: '1.5rem',
                fontSize: '0.9rem',
              }}
            >
              <p><strong>Analysis Error:</strong> {analysisError}</p>
              <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                <button
                  type="button"
                  className="button-primary"
                  onClick={() => handleAnalyze(currentGuesses)}
                >
                  Retry Analysis
                </button>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={handleNewSession}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Screen 5: Results & Reflection */}
      {currentScreen === 'results' && analysisResult && (
        <ResultsScreen
          analysis={analysisResult}
          audioUrl={audioUrl}
          onSaveToJournal={handleSaveToJournal}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
        />
      )}

      {/* Screen 6: Local Field Journal */}
      {currentScreen === 'journal' && (
        <JournalScreen
          sessions={sessions}
          onBack={() => setCurrentScreen('welcome')}
          onDeleteSession={deleteSession}
          onClearJournal={clearJournal}
          onExportJournal={exportJournalJson}
        />
      )}
    </div>
  );
};

export default App;
