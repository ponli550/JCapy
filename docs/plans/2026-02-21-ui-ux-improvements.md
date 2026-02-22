# JCapy UI/UX Improvements Plan

## Current State Audit

### TUI (Textual-based)
**Strengths:**
- Rich widget ecosystem (Kanban, GitLog, News, UsageTracker, etc.)
- Good keyboard navigation
- Edit mode for layout customization
- Zen mode for focus

**Pain Points:**
1. No live system stats (CPU, memory, task count)
2. Command input requires navigating to console drawer
3. No quick action bar for common commands
4. Status bar doesn't show enough context
5. No visual feedback for ZMQ/Web connection status

### Web UI (React-based)
**Strengths:**
- Modern glass-morphic design
- Kill switch intervention UI
- Connection status indicator

**Pain Points:**
1. No actual terminal output panel
2. No command input functionality (added but not tested)
3. Static "ClawEngine.v2" agent info (not real)
4. No persona/mode switching UI
5. Events panel is empty without running TUI

---

## Improvement Plan

### Phase 1: Web UI Terminal Panel (HIGH IMPACT)
- [ ] Add real terminal emulator panel showing TUI output
- [ ] Add command input with history
- [ ] Add persona quick-switch buttons
- [ ] Show real connection status with visual indicator

### Phase 2: TUI Quick Actions (HIGH IMPACT)
- [ ] Add quick action bar at bottom
- [ ] Add system stats widget (CPU, memory, tasks)
- [ ] Improve status HUD with connection info
- [ ] Add visual ZMQ status indicator

### Phase 3: Integration Polish
- [ ] Verify TUI → Web event flow works
- [ ] Add real-time updates to Web UI
- [ ] Test command execution from Web to TUI

### Phase 4: Visual Polish
- [ ] Consistent color scheme between TUI and Web
- [ ] Better error states
- [ ] Loading states

---

## Implementation Order

1. **Web UI Terminal Panel** - Most visible change
2. **TUI Quick Actions** - Improves daily workflow
3. **Connection Status** - Makes integration visible
4. **System Stats Widget** - Adds monitoring capability