# JCapy Publishing Guide

> **Top-Notch Standard Publishing Strategy for JCapy CLI, Daemon, and Web Control Plane**

This guide covers the complete publishing workflow for all JCapy components following industry best practices.

---

## 📦 Publishing Targets

| Component | Target | Artifact Type |
|-----------|--------|---------------|
| **jcapy CLI** | PyPI | Python Wheel + Sdist |
| **jcapy Web** | npm / GitHub Pages | Static Assets |
| **jcapy Daemon** | Docker Hub + GHCR | Container Image |
| **Homebrew** | homebrew-jcapy | Formula |
| **Documentation** | GitHub Pages | Static Site |

---

## 🚀 Quick Start

```bash
# Full release (interactive)
./scripts/publish.sh

# Dry-run to preview
./scripts/publish.sh --dry-run

# Force mode (skip confirmations)
./scripts/publish.sh --force
```

---

## 1. PyPI Publishing (CLI)

### Prerequisites

1. **Trusted Publishing** (Recommended - No API tokens needed)
   - Configure in PyPI project settings
   - Already set up in `.github/workflows/market-release.yml`

2. **Or API Token** (Legacy)
   ```bash
   # Create ~/.pypirc
   [pypi]
     username = __token__
     password = pypi-...
   ```

### Manual Publish

```bash
# Build
python -m build

# Check
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to Production
twine upload dist/*
```

### Automated (GitHub Release)

Creating a GitHub Release automatically triggers PyPI publishing via `market-release.yml`.

---

## 2. Docker Publishing (Daemon)

### Multi-Registry Strategy

We publish to both **Docker Hub** and **GitHub Container Registry (GHCR)** for maximum availability.

### Prerequisites

```bash
# Docker Hub login
docker login

# GHCR login (uses GitHub token)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Manual Publish

```bash
# Build with version tag
docker build -f docker/Dockerfile -t jcapy:4.1.8 .

# Tag for registries
docker tag jcapy:4.1.8 ponli550/jcapy:4.1.8
docker tag jcapy:4.1.8 ponli550/jcapy:latest
docker tag jcapy:4.1.8 ghcr.io/ponli550/jcapy:4.1.8
docker tag jcapy:4.1.8 ghcr.io/ponli550/jcapy:latest

# Push to Docker Hub
docker push ponli550/jcapy:4.1.8
docker push ponli550/jcapy:latest

# Push to GHCR
docker push ghcr.io/ponli550/jcapy:4.1.8
docker push ghcr.io/ponli550/jcapy:latest
```

### Docker Compose (Production)

```bash
# Using Docker Hub
docker-compose up -d

# Using GHCR
docker-compose -f docker-compose.ghcr.yml up -d
```

---

## 3. Web Control Plane Publishing

### Option A: Embedded in Python Package

The web assets are embedded in the Python package and served by the daemon:

```bash
# Build web assets
cd apps/web && npm run build

# Assets are included in Python package via MANIFEST.in
```

### Option B: Standalone Deployment (CDN/Static)

For deploying the web UI separately:

```bash
# Build for production
cd apps/web
npm run build

# Deploy to:
# - GitHub Pages
# - Cloudflare Pages
# - Vercel
# - Netlify
```

### GitHub Pages Deployment

Web assets can be deployed to GitHub Pages via the `web-deploy.yml` workflow.

---

## 4. Homebrew Publishing

### Automatic (via publish.sh)

```bash
./scripts/publish.sh
# Select "Yes" when prompted for Homebrew update
```

### Manual Update

```bash
# Get SHA256
curl -sL https://github.com/ponli550/JCapy/archive/refs/tags/v4.1.8.tar.gz | shasum -a 256

# Update formula in homebrew-jcapy repo
# Push changes
```

---

## 5. GitHub Releases

### Automated Release Notes

Releases are automated via GitHub Actions. The workflow:
1. Builds and tests the package
2. Creates a draft release with auto-generated notes
3. Publishes to PyPI on release
4. Builds and pushes Docker images

### Manual Release

```bash
# Create tag
git tag v4.1.8

# Push tag
git push origin v4.1.8

# Go to GitHub > Releases > Draft new release
# Or use gh CLI:
gh release create v4.1.8 --title "v4.1.8" --notes-file RELEASE_NOTES.md
```

---

## 📋 Publishing Checklist

### Pre-Release

- [ ] All tests pass: `pytest tests/`
- [ ] Version bumped in `pyproject.toml` and `src/jcapy/utils/updates.py`
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Security audit: `pip-audit`

### Release

- [ ] Run `./scripts/publish.sh`
- [ ] Verify PyPI package: `pip install jcapy==X.Y.Z`
- [ ] Verify Docker image: `docker pull ponli550/jcapy:X.Y.Z`
- [ ] Verify Homebrew: `brew install ponli550/jcapy/jcapy`

### Post-Release

- [ ] GitHub release published
- [ ] Social announcement (if major release)
- [ ] Update documentation site

---

## 🔐 Security Best Practices

1. **Trusted Publishing** - Use OIDC for PyPI (no tokens in CI)
2. **Signed Commits** - All release commits should be signed
3. **Attestations** - Docker images include SBOM and provenance
4. **Secret Scanning** - GitHub automatically scans for leaked secrets
5. **Dependabot** - Enabled for dependency updates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PUBLISHING PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
│  │   Git    │───>│ GitHub   │───>│ PyPI (Trusted Publishing)│  │
│  │  Tag     │    │ Actions  │    │ pip install jcapy        │  │
│  └──────────┘    └────┬─────┘    └──────────────────────────┘  │
│                       │                                         │
│                       ├──> ┌────────────────────────────────┐  │
│                       │    │ Docker Hub                     │  │
│                       │    │ docker pull ponli550/jcapy     │  │
│                       │    └────────────────────────────────┘  │
│                       │                                         │
│                       ├──> ┌────────────────────────────────┐  │
│                       │    │ GHCR                           │  │
│                       │    │ docker pull ghcr.io/ponli550/  │  │
│                       │    └────────────────────────────────┘  │
│                       │                                         │
│                       └──> ┌────────────────────────────────┐  │
│                            │ Homebrew Tap                    │  │
│                            │ brew install ponli550/jcapy/jcapy│ │
│                            └────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Related Documentation

- [Installation Guide](INSTALLATION.md)
- [Docker Deployment](DAEMON_DEPLOYMENT.md)
- [Developer Guide](guides/developer-guide.md)