# UX Module - Centralized UI/UX helpers for jcapy
from jcapy.ui.ux.feedback import with_spinner, progress_bar, show_success, show_error, show_warning
from jcapy.ui.ux.safety import confirm, UndoStack, require_dependency
from jcapy.ui.ux.hints import suggest_command, show_hint, Tutorial
from jcapy.ui.ux.a11y import get_color, announce, is_reduced_motion, THEMES

__all__ = [
    # Feedback
    'with_spinner', 'progress_bar', 'show_success', 'show_error', 'show_warning',
    # Safety
    'confirm', 'UndoStack', 'require_dependency',
    # Hints
    'suggest_command', 'show_hint', 'Tutorial',
    # Accessibility
    'get_color', 'announce', 'is_reduced_motion', 'THEMES',
]
