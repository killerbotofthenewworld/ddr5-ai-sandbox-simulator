# 🧠 DDR5 AI Memory Tuner v6.0.2

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-6.0.2-blue.svg)](https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/releases)
[![CI](https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/actions/workflows/ci-cd.yml)

> AI-powered DDR5 memory timing optimizer and performance simulator. Streamlit web UI, Windows installer, JEDEC compliance validation, and genetic-algorithm-driven tuning — no physical hardware required.

---

Looking for docs? See the consolidated docs hub in `docs/` (index at `docs/README.md`).

## 📸 Screenshots & Features Demo

### 🎯 Main Interface - Professional Dashboard

![Main Dashboard](screenshots/Screenshot_20250623_155226.png)
*Professional DDR5 optimization interface with simulation and AI optimization features*

### 🚀 Enhanced Features Hub - Advanced Tools

![Enhanced Features](screenshots/Screenshot_20250623_155423.png)
*Comprehensive feature hub with dark/light theme, 3D charts, real-time monitoring, and AI assistant*

### 🔧 Live Hardware Integration

![Live Tuning](screenshots/Screenshot_20250623_155517.png)
*Real hardware control with safety locks, advanced integration, and comprehensive databases*

---

## 🚀 Quick Start

### Easy install (Windows)

Option A — EXE installer (recommended):

- Download the Windows installer:
	- Latest: <https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/releases/latest/download/DDR5-AI-Memory-Tuner-Setup.exe>
	- All versions: <https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/releases>
- Run the EXE (no admin required). It installs to `%LOCALAPPDATA%\DDR5-AI-Memory-Tuner`, sets up a venv, installs dependencies, and adds Start Menu/Desktop shortcuts.

Option B — Scripted install (from source):

- Double-click `windows/install.bat` (or right-click `windows/install.ps1` → Run with PowerShell)
- Creates the same per-user install/shortcuts as the EXE
- More details in `windows/README-windows.md`

Launch options on Windows:

- From Desktop/Start Menu shortcut "DDR5 AI Memory Tuner", or
- Run `%LOCALAPPDATA%\DDR5-AI-Memory-Tuner\run_ddr5_simulator.bat`

### From source (all platforms)

```bash
git clone https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner.git
cd ddr5-ai-memory-tuner
python -m pip install -r requirements.txt
python -m streamlit run src/web_interface/main.py --server.port 8521
```

### Quick AI demo (no web UI)

```bash
python demo_advanced_ai.py
```

---

## ✨ Features

### 🎨 **Professional UI/UX**

- **Dark/Light Theme** with smooth animations
- **Custom CSS** styling and metric cards
- **Progress indicators** and loading spinners
- **Responsive design** for all screen sizes

### 📊 **Advanced Visualizations**

- **3D Performance Charts** - Interactive surface plots
- **Real-time Graphs** - Live memory bandwidth/latency
- **Configuration Comparisons** - Side-by-side analysis
- **Optimization Landscapes** - AI fitness visualization

### 🤖 **AI-Powered Optimization**

- **Genetic Algorithm** - Population-based search with JEDEC constraint repair
- **Reinforcement Learning** - Q-learning agent for incremental tuning
- **Ensemble Methods** - Combines GA + RL results for best-of-both
- **AutoML Pipeline** - Automated model training with Optuna
- **LLM Integration** - OpenAI, Anthropic, Ollama, Local models (optional)

### 🔬 **DDR5 Simulation Engine**

- **Bandwidth Simulation** - Sequential, random, and mixed access patterns
- **Latency Modelling** - Bank conflicts, command overhead, timing efficiency
- **Power Estimation** - Dynamic + static power with thermal derating
- **Stability Testing** - Configurable stress levels with scoring and recommendations
- **JEDEC Compliance** - Validates frequencies (DDR5-4000 to DDR5-8400), timings, and voltages

### ⚡ **Hardware Integration** (Linux & Windows)

- **Hardware Detection** - Automatic system profiling via dmidecode / WMI / system_profiler
- **Live Tuning** - Safety locks, backup/restore, emergency stops
- **WebSocket Monitoring** - Real-time metrics streaming
- **Emergency Recovery** - Instant parameter restoration
- **Windows Support** - WMI-based memory detection, Event Log stability checks, thermal monitoring via WMI/psutil, vendor-tool detection via registry, backup/restore of memory configuration snapshots

> **Note:** On both Linux and Windows, direct register-level memory writes require kernel drivers or vendor tools. The tuner will detect installed vendor tools (MSI Dragon Center, ASUS AI Suite, etc.) and guide you to apply settings through those tools or via BIOS. Backup/restore captures a full WMI snapshot on Windows and dmidecode/UEFI variables on Linux.

### 🛡️ **Safety & Validation**

- **Multi-level Confirmations** for hardware changes
- **Bounded Optimization** - AI stays within safe voltage (1.0–1.2 V VDDQ) and timing ranges
- **JEDEC Compliance** checking for all configurations
- **Stability Scoring** for parameter combinations
- **Voltage bounds clamping** during thermal simulation

### 🔧 **Professional Integrations**

- **Database Integration** - CPU, Motherboard, Memory Kit databases
- **Cross-Brand Compatibility** - Intel, AMD platforms
- **Benchmark Integration** - Performance validation

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.9+ | 3.11+ |
| **OS** | Windows 10/11 or Linux | Ubuntu 22.04+/Fedora 38+ |
| **RAM** | 8 GB | 16 GB+ |
| **Storage** | 2 GB | 5 GB+ |
| **Hardware Access** | User | Admin/Root (for live tuning) |
| **GPU** | Optional | CUDA (for PyTorch AI acceleration) |

---

## 🎯 Interface Overview

| Tab | Description | Features |
|-----|-------------|----------|
| **⚙️ Manual Tuning** | Parameter tuning sandbox | Manual configuration, validation, JEDEC compliance |
| **⚡ Simulation** | Performance simulation | Bandwidth, latency, power, stability testing |
| **🧠 AI Optimization** | Automated optimization | GA, RL, and ensemble engines |
| **🎮 Gaming Performance** | Game-oriented tuning | Latency-focused profiles |
| **📊 Analysis** | Configuration analysis | Side-by-side comparisons |
| **🚀 Enhanced Features** | Advanced tools hub | 3D charts, AI assistant, monitoring |
| **📈 Benchmarks** | Performance validation | Benchmark scoring |
| **💻 Hardware Detection** | System profiling | Auto-detect RAM modules |
| **⚡ Live Tuning** | Real hardware control | Safety locks, backup/restore, emergency stops |
| **🔄 Cross-Brand Tuning** | Multi-platform support | Intel/AMD compatibility |
| **🔬 Advanced Integration** | Hardware databases | CPU/MB/RAM databases |

---

## 🧪 Testing & Quality

```bash
# Run tests
pytest tests/ -v

# Code quality checks
black src/ tests/ main.py
flake8 src/ tests/ main.py
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/
safety check
```

See also: `docs/TESTING.md` for a concise testing guide.

---

## 🔒 Safety Features

### Hardware Protection

- **Multi-level confirmations** before applying changes
- **Automatic parameter backup** and instant recovery
- **Real-time validation** of voltage/timing relationships
- **Emergency stop buttons** with immediate effect

### AI Safety

- **Bounded optimization** within safe parameter ranges
- **JEDEC compliance** checking for all configurations
- **Stability scoring** for parameter combinations
- **Gradual tuning** with incremental steps
- **Constraint repair** ensures every generated config satisfies DDR5 timing rules

### System Safety

- **Privilege escalation** warnings and confirmations
- **System monitoring** during live tuning sessions
- **Rollback mechanisms** for failed configurations

---

## 📊 Project Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Version** | 6.0.2 | ✅ Current |
| **Tests** | 98 passing | ✅ All Green |
| **DDR5 Frequencies** | 4000–8400 MT/s | ✅ JEDEC Compliant |
| **Platform Support** | Linux (full) / Windows (detection) / macOS (detection) | ✅ Cross-platform |
| **AI Engines** | GA, RL, Ensemble, AutoML | ✅ Advanced |
| **Safety** | Voltage clamping, timing validation, backup/restore | ✅ Secure |

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Add tests** for new functionality
4. **Run the test suite**: `pytest tests/`
5. **Submit a pull request**

### Development Setup

```bash
git clone https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner.git
cd ddr5-ai-memory-tuner
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

---

## 💝 Support the Project

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/killerbotofthenewworld)

Your support helps fund:

- **Hardware testing** on diverse platforms
- **AI model training** and optimization
- **New feature development**
- **Documentation** and tutorials

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔎 Keywords (for discovery)

- ddr5, ddr5-memory, ram, memory-tuning, overclocking, timing-optimization
- ai, machine-learning, reinforcement-learning, genetic-algorithm, optuna
- pytorch, scikit-learn, xgboost, lightgbm
- jedec, hardware-detection, performance-tuning
- streamlit, windows-installer, simulator, benchmark, optimization

---

## 🔗 Links

- **📖 Documentation**: GitHub Pages (auto-published from /docs)
- **🐛 Bug Reports**: <https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/issues>
- **💬 Discussions**: <https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/discussions>
- **📦 Releases**: <https://github.com/killerbotofthenewworld/ddr5-ai-memory-tuner/releases>

---

Built with ❤️ for the DDR5 optimization community
