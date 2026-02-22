# JCapy Publishing Quick Reference

> One-page reference for publishing JCapy CLI, Daemon, and Web Control Plane

## 🚀 Quick Commands

```bash
# Development
make install              # Install all dependencies
make dev                  # Start CLI development
make dev-web              # Start web development
make test                 # Run tests
make build                # Build all artifacts

# Release
make release              # Interactive release script
make release-dry          # Dry-run (preview only)

# Docker
make docker-up            # Start daemon with docker-compose
make docker-logs          # View logs
make build-docker         # Build Docker image
```

## 📦 Publishing Targets

| Target | When | Workflow | Result |
|--------|------|----------|--------|
| **PyPI** | On release | `release.yml` | `pip install jcapy` |
| **Docker Hub** | On release | `docker-publish.yml` | `docker pull ponli550/jcapy` |
| **GHCR** | On release | `docker-publish.yml` | `docker pull ghcr.io/ponli550/jcapy` |
| **GitHub Pages** | On release | `web-deploy.yml` | Web UI on GitHub Pages |
| **Homebrew** | On release | `homebrew-bump.yml` | `brew install ponli550/jcapy/jcapy` |

## 🔄 Release Flow

```
git tag v4.1.9
git push origin v4.1.9
        │
        ▼
┌───────────────────┐
│ GitHub Actions    │
│   ├─ validate     │ ← Version consistency check
│   ├─ test         │ ← Run test suite
│   ├─ build-python │ ← Build wheel + sdist
│   ├─ publish-pypi │ ← Trusted Publishing (no tokens!)
│   ├─ build-docker │ ← Multi-platform images
│   └─ github-release│ ← Create release with notes
└───────────────────┘
        │
        ▼
   ✅ Published!
```

## 🔐 Required GitHub Secrets

| Secret | Purpose | Required For |
|--------|---------|--------------|
| `DOCKERHUB_USERNAME` | Docker Hub login | Docker Hub publishing |
| `DOCKERHUB_TOKEN` | Docker Hub token | Docker Hub publishing |
| `HOMEBREW_TAP_TOKEN` | PAT for tap repo | Homebrew formula bump |
| `CODECOV_TOKEN` | Coverage uploads | CI (optional) |

### PyPI Setup (Trusted Publishing - No Secrets!)

1. Go to PyPI → Manage Project → Publishing
2. Add GitHub repository: `ponli550/JCapy`
3. Add workflow: `release.yml`
4. That's it! No tokens needed.

## 📋 Pre-Release Checklist

```bash
# 1. Ensure tests pass
make test

# 2. Check code quality
make quality

# 3. Security audit
make security

# 4. Build locally
make build

# 5. Run release
make release
```

## 🛠️ Make Targets

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets |
| `make install` | Install all dependencies |
| `make test` | Run test suite with coverage |
| `make test-fast` | Run tests without coverage |
| `make lint` | Run linters (ruff) |
| `make format` | Format code (black, isort) |
| `make quality` | All quality checks |
| `make build` | Build Python + Web artifacts |
| `make build-docker` | Build Docker image |
| `make clean` | Clean build artifacts |
| `make check` | Run all checks (quality + test + security) |
| `make release` | Interactive release script |

## 🐳 Docker Quick Reference

```bash
# Pull from GHCR (recommended)
docker pull ghcr.io/ponli550/jcapy:latest
docker pull ghcr.io/ponli550/jcapy:4.1.8

# Pull from Docker Hub
docker pull ponli550/jcapy:latest

# Run daemon
docker run -d -p 8080:8080 ghcr.io/ponli550/jcapy

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Shell access
docker-compose exec jcapy bash
```

## 🍺 Homebrew Quick Reference

```bash
# Add tap
brew tap ponli550/jcapy

# Install
brew install jcapy

# Upgrade
brew upgrade jcapy

# Or one-liner
brew install ponli550/jcapy/jcapy
```

## 🐍 PyPI Quick Reference

```bash
# Install latest
pip install jcapy

# Install with all extras
pip install "jcapy[all]"

# Install specific version
pip install jcapy==4.1.8

# Install from TestPyPI (for testing)
pip install --index-url https://test.pypi.org/simple/ jcapy
```

## 🚨 Troubleshooting

### Docker build fails
```bash
# Check Dockerfile
docker build -f docker/Dockerfile -t jcapy:test .

# Check platform support
docker buildx ls
```

### PyPI upload fails
```bash
# Check with TestPyPI first
make build
twine upload --repository testpypi dist/*
```

### Web build fails
```bash
# Check Node version (20+)
node --version

# Reinstall dependencies
cd apps/web
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

## 📚 Full Documentation

- [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) - Complete publishing guide
- [INSTALLATION.md](INSTALLATION.md) - Installation instructions
- [DAEMON_DEPLOYMENT.md](DAEMON_DEPLOYMENT.md) - Docker/K8s deployment
- [CHANGELOG.md](../CHANGELOG.md) - Version history