# JCapy Plugin System

JCapy is designed to be extensible through a powerful plugin system. Plugins (also called "Skills") can add new commands, widgets, and capabilities to your One-Army Orchestrator.

## 1. Installing Existing Skills

You can install any JCapy skill hosted on a Git repository (like GitHub).

### Command
```bash
jcapy install <git_url>
```

### Example
To install the `hello-world` skill:
```bash
jcapy install https://github.com/ponli550/jcapy-skills/tree/main/examples/hello-world
```

This will:
1.  Clone the repository into `~/.jcapy/skills/<skill_name>`.
2.  Install any Python dependencies listed in `requirements.txt`.
3.  Register new commands automatically.

---

## 2. Creating Your Own Plugin (Local)

You can create private skills directly on your machine.

### Structure
Plugins live in `~/.jcapy/skills/`. Each plugin needs its own directory and a `jcapy.yaml` manifest.

```text
~/.jcapy/skills/
└── my-awesome-skill/
    ├── jcapy.yaml      # Manifest file
    ├── plugin.py       # Main python code
    └── requirements.txt # (Optional) Dependencies
```

### Step-by-Step Guide

1.  **Create the directory**:
    ```bash
    mkdir -p ~/.jcapy/skills/my-awesome-skill
    ```

2.  **Create the Manifest (`jcapy.yaml`)**:
    ```yaml
    name: my-awesome-skill
    version: 0.1.0
    description: "My custom commands to automate deployment"
    entry_point: plugin.py
    permissions:
      - network
      - file_system
    ```

3.  **Write the Code (`plugin.py`)**:
    ```python
    def run_deploy(args):
        print("🚀 Deploying to production...")
        # Your custom logic here

    def register_commands(registry):
        registry.register("deploy-prod", run_deploy, "Deploys the current project to production")
    ```

4.  **Test It**:
    Run `jcapy` and type `help`. You should see your new `deploy-prod` command listed!

---

## 3. Sharing Your Plugin

If you build something great, consider sharing it!
1.  Push your plugin directory to a GitHub repository.
2.  Anyone can then install it with `jcapy install <your-repo-url>`.
3.  Submit a PR to the [Official Skills Registry](https://github.com/ponli550/jcapy-skills) to get featured.
