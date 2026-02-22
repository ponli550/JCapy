# Showcase: The One-Army V2 Experience

This scenario demonstrates the full capabilities of JCapy 2.0.0, from cinematic orchestration to secure tool execution.

## 🎬 Part 1: Cinematic Ignition
Launch JCapy to witness the holographic crystallization reveal.
```bash
jcapy
```
- **Visuals**: Matrix-inspired rain transitions into the high-contrast JCapy logo.
- **Initialization**: Real-time status logs verify the `EventBus` and `Sandbox` acquisition.

## 🧠 Part 2: The Cognitive Split (Planning)
Ask a complex architectural question to trigger the **Sentinel**.
```bash
jcapy ask "Redesign our microservices for high-availability using the one-army pattern" --cognitive
```
- **The Sentinel**: Analyzes the request and drafts a multi-step `ExecutionPlan`.
- **Approval Flow**: The TUI prompts you to review the plan, highlighting estimated impact and security permissions.

## 🛡️ Part 3: Secure Execution (Sandboxing)
Approving the plan triggers the **Executor** in a secure environment.
- **Isolated Execution**: Tools run in a Docker or Local Sandbox.
- **Event Bus Monitoring**: Watch the `AuditLogger` capture every `TOOL_CALL` via the async bus.
- **Circuit Breaker**: Try to force a recursive failure and witness JCapy's automatic protection arming.

## 🧘 Part 4: Zen Mode Mastery
Focus on the generated reports using the refined Zen mode.
- **Command**: Press `z` in the dashboard.
- **Result**: All UI chrome disappears, leaving a pure, distraction-free environment for deep reading.

## 📡 Part 5: Observability Audit
Verify the governance trail.
```bash
cat ~/.jcapy/audit.jsonl | tail -n 5
```
- **Traceability**: Every plan step, tool result, and bus event is indexed and ready for governance review.
