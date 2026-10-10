# Changelog

All notable changes to **Sit Spot** are documented here in accordance with [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added - Milestone 1
- Repository initialization with Apache-2.0 license.
- Documentation standards: `README.md`, `PRIVACY.md`, `SECURITY.md`, `MODELS.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- Verified YAMNet model provenance, license evidence, and tensor contracts.
- Backend architecture skeleton with FastAPI, Pydantic, and `uv` virtual environment management.
- Abstract `AudioClassifier` interface and explicit `FakeAudioClassifier` test fixture.
- Detection schema with documented score bands (not pseudo-probabilities).
- Backend unit test suite (`test_health.py`, `test_classifier_contract.py`).
- Accessible, naturalist design system tokens and frontend scaffolding.
