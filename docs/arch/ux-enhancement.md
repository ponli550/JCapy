# JCapy UI/UX Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a centralized UX module providing visual feedback, error recovery, discoverability, and accessibility features for JCapy CLI.

**Architecture:** Create `ui/ux/` subpackage with 4 modules (`feedback.py`, `safety.py`, `hints.py`, `a11y.py`) plus shared config. Commands import UX helpers; all preferences stored in `~/.jcapyrc`.

**Tech Stack:** Python 3.11+, Rich (already dependency), curses (stdlib), difflib (stdlib for typo matching)

---

## Proposed Changes

### UX Module Foundation

#### [NEW] `src/jcapy/ui/ux/__init__.py`
Package init exporting public API.

#### [NEW] `src/jcapy/ui/ux/feedback.py`
- `with_spinner(message)` decorator for slow operations
- `progress_bar(title, total)` context manager
- `show_success/error/warning(msg, hint=None)` banner functions
- Respects `--quiet` flag and `reduced_motion` config

#### [NEW] `src/jcapy/ui/ux/safety.py`
- `UndoStack` class managing `~/.jcapy/undo/` directory
- `confirm(msg, destructive=False)` prompt with color coding
- `@require_dependency(name, fallback)` decorator
- Auto-cleanup of backups older than 7 days

#### [NEW] `src/jcapy/ui/ux/hints.py`
- `suggest_command(typo, commands)` using difflib.get_close_matches
- `show_hint(msg)` contextual tip display
- `Tutorial` class with step tracking in `~/.jcapy/tutorial.json`

#### [NEW] `src/jcapy/ui/ux/a11y.py`
- `THEMES` dict with `default`, `high-contrast`, `monochrome`
- `announce(msg, urgent=False)` screen reader helper
- `get_color(name)` returning theme-aware ANSI codes
- `is_reduced_motion()` checking config and system preference

---

### Config Integration

#### [MODIFY] `src/jcapy/config.py`
Add UX preference keys: `theme`, `hints`, `reduced_motion`, `quiet`

---

### Command Integration

#### [MODIFY] `src/jcapy/main.py`
- Add `undo` and `tutorial` subcommands
- Add `config` subcommand for setting preferences
- Integrate typo suggestion in command router fallback

#### [MODIFY] `src/jcapy/commands/sync.py`
- Wrap `sync_all_personas` with `@with_spinner`
- Wrap `push_all_personas` with `@with_spinner`

#### [MODIFY] `src/jcapy/commands/skills.py`
- Add undo support to `delete_skill`
- Add confirmation prompt to `delete_skill`
- Show contextual hint after `harvest_skill`

#### [MODIFY] `src/jcapy/commands/project.py`
- Wrap `deploy_project` with progress bar
- Show success banner on completion

---

### Tests

#### [NEW] `tests/test_feedback.py`
Tests for spinner, progress bar, and banner functions.

#### [NEW] `tests/test_safety.py`
Tests for undo stack, confirm prompts, dependency decorator.

#### [NEW] `tests/test_hints.py`
Tests for typo suggestions, hints display, tutorial state.

#### [NEW] `tests/test_a11y.py`
Tests for theme colors, announce function, reduced motion.

---

## Verification Plan

### Automated Tests

```bash
# Run all UX tests (from jcapy directory)
cd .
python -m pytest tests/ -v

# Run specific module tests
python -m pytest tests/test_feedback.py -v
python -m pytest tests/test_safety.py -v
python -m pytest tests/test_hints.py -v
python -m pytest tests/test_a11y.py -v
```

### Manual Verification

1. **Spinners**: Run `jcapy sync` and observe spinner animation
2. **Banners**: Run `jcapy harvest` and complete wizard, observe success banner
3. **Undo**: Delete a skill with `jcapy delete <name>`, then run `jcapy undo`
4. **Confirm**: Run `jcapy delete <name>` and verify red `[y/N]` prompt
5. **Typo**: Run `jcapy delpoy` and verify "Did you mean 'deploy'?" suggestion
6. **Tutorial**: Run `jcapy tutorial` and step through onboarding
7. **High-Contrast**: Run `jcapy config set theme=high-contrast`, then `jcapy help`
8. **Reduced Motion**: Run `jcapy config set reduced_motion=true`, then `jcapy sync`

### Accessibility Testing

- Enable VoiceOver (macOS: Cmd+F5)
- Run `jcapy list` and verify skill count is announced
- Navigate TUI and verify state changes are spoken
