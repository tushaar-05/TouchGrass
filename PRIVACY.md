# Privacy Policy & Architecture Principles

Sit Spot is built on a single, uncompromising privacy rule: **Your recordings stay on your machine.**

## 1. Core Commitments

1. **Local-Only Audio**:
   - Audio recorded in the browser is transferred directly to your local FastAPI backend running on `localhost`.
   - The audio never leaves your machine. There are no cloud APIs, third-party inference endpoints, or remote storage buckets.
2. **Zero Telemetry & Analytics**:
   - Sit Spot contains no trackers, telemetry, error reporting SDKs, or analytics pings.
3. **Explicit Permissions**:
   - The microphone is accessed only when you explicitly press "Start Listening Session".
   - The microphone is disconnected immediately once the session concludes or is cancelled.
4. **User-Controlled Data**:
   - All session files (WAV audio and JSON metadata) are stored locally in the application's `data/recordings/` folder.
   - Users can permanently delete recordings and session history at any time with a single click.
5. **Offline by Design**:
   - Once the local model weights are acquired during setup, the analysis pipeline works completely offline without network access.

## 2. Respectful Nature Listening Ethics

When listening outdoors:
- Natural spaces are shared spaces. Recordings might accidentally capture ambient human conversation or private sounds.
- Sit Spot encourages listening in mindful, low-traffic areas.
- Always observe wildlife from a respectful distance; never use acoustic playback or chase animals to produce audio recordings.
