# JCapy Skills Registry

This repository contains official and community-contributed skills for the [JCapy](https://github.com/ponli550/jcapy) Orchestrator.

## 🏗️ Structure

Skills are organized into directories, each containing:
- `jcapy.yaml`: The Skill Manifest (metadata, commands, and permissions).
- `SKILL.md`: Detailed instructions for the agent on how to use the skill.
- `scripts/`: (Optional) Helper scripts.

## 🗃️ Central Registry

The registry is indexed by [registry.yaml](./registry.yaml). This file tracks:
- **Official Skills**: Core skills developed by the JCapy team.
- **Extensions**: Community-developed plugins.

## 🧩 Anatomy of a Skill Manifest

```yaml
name: "systematic-debugging"
version: "1.0.0"
category: "tactical"
description: "Industry-standard debugging patterns."
permissions:
  - "terminal.read"
  - "file.write"
dependencies: []
```

## 🛠️ Loading Skills

To load skills from this registry into your local JCapy instance:

```bash
jcapy sync
```

To create a new skill in this registry, use the [Writing Skills Guide](https://github.com/irfansoftstudio/jcapy/docs/guides/writing-skills.md).
