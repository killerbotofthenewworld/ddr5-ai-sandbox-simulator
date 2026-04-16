# Changelog

All notable changes to this project will be documented in this file. For full release notes with screenshots and details, see docs/releases or the RELEASE_*.md files.

## [Unreleased]

- Documentation cleanup and consolidation into a single docs hub
- Minor polish to Windows installer docs and README links

## [7.0.0]

- **DDR3 Memory Support**: Full DDR3 models, simulator, and AI optimizer
  - DDR3TimingParameters, DDR3VoltageParameters, DDR3PerformanceMetrics dataclasses
  - DDR3Configuration Pydantic model with JEDEC frequency validation (800-2133 MT/s)
  - DDR3Simulator with bandwidth, latency, power, and stability simulation
  - DDR3GeneticAlgorithmOptimizer with JEDEC constraint enforcement
  - DDR3L (1.35V) low-voltage support
- **Comprehensive DDR3 test suite**: 52 new tests covering models, simulator, optimizer, and constraints
- **Code audit improvements**: Version consistency across all files, improved type hints
- Updated module exports in `src/__init__.py` and root `__init__.py`
- Updated `setup.py` with DDR3 keywords and version 7.0.0

## [6.0.0]

- Major enhancement release: interactive tutorial system, Optuna-based hyperparameter optimization, advanced performance monitoring, professional configuration templates, and analytics dashboard
- Streamlit UI standardized on port 8521
- Documentation: expanded guides and status, with comprehensive release notes in RELEASE_v6.0.0.md

## [5.1.0]

- Hardware integration with safety lock and live tuning preparation workflow
- Pydantic model compatibility fixes; stability improvements across predictors and optimizers
- Initial documentation around live tuning safety and usage

## [5.0.0]

- Architecture and safety update: stronger validators, timing/voltage bounds, and modularization
- Initial Fedora/Linux packaging and setup guidance

---

Links:

- Full notes: RELEASE_v6.0.0.md, RELEASE_v5.1.0.md, RELEASE_v5.0.0.md
- Windows installer docs: windows/installer/README.md and windows/README-windows.md
