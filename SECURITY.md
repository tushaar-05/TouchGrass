# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Model & Threat Mitigation

Sit Spot runs as a local web application (`localhost:8000` backend and `localhost:5173` frontend).

### Mitigations
1. **Host Binding**:
   - Backend services bind to `127.0.0.1` by default to avoid exposure to external networks.
2. **Input Validation**:
   - Audio payloads are bounded by strict maximum durations (default 300 seconds) and file size caps (default 25 MB).
   - Audio headers and magic bytes are verified via `soundfile` before decoding.
3. **Path Traversal Guards**:
   - Session identifiers are UUIDv4 validated. File paths are strictly sandboxed inside the designated `data/` directory.
4. **Offline Isolation**:
   - The audio classification process requires zero internet access and does not execute untrusted code or arbitrary remote scripts.

## Reporting a Vulnerability

If you discover a security concern, please open a private security advisory on GitHub or contact the maintainer directly. Please do not publish security issues in public issue trackers until a fix is available.
