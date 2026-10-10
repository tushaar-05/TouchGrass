# Sit Spot 🌲

> **"Listen first. Then check."**
> An open-source, screen-minimal AI nature listening companion.

Sit Spot encourages people to spend time outdoors paying attention to their natural surroundings. The user selects a listening duration, puts the phone away, and listens without screen distractions. Afterward, the user records their own sound guesses before revealing a timestamped timeline of acoustic detections analyzed locally on-device.

---

## Highlights

- **Distraction-Free Listening**: True dark screen mode during listening sessions with zero distracting notifications.
- **Listen-First Loop**: Guess what you heard first before revealing detections to cultivate active sensory perception.
- **100% Local On-Device AI**: Uses Google YAMNet (Apache-2.0) via ONNX Runtime. Audio never leaves your device.
- **Honest AI & Calibration**: Raw scores mapped to qualitative score bands; no misleading probability claims.
- **Private Field Journal**: Timestamped snippet playback, grounded natural reflections, and instant recording deletion.

---

## Architecture & Principles

```
Browser (React + Vite + TypeScript)
   ├── Dark Listening Session (Microphone Web Audio)
   ├── Guess Entry ("Listen first")
   └── Timeline Reveal & Snippet Player
          │
          ▼ Local HTTP / WebSocket (127.0.0.1)
Backend (FastAPI + ONNX Runtime on Apple Silicon M4)
   ├── Audio Validation & Preprocessing (16kHz mono normalization)
   ├── AudioClassifier Provider Interface
   │      ├── FakeAudioClassifier (Unit test fixture)
   │      └── YAMNet ONNX Adapter (Local offline inference)
   ├── Grounded Reflection Engine (Deterministic templates)
   └── Sandboxed Local Storage (WAV files & JSON journal)
```

See [`MODELS.md`](MODELS.md) for full model card provenance, license evidence, and tensor contracts.
See [`PRIVACY.md`](PRIVACY.md) for our strict local-only audio commitments.

---

## Quickstart

### Prerequisites
- macOS Apple Silicon (or Linux/Windows)
- Python 3.11+ (managed via `uv`)
- Node.js 20+

### 1. Backend Setup
```bash
cd backend
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## License

Sit Spot code is licensed under the [Apache License 2.0](LICENSE).
Third-party models, datasets, and audio fixtures are documented separately in [`MODELS.md`](MODELS.md).
