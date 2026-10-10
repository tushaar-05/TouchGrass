# Models & Audio Machine Learning Specifications

This document outlines the machine learning models utilized by **Sit Spot**, their verified provenance, licensing terms, input/output tensor contracts, and honest confidence calibration guidelines.

---

## 1. Primary Model: Google YAMNet

### 1.1 Provenance and Official Sources
- **Original Architecture & Codebase**: Google TensorFlow Model Garden
  - Source Repository: [`tensorflow/models/research/audioset/yamnet`](https://github.com/tensorflow/models/tree/master/research/audioset/yamnet)
  - Kaggle Models Hub: [`google/yamnet/tensorFlow2/yamnet/1`](https://www.kaggle.com/models/google/yamnet/tensorFlow2/yamnet/1)
  - TensorFlow Hub: `https://tfhub.dev/google/yamnet/1`
- **Original Authors**: Manoj Ellis, Dan Ellis, Google Research.
- **Trained Dataset**: AudioSet corpus (521 audio event classes).

### 1.2 Model License & Redistribution
- **Code & Weight License**: **Apache License 2.0**
- **License Evidence**:
  - The TensorFlow Model Garden repository explicitly licenses research models under Apache-2.0.
  - The Kaggle Model Card specifies Apache-2.0.
- **Commercial & Open Source Compatibility**: Free to inspect, adapt, run locally, and redistribute under Apache-2.0 terms.

### 1.3 Verified ONNX Conversion
To eliminate heavy TensorFlow runtime dependencies and run natively on Apple Silicon M4 with optimal energy efficiency, the model is loaded via **ONNX Runtime**:
- **Export Source**: [`zeropointnine/yamnet-onnx`](https://huggingface.co/zeropointnine/yamnet-onnx)
- **Commit SHA**: `ac2ca3bd45d12ec1f19f1144205ea529b4e9dedf`
- **Conversion Pipeline**:
  ```bash
  pip install "tensorflow>=2.15,<2.17" "numpy<2.0" "tf2onnx>=1.16"
  python -m tf2onnx.convert --saved-model yamnet_saved_model/ --output yamnet.onnx
  ```
- **Files & Verified Checksums**:
  - `yamnet.onnx` (16,093,595 bytes)
    - SHA-256: `1510041dce24a2e9e84ec546807ac408ae496da6d1ed41bc3ccba649623f8e19`
  - `yamnet_class_map.csv` (14,834 bytes)
    - SHA-256: `cdf24d193e196d9e95912a2667051ae203e92a2ba09449218ccb40ef787c6df2`

### 1.4 Technical Tensor Contract
- **Input Name**: `waveform`
  - Shape: `[N]` (1D dynamic length float32 array).
  - Sample Rate: **16,000 Hz** (mono).
  - Normalization: Amplitude scaled strictly between `[-1.0, 1.0]`.
- **Sliding Window Specification**:
  - Window Duration: **0.975 seconds** (15,600 samples).
  - Hop Duration: **0.4875 seconds** (7,800 samples, 50% overlap).
- **Output Name**: `output_0`
  - Shape: `[M, 521]` where `M` is the number of time frames.
  - Output values: Uncalibrated sigmoid activations for each AudioSet class.

---

## 2. Score Calibration & Scientific Disclaimers

### 2.1 Scores are Not Probabilities
- **Critical Policy**: The raw numerical outputs from YAMNet represent uncalibrated class activation scores, **not true Bayesian posterior probabilities**.
- Applications must never present a score of `0.85` as "85% probability that a bird was present".

### 2.2 Score Bands
To avoid misleading users, Sit Spot groups detection scores into qualitative, documented score bands:

| Raw Score Band | Label Category | Scientific Interpretation |
| :--- | :--- | :--- |
| **0.50 – 1.00** | `STRONG_SIGNAL` | Strong acoustic match with training representations. High likelihood of sound signature, though acoustic mimicry or background noise may still trigger false positives. |
| **0.25 – 0.49** | `MODERATE_SIGNAL` | Discernible pattern consistent with target sound class. Often observed in distant calls or mixed ambient backgrounds. |
| **0.10 – 0.24** | `SUGGESTIVE_TRACE` | Weak acoustic presence. May be faint background audio, sensor noise, or partial resonance. |
| **< 0.10** | Filtered / Ignored | Noise floor; not reported in primary journal timeline. |

### 2.3 Environmental Sound Focus & Species Limitations
- YAMNet is trained on **AudioSet**, designed for general acoustic event detection:
  - Natural classes: *Bird, Bird vocalization / bird call, Wind, Rain, Stream / Water, Thunder, Rustling leaves, Insect, Animal sounds*.
- **Avian Species Disclaimer**: YAMNet detects the presence of bird vocalizations in general, but **does not classify individual bird species**. Users must be clearly informed that the system does not identify exact biological species.

---

## 3. Audio Preprocessing, Normalization & Quality Policies

### 3.1 Supported Containers & Codecs
- **WAV**: Uncompressed PCM (16-bit, 24-bit, 32-bit float). Handled directly in-memory via `soundfile` without subprocess overhead when natively 16 kHz.
- **WebM**: Browser-recorded container (`audio/webm`) with Opus audio codec. Decoded to 16 kHz mono float32 via sandboxed FFmpeg.
- **MP4 / M4A**: AAC audio in MP4 container (`audio/mp4`, `audio/aac`). Decoded via sandboxed FFmpeg.
- **Format Validation**: Header magic bytes are validated before decoding (e.g. `RIFF...WAVE`, `0x1A45DFA3` for WebM, `ftyp` for MP4). Unsupported extensions or spoofed payloads are rejected immediately.

### 3.2 Upload & Duration Bounds
- **Maximum File Size**: 25 MB.
- **Duration Range**: Strictly between **1.0 second** and **300.0 seconds** (5 minutes). Uploads outside these bounds are rejected prior to inference.

### 3.3 Normalization & Gain Policy
- **No Artificial Amplification**: Low-amplitude field recordings are **not** artificially normalized to full scale. Synthetically boosting gain amplifies microphone noise floor and sensor hiss, creating spurious false-positive detections.
- **Safe Value Clipping**: Samples are hard-clamped to `[-1.0, 1.0]` to guarantee tensor shape stability without arithmetic overflow.

### 3.4 Silence & Clipping Diagnostics
- **Silence Detection**: Root Mean Square (RMS) energy is computed:
  $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x_i^2}$$
  Recordings with $\text{RMS} < 10^{-4}$ (approximately $-80\text{ dBFS}$) or peak amplitude $< 10^{-3}$ are flagged as silent audio (`is_silent=True`).
- **Clipping Thresholds**:
  - Samples with $|x| \ge 0.999$ are counted.
  - **Diagnostic Warning**: If $> 5\%$ of samples are clipped, an `AudioQualityWarning` is logged for diagnostic inspection.
  - **Rejection Threshold**: If $> 30\%$ of samples are clipped, the recording is rejected with `AudioClippingError` as excessive acoustic distortion renders spectral features unreliable.

### 3.5 Temporal Window Bounding (Partial Final Window)
- YAMNet processes audio in 0.975-second windows with 0.4875-second hops.
- **Bounded Timestamps**: For non-integer multiples of window duration, the final partial window is clamped strictly to the true recording duration:
  $$\text{end\_timestamp} = \min(\text{start\_timestamp} + 0.975, \text{actual\_duration})$$
- Padded zeros used to satisfy tensor dimensions are strictly masked from user-facing detection intervals.

---

## 4. Local Offline Operation Guarantee

- Sit Spot downloads weights only once during explicit setup (`scripts/download_model.py`).
- During recording and inference, no network sockets are opened.
- Model execution occurs on device via Apple Silicon NEON CPU or CoreML execution providers.
