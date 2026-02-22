# Changelog

All notable changes to JCapy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive publishing infrastructure for PyPI, Docker, and Homebrew
- GitHub Actions CI/CD workflows for automated testing and releases
- Makefile for streamlined development commands
- Multi-platform Docker images (linux/amd64, linux/arm64)
- SBOM and provenance attestations for Docker images
- GitHub Pages deployment for Web Control Plane

## [4.1.8] - 2025-02-21

### Added
- Web Control Plane with real-time dashboard
- Daemon mode for background operation
- MCP (Model Context Protocol) integration
- Skill system for extensible functionality
- Memory system with ChromaDB integration
- Telemetry and observability features

### Changed
- Improved TUI with Textual framework
- Enhanced security with circuit breaker pattern
- Better error handling and user feedback

### Fixed
- Various bug fixes and performance improvements

## [4.1.0] - 2025-02-15

### Added
- Interactive mission control dashboard
- Dual-terminal support for TUI
- Widget furnishing system
- AContext orbital integration

### Changed
- Refactored framework engine decoupling
- Improved framework interface

## [4.0.0] - 2025-02-01

### Added
- Complete rewrite with modern architecture
- Agentic security architecture
- Hybrid TUI/Web integration
- Knowledge Lakehouse concept

### Changed
- Breaking changes from v3.x
- New plugin architecture

## [3.x] - 2024

### Note
Legacy versions. See git history for details.

---

## Release Notes Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Deprecated
- Features to be removed in future releases

### Removed
- Features removed in this release

### Fixed
- Bug fixes

### Security
- Security improvements
```

## Publishing Targets

| Target | URL | Command |
|--------|-----|---------|
| PyPI | https://pypi.org/project/jcapy/ | `pip install jcapy` |
| Docker Hub | https://hub.docker.com/r/ponli550/jcapy | `docker pull ponli550/jcapy` |
| GHCR | ghcr.io/ponli550/jcapy | `docker pull ghcr.io/ponli550/jcapy` |
| Homebrew | github.com/ponli550/homebrew-jcapy | `brew install ponli550/jcapy/jcapy` |