export type ScoreBand = 'STRONG_SIGNAL' | 'MODERATE_SIGNAL' | 'SUGGESTIVE_TRACE';

export interface Detection {
  start_time: number;
  end_time: number;
  label: string;
  raw_score: number;
  score_band: ScoreBand;
  model_id: string;
  model_version: string;
  is_test_fixture: boolean;
  scientific_disclaimer: string;
}

export interface BackendHealth {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  platform: {
    system: string;
    machine: string;
    python_version: string;
  };
  limits: {
    max_duration_seconds: number;
    min_duration_seconds: number;
    max_file_size_bytes: number;
  };
  local_model: {
    configured_model: string;
    license: string;
    weights_present: boolean;
    model_path: string;
  };
}

export interface AnalysisResponse {
  session_id: string;
  duration_seconds: number;
  sample_count: number;
  is_silent: boolean;
  has_clipping_warning: boolean;
  detections: Detection[];
  user_guesses: string[];
  reflection: string;
  scientific_disclaimer: string;
}

export interface SavedSession {
  id: string;
  timestamp: string;
  duration_seconds: number;
  user_guesses: string[];
  detections: Detection[];
  reflection: string;
  user_notes?: string;
  is_silent: boolean;
}
