# Changelog

All notable changes to **Sit Spot** are documented here in accordance with [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

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
