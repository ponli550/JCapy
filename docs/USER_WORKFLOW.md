# JCapy User Workflow: Building a Project

## Overview
This document illustrates the complete user journey when building a project using JCapy CLI commands.

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

    subgraph PERSONA["👤 Persona Selection"]
        D & E & F --> G[jcapy persona]
        G --> H{Select Persona}
        H -->|Programmer| I[Core Library]
        H -->|Custom| J[Personal Brain]
    end

    subgraph BUILD["🛠️ Development Phase"]
        I & J --> K[jcapy ls]
        K --> L[Browse available skills]
        L --> M{Need skill?}
        M -->|Yes| N[jcapy apply SKILL_NAME]
        M -->|No| O[Write code manually]
        N --> P[Skill injected into project]
        P --> Q{More skills?}
        Q -->|Yes| M
        Q -->|No| R[Continue development]
        O --> R
    end

    subgraph KNOWLEDGE["📚 Knowledge Management"]
        R --> S{New pattern discovered?}
        S -->|Yes| T[jcapy harvest]
        T --> U[Create new skill from pattern]
        U --> V[jcapy push]
        V --> W[Skill saved to brain]
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
        AD --> AE[Pull latest skills from cloud]
        AE --> AF[Ready for next iteration]
        AF --> K
    end

    style SETUP fill:#e1f5fe
    style PERSONA fill:#fff3e0
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
| **Persona** | `jcapy persona` / `jcapy p` | Switch active brain/persona |
| **Browse** | `jcapy ls` / `jcapy list` | View available skills |
| **Search** | `jcapy search QUERY` | Find skills by content |
| **Apply** | `jcapy apply SKILL` | Inject skill into project |
| **Create** | `jcapy harvest` / `jcapy new` | Extract new skill from pattern |
| **Deploy** | `jcapy deploy` | Grade-aware deployment |
| **Sync** | `jcapy sync` | Pull updates from cloud |
| **Push** | `jcapy push` | Upload local changes |
| **Health** | `jcapy doctor` / `jcapy chk` | Check system status |

---

## Quick Start Example

```bash
# 1. Initialize project
mkdir my-app && cd my-app
jcapy init

# 2. Browse skills
jcapy ls

# 3. Apply useful skills
jcapy apply deploy_react
jcapy apply structure_docs

# 4. Deploy
jcapy deploy

# 5. Save new patterns
jcapy harvest  # Create skill from discovered pattern

# 6. Sync with cloud
jcapy push     # Upload to GitHub
jcapy sync     # Pull latest
```
