# Changelog

All notable changes to **Sit Spot** are documented here in accordance with [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added - Complete End-to-End Application
- Completed full frontend experience in React 18 / Vite / TypeScript:
  - Welcome screen with configurable listening durations (30s, 1m, 3m, 5m).
  - Minimal dark listening screen with elapsed timer and clean microphone track release.
  - Guess-first observation screen capturing user perception before model reveal.
  - Results view with seekable audio playback and snippet player for each detected acoustic event.
  - Deterministic grounded reflection generator (`app/reflection/generator.py`) contrasting user observations with detections.
  - Field Journal screen persisting listening history locally in browser storage (`localStorage`) with JSON export and deletion controls.
- Integrated `/api/analyze` FastAPI endpoint with audio validation, on-device YAMNet inference, and reflection generation.
- Expanded backend test suite to 48 tests with 100% pass rate.
- Implemented real Google YAMNet ONNX inference adapter (`app/classifier/adapters/yamnet_onnx.py`):
  - Validates tensor input/output signatures at runtime (`waveform` [N] -> `output_0` [M, 521]).
  - Connects to existing 16 kHz mono audio validation and decoding pipeline.
  - Implements temporal detection aggregation and score smoothing (`app/classifier/aggregator.py`), merging contiguous overlapping windows into continuous sound events with peak activation scores.
  - Strictly clamps detection timestamps within actual recording duration, never presenting zero-padded samples as observed sound.
  - Enforces zero silent fallback policy: runtime failures raise structured exceptions rather than substituting fake data.
  - Added unit test coverage for aggregation, short inputs, tensor mismatches, and offline isolation.
  - Added real-model integration test executing local inference on Apple Silicon M4 under socket-blocked isolation.
  - Resolved `StarletteDeprecationWarning` in test configuration.

### Added - Milestone 2
- Implemented robust audio validation and decoding service (`app/core/audio.py`):
  - In-memory decoding for standard 16 kHz WAV files via `soundfile`.
  - Secure, sandboxed FFmpeg fallback (`shell=False`, 15s timeout) for browser-recorded WebM (Opus) and MP4/M4A (AAC).
  - Pre-validation of file size (25 MB max) and duration bounds (1.0s – 300.0s).
  - Magic-byte sniffing to reject unsupported or spoofed containers (`RIFF`, EBML `0x1A45DFA3`, `ftyp`).
  - Strict stereo-to-mono mixdown and 16,000 Hz resampling to float32 samples in `[-1.0, 1.0]`.
  - Silence detection thresholding (RMS < 1e-4) and clipping diagnostics (>5% warning, >30% rejection).
  - Bounded temporal windowing logic ensuring partial final windows never exceed recording duration.
  - Comprehensive unit test suite with 25 passing tests (`backend/tests/test_audio.py`).

### Added - Milestone 1
- Repository initialization with Apache-2.0 license.
- Documentation standards: `README.md`, `PRIVACY.md`, `SECURITY.md`, `MODELS.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- Verified YAMNet model provenance, license evidence, and tensor contracts.
- Backend architecture skeleton with FastAPI, Pydantic, and `uv` virtual environment management.
- Abstract `AudioClassifier` interface and explicit `FakeAudioClassifier` test fixture.
- Detection schema with documented score bands (not pseudo-probabilities).
- Backend unit test suite (`test_health.py`, `test_classifier_contract.py`).
- Accessible, naturalist design system tokens and frontend scaffolding.
