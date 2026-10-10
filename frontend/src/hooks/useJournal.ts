import { useCallback, useEffect, useState } from 'react';
import type { SavedSession } from '../types/index.ts';

const STORAGE_KEY = 'sitspot_saved_sessions';

export function useJournal() {
  const [sessions, setSessions] = useState<SavedSession[]>([]);

  const loadSessions = useCallback(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setSessions(parsed);
          return;
        }
      }
    } catch {
      // Fallback on corrupt storage
    }
    setSessions([]);
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const saveSession = useCallback((session: SavedSession) => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const existing: SavedSession[] = raw ? JSON.parse(raw) : [];
      const updated = [session, ...existing.filter((s) => s.id !== session.id)];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      setSessions(updated);
    } catch (e) {
      console.error('Failed to save session to local storage', e);
    }
  }, []);

  const deleteSession = useCallback((id: string) => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const existing: SavedSession[] = raw ? JSON.parse(raw) : [];
      const updated = existing.filter((s) => s.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      setSessions(updated);
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  }, []);

  const clearJournal = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setSessions([]);
  }, []);

  const exportJournalJson = useCallback(() => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(sessions, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute('href', dataStr);
    dlAnchor.setAttribute('download', `sitspot_journal_${new Date().toISOString().slice(0, 10)}.json`);
    dlAnchor.click();
  }, [sessions]);

  return {
    sessions,
    saveSession,
    deleteSession,
    clearJournal,
    exportJournalJson,
    refreshJournal: loadSessions,
  };
}
