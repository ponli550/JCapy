# JCapy Web Control Plane Implementation Plan

> [!IMPORTANT]
> **Premium Skill Active: writing-plans**
> I am using the `writing-plans` workflow to detail the JCapy Web Control Plane.
> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Build the JCapy Web Control Plane serving as an Orbital Hub and Security Command Center, featuring a real-time Reasoning Stream and Kill Switch.

**Architecture:** A single-page application (React + Vite) adhering to the One-Army `TEMPLATE_FRONT_ARCHITECTURE2.md`. It acts as a local-first bridge connecting directly to the developer's laptop `localhost:jcapyd`.

**Tech Stack:** React, Vite, Tailwind CSS (Glassmorphism), TypeScript, Framer Motion, Lucide React.

---

### Task 1: Scaffold the Web Application & Design System

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/tailwind.config.js`
- Create: `apps/web/index.css`

**Step 1: Write the failing test**
*Skipped for scaffolding, verification is a successful dev build.*

**Step 2: Run test to verify it fails**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| FAIL | `cd apps/web && npm run build` | `ENOENT: no such file or directory` |

**Step 3: Write minimal implementation**
1. Run Vite scaffold: `npm create vite@latest apps/web -- --template react-ts`
2. Install dependencies: `npm i -D tailwindcss postcss autoprefixer`, then `npx tailwindcss init -p`
3. Install UI libs: `npm i framer-motion lucide-react`
4. Setup `tailwind.config.js` with Glassmorphism tokens (`bg-glass`, `var(--primary)`).

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `cd apps/web && npm run build` | `dist/ built successfully` |

**Step 5: Commit**

```bash
git add apps/web
git commit -m "chore(web): scaffold web control plane with React/Vite/Tailwind"
```

---

### Task 2: Build the One-Army Dashboard Layout & Kill Switch (ASI08)

**Files:**
- Create: `apps/web/src/components/layout/DashboardLayout.tsx`
- Create: `apps/web/src/components/ui/KillSwitch.tsx`

**Step 1: Write the failing test**

```tsx
// tests/layout.test.tsx
import { render, screen } from '@testing-library/react';
import { DashboardLayout } from '../components/layout/DashboardLayout';

test('renders the global kill switch securely', () => {
    render(<DashboardLayout title="Hub" />);
    expect(screen.getByText(/KILL SWITCH/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| FAIL | `npm test` | `tests/layout.test.tsx fails: module not found` |

**Step 3: Write minimal implementation**
Implement the synthesized layout from the brainstorming session:
- **Header**: Persistent Connection Status ("Daemon Synced") and the Red `KillSwitch` component.
- **Sidebar**: The `Capability Manifest` block showing active agent scopes (Read/Write/Network).

```tsx
// apps/web/src/components/layout/DashboardLayout.tsx
export function DashboardLayout({ children }) {
    return (
        <div className="flex h-screen bg-slate-900 text-white">
            <aside className="w-64 bg-slate-800/50 backdrop-blur border-r border-slate-700 p-4">
                <CapabilityManifest />
            </aside>
            <div className="flex-1 flex flex-col">
                <header className="h-16 border-b border-slate-700 flex items-center justify-between px-6 bg-slate-800/80">
                    <span>Connection: [O] Daemon Synced (localhost)</span>
                    <KillSwitch />
                </header>
                <main className="p-6">{children}</main>
            </div>
        </div>
    );
}
```

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `npm test layout.test.tsx` | `1 passed` |

**Step 5: Commit**

```bash
git add apps/web/src/components/
git commit -m "feat(ui): implement DashboardLayout featuring global Kill Switch and Capability Sidebar"
```

---

### Task 3: Implement the Real-time Reasoning Stream via Orbital Bridge

**Files:**
- Create: `apps/web/src/components/pages/ReasoningStream.tsx`
- Create: `apps/web/src/components/ui/ToolProxyBlock.tsx`
- Create: `apps/web/src/services/daemonBridge.ts`

**Goal:** Connect the Web UI to the `jcapyd` Daemon using a WebSocket proxy (translating gRPC/ZeroMQ to Web-friendly streams).

**Step 1: Implement the daemonBridge service**
This service connects to the `jcapyd` ZeroMQ log stream (standardized in the Orbital plan) and decodes `LogEntry` and `TrajectoryEvent` protobufs.

**Step 2: Build the ReasoningStream component**
- Subscribe to `daemonBridge`.
- Filter for `thought` and `action` event types.
- Implement the `ToolProxyBlock` for 'await_approval' events.

**Step 3: Implementation of Approve/Reject RPCs**
When the operator clicks "Approve", call the `jcapyd.ExecuteApproval(event_id, approved=True)` RPC.

**Step 4: Run test to verify it passes**

| Phase | Command | Expected Outcome |
|-------|---------|------------------|
| PASS | `npm test stream.test.tsx` | `1 passed` |

**Step 5: Commit**

```bash
git add apps/web/src/
git commit -m "feat(ui): build real-time reasoning stream with interactive Tool Proxy diffs"
```
