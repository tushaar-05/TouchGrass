# Sit Spot 🌲

> **"Listen first. Then check."**
> An open-source, screen-minimal AI nature listening companion.

Sit Spot is a local-first nature listening application designed to encourage people to spend time outdoors paying attention to their natural surroundings. The user selects a listening duration (from 30 seconds up to 5 minutes), puts their device aside, and listens without screen distractions. Afterward, the user writes down what they observed before revealing a timestamped timeline of acoustic detections analyzed locally on-device.

---

## What Sit Spot Does

1. **Distraction-Free Outdoor Listening**: A true dark screen mode minimizes screen glare and notifications while you sit quietly outdoors.
2. **Listen-First Methodology**: You record your observations first before viewing AI results to cultivate active sensory awareness.
3. **100% Local On-Device AI**: Powered by Google YAMNet (Apache-2.0) running natively on Apple Silicon via ONNX Runtime with ARM64 NEON optimization.
4. **Honest Detections & Score Bands**: Acoustic outputs are presented as uncalibrated model activations categorized into qualitative bands (`STRONG_SIGNAL`, `MODERATE_SIGNAL`, `SUGGESTIVE_TRACE`), never false probabilities.
5. **Timeline Snippet Playback**: Review the recorded audio and jump directly to detected timestamps.
6. **Grounded Reflection**: A deterministic reflection engine compares your observations against model output without inventing wildlife or weather.
7. **Private Field Journal**: Save sessions to your browser's local storage, export to `.json` or `.txt`, or delete recordings immediately.

---

## Requirements

- **Operating System**: macOS (Apple Silicon M1/M2/M3/M4 recommended) or Linux.
- **Python**: Python 3.11+ (managed via `uv`).
- **Node.js**: Node 20+ with npm.
- **FFmpeg**: System FFmpeg installed (available via `brew install ffmpeg`).

---

## Model Location & Verification

The local AI model files reside in the repository's `models/` folder:

| File | Expected Location | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Model Weights** | `models/yamnet.onnx` | ~15.35 MB | `1510041dce24a2e9e84ec546807ac408ae496da6d1ed41bc3ccba649623f8e19` |
| **Ontology Map** | `models/yamnet_class_map.csv` | ~14.8 KB | `cdf24d193e196d9e95912a2667051ae203e92a2ba09449218ccb40ef787c6df2` |

To acquire and verify the official weights:
```bash
cd backend
.venv/bin/python scripts/download_model.py
```

To verify checksums manually:
```bash
shasum -a 256 models/yamnet.onnx models/yamnet_class_map.csv
```

See [`MODELS.md`](MODELS.md) for full provenance and licensing evidence.

---

## Setup & Running the Application

### 1. Terminal 1 — Backend (FastAPI Service)
```bash
cd backend
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"

# Start backend server on localhost:8000
uvicorn app.main:app --reload --port 8000
```
The backend API and health status will be available at `http://127.0.0.1:8000/api/health`.

### 2. Terminal 2 — Frontend (Vite + React)
```bash
cd frontend
npm install

# Start development frontend on localhost:5173
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Tests

### Complete Backend Test Suite
Runs all 48 unit and integration tests covering audio decoding, format sniffing, silence detection, duration limits, clipping diagnostics, temporal aggregation, and API routes:
```bash
cd backend
.venv/bin/pytest -v
```

### Standalone Real-AI Smoke Test
Executes genuine on-device inference on Apple Silicon under strict socket-blocked offline isolation:
```bash
cd backend
.venv/bin/python scripts/smoke_test_ai.py
```

### Frontend TypeScript Check & Build
```bash
cd frontend
npm run build
```

---

## Audio Pipeline & Supported Formats

- **Supported Input Formats**:
  - `WAV` (PCM 16-bit, 24-bit, 32-bit float; decoded directly in-memory).
  - Browser-recorded `WebM` with Opus audio (decoded via sandboxed FFmpeg).
  - `MP4` / `M4A` with AAC audio (decoded via sandboxed FFmpeg).
- **Enforced Safety Bounds**:
  - Maximum upload size: **25 MB**.
  - Minimum recording duration: **1.0 second**.
  - Maximum recording duration: **300.0 seconds** (5 minutes).
- **Normalization Policy**:
  - Resampled to 16,000 Hz, mixed down to mono float32 in `[-1.0, 1.0]`.
  - **No artificial amplification**: Quiet audio is never synthetically boosted, avoiding false-positive background noise triggers.
  - **Silence detection**: Audio with RMS $< 10^{-4}$ ($\approx -80\text{ dBFS}$) is flagged as silent (`is_silent=True`).
  - **Clipping diagnostics**: $>5\%$ samples clipped triggers a warning; $>30\%$ samples clipped is rejected as severely distorted.

---

## Privacy & Safety Commitments

- **Local Only**: All audio recordings remain on your machine. The app does not open external connections during analysis.
- **Zero Telemetry**: No analytics, trackers, or cloud accounts.
- **Microphone Control**: Access is requested only when starting a session; all audio tracks are terminated immediately upon completion or cancellation.
- **Local Storage**: Saved sessions remain in your browser's `localStorage` and can be exported or purged at any time.
- **Respectful Observation**: Always observe nature from a safe distance and never approach or harass wildlife.

---

## Limitations

- **General Acoustic Ontology**: Google YAMNet is trained on AudioSet (521 classes, including *Bird, Wind, Stream, Rain, Insects*). It detects sound events in general, but **does not classify individual biological bird species**.
- **Acoustic Mimicry & Noise**: Distant mechanical sounds, road traffic, or clothing friction can trigger false positives or mask quiet calls.
- **Browser MediaRecorder Support**: Tested on Safari, Chrome, and Firefox on macOS.

---

## License

Sit Spot is open source licensed under the [Apache License 2.0](LICENSE).
Third-party models, ontology maps, and test fixtures are documented in [`MODELS.md`](MODELS.md).
