# JCapy User Workflow: Building a Project

## Overview
This document illustrates the complete user journey when building a project using JCapy CLI commands.

---

## Terminology Reference

| JCapy Term | Industry Standard | Description |
|------------|-------------------|-------------|
| Framework | Template/Scaffold | Reusable code pattern with executable steps |
| Library | Knowledge Base | Collection of frameworks organized by domain |
| Persona | Workspace/Profile | Isolated environment with custom library |
| Harvest | Capture Pattern | Extract reusable code into a framework |
| Apply | Deploy Template | Inject framework code into current project |
| Brain | Repository | Personal or shared framework storage |

---

## User Workflow Diagram

```mermaid
flowchart TD
    subgraph SETUP["🚀 Setup Phase"]
        A[Developer starts new project] --> B[jcapy init]
        B --> C{Select Grade}
        C -->|A: Production| D[Full CI/CD, Tests, Security]
        C -->|B: Staging| E[Docker, Basic Tests]
        C -->|C: Prototype| F[Minimal setup]
    end

    subgraph PROFILE["👤 Profile Selection"]
        D & E & F --> G[jcapy persona]
        G --> H{Select Workspace}
        H -->|Programmer| I[Core Library]
        H -->|Custom| J[Personal Repository]
    end

    subgraph BUILD["🛠️ Development Phase"]
        I & J --> K[jcapy ls]
        K --> L[Browse available frameworks]
        L --> M{Need framework?}
        M -->|Yes| N[jcapy apply FRAMEWORK]
        M -->|No| O[Write code manually]
        N --> P[Template deployed to project]
        P --> Q{More frameworks?}
        Q -->|Yes| M
        Q -->|No| R[Continue development]
        O --> R
    end

    subgraph KNOWLEDGE["📚 Knowledge Management"]
        R --> S{New pattern discovered?}
        S -->|Yes| T[jcapy harvest]
        T --> U[Capture pattern as framework]
        U --> V[jcapy push]
        V --> W[Framework published to repository]
        S -->|No| X[Continue]
        W --> X
    end

    subgraph DEPLOY["🚀 Deployment Phase"]
        X --> Y[jcapy deploy]
        Y --> Z{Grade Check}
        Z -->|A| AA[Full pipeline: Tests + Security + Deploy]
        Z -->|B| AB[Docker compose up]
        Z -->|C| AC[Direct deploy]
    end

    subgraph SYNC["🔄 Sync Phase"]
        AA & AB & AC --> AD[jcapy sync]
        AD --> AE[Pull latest frameworks from cloud]
        AE --> AF[Ready for next iteration]
        AF --> K
    end

    style SETUP fill:#e1f5fe
    style PROFILE fill:#fff3e0
    style BUILD fill:#e8f5e9
    style KNOWLEDGE fill:#f3e5f5
    style DEPLOY fill:#ffebee
    style SYNC fill:#e0f7fa
```

---

## Command Reference by Phase

| Phase | Command | Purpose |
|-------|---------|---------|
| **Setup** | `jcapy init` | Scaffold project with grade selection |
| **Profile** | `jcapy persona` / `jcapy p` | Switch active workspace/profile |
| **Browse** | `jcapy ls` / `jcapy list` | View available frameworks |
| **Search** | `jcapy search QUERY` | Find frameworks by content |
| **Deploy Template** | `jcapy apply FRAMEWORK` | Inject framework into project |
| **Capture Pattern** | `jcapy harvest` / `jcapy new` | Extract new framework from code |
| **Deploy** | `jcapy deploy` | Grade-aware deployment pipeline |
| **Pull** | `jcapy sync` | Pull updates from repository |
| **Publish** | `jcapy push` | Upload local changes to repository |
| **Diagnose** | `jcapy doctor` / `jcapy chk` | Health-check system status |
| **Preferences** | `jcapy config` | View/set UX preferences |
| **Undo** | `jcapy undo` | Restore last deleted framework |
| **Onboarding** | `jcapy tutorial` | Interactive getting-started guide |

---

## Quick Start Example

```bash
# 1. Initialize project
mkdir my-app && cd my-app
jcapy init

# 2. Browse frameworks
jcapy ls

# 3. Deploy templates to project
jcapy apply deploy_react
jcapy apply structure_docs

# 4. Deploy to environment
jcapy deploy

# 5. Capture new patterns
jcapy harvest  # Extract pattern as reusable framework

# 6. Publish & sync with repository
jcapy push     # Publish to GitHub
jcapy sync     # Pull latest frameworks
```

---

## UX Configuration

Customize your JCapy experience:

```bash
# Set high-contrast theme
jcapy config set theme=high-contrast

# Disable contextual hints
jcapy config set hints=false

# Enable reduced motion (accessibility)
jcapy config set reduced_motion=true
```

Available themes: `default`, `high-contrast`, `monochrome`
