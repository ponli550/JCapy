# Design: Widget System Furnishing
**Date**: February 18, 2026
**Status**: ✅ Implemented

## Overview
As JCapy 2.0 moves towards a decoupled "Orbital Architecture," the dashboard must evolve from a static monitoring tool into an interactive, high-fidelity mission control. This update, known as "Furnishing," introduces bidirectional interactivity, telemetry visualization, and dynamic extensibility.

## Core Pillars

### 1. Command & Control (Bidirectional Interactivity)
Traditional dashboard widgets are read-only. We implemented an **Action Bar** system using a standardized `.widget-action-bar` CSS class.
- **Git Integration**: Direct `Push` and `Sync` actions from the UI.
- **FS Exploration**: Seamless pivoting from file selection to internal terminal/command execution.
- **Automation**: One-click task archiving within the Kanban loop.

### 2. The Intelligence Pulse (Telemetry)
To build trust in the AI's autonomous actions, we introduced the `AIAgentWidget`.
- **Thought Visualization**: Exposes the internal reasoning chain of the orchestrator.
- **Confidence Scoring**: Real-time progress bars representing model certainty.
- **Consumption Sparklines**: TUI-native sparkline charts (using Unicode block elements) for monitoring token consumption rates and session costs.

### 3. State-of-the-Art Aesthetics
Visual polish is used to enhance usability, not just for "WOW" factor.
- **Cinematic Transitions**: Hover and focus states use CSS transitions for depth and responsiveness.
- **Glassmorphism Refinement**: Improved transparency layers and accent bordering for a premium HUD feel.

### 4. Open-Platform Extensibility
The dashboard is now a platform, not a monolith.
- **Dynamic Discovery**: A hot-loading logic in `WidgetRegistry` that scans `~/.jcapy/widgets` for Python-based extensions.
- **Extensible Registry**: Allows 1st and 3rd party widgets to be registered with identically ranked lifecycle hooks and styling access.

## Technical Implementation Notes
- **Layout Engine**: Leverages Textual's fractional containers with custom `Splitter` components that intercept and persist dimension changes to the user's config.
- **Inter-Widget Communication**: Uses Textual's message-passing system for notifying the UI of background events (e.g., `ConfigUpdated`, `SplitterUpdated`).
