# Contributing to Sit Spot

Thank you for your interest in contributing to Sit Spot!

## 1. Principles

- **Listen first, screen second**: Features should minimize screen fatigue and encourage outdoor connection.
- **Privacy by default**: Never introduce telemetry, user tracking, or cloud audio processing.
- **Honest AI**: Never exaggerate model capabilities, claim uncalibrated scores as probabilities, or fabricate detections.
- **Reproducibility**: All dependencies and models must have documented provenance, automated tests, and verified licensing.

## 2. Development Setup

Sit Spot uses:
- Python 3.11+ managed by `uv` for the backend
- Node 20+ with npm for the frontend

### Backend
```bash
cd backend
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 3. Pull Request Guidelines

1. Ensure all unit tests pass (`pytest` and `npm test`).
2. Adhere to the Apache-2.0 license and document any new third-party dependencies in `MODELS.md` or package files.
3. Keep code accessible, semantic, and responsive.
