# JCapy Showcase Gallery

Welcome to the **"Ideally Lazy Engineer's" Recipe Book**.

This gallery contains **10 verified use case scenarios** demonstrating how JCapy can be used as a Universal Knowledge Harvester across different engineering roles.

## What's Inside?

| Role | Directory | Scenario |
|------|-----------|----------|
| **Backend** | `01-backend-api/` | Harvesting a FastAPI Microservice Scaffold |
| **Frontend** | `02-frontend-ui/` | Creating a reusable React Component Library |
| **Data Science** | `03-data-science/` | Standardizing ML Training Pipelines |
| **Security** | `04-security/` | Automating Security Audits |
| **QA** | `05-qa/` | Setting up Cypress E2E Testing |
| **SRE** | `06-sre/` | Incident Response Diagnostics |
| **Mobile** | `07-mobile/` | Automated iOS Deployment (Fastlane) |
| **DBA** | `08-dba/` | Database Backup Strategy |
| **Tech Writer** | `09-tech-writer/` | Documentation Site Setup (MkDocs) |
| **Product Manager** | `10-product-manager/` | PRD Templates |

## How to Run a Demo
Each directory contains a `usecase.sh` script that:
1.  Initializes a temporary workspace.
2.  Creates the artifact (code/config/docs).
3.  Harvests it into your JCapy library.
4.  Applies it back to verify reuse.

To run a specific scenario:
```bash
./showcase/01-backend-api/usecase.sh
```

To run the full "Master Demo" (all 10 scenarios):
```bash
./scripts/run_all_usecases.sh
```

## Creating Your Own Gallery Item
1.  Create a directory: `showcase/my-role/`.
2.  Add your artifact file (e.g., `MyConfig.yml`).
3.  Create a `usecase.sh` following the template in other directories.
