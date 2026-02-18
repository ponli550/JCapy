"""
JCapy UX Module: Audio & Animation Safety
"""
import os
import sys
import subprocess

def play_audio(event):
    """Play a sound based on the UX audio_mode preference."""
    try:
        from jcapy.config import get_ux_preference
        mode = get_ux_preference("audio_mode")
        if mode == "muted" or not mode:
            return

        if mode == "beeps":
            # Simple terminal bell
            print('\a', end='', flush=True)
            return

        if mode == "voice":
            voices = {
                "matrix_start": "J-Capy",
                "ready": "Ready to work, sir."
            }
            text = voices.get(event, "")
            if text:
                # Use macOS 'say' command
                subprocess.Popen(['say', '-v', 'Daniel', text])
            return

        if mode == "custom":
            # Use macOS 'afplay' with system sounds as default custom
            sounds = {
                "matrix_start": "/System/Library/Sounds/Tink.aiff",
                "logo_crystallize": "/System/Library/Sounds/Glass.aiff",
                "ready": "/System/Library/Sounds/Hero.aiff"
            }
            sound_path = sounds.get(event)
            if sound_path and os.path.exists(sound_path):
                subprocess.Popen(['afplay', sound_path])
            return

    except Exception:
        # Silently fail if something goes wrong with audio
        pass

def should_animate():
    """Check if animations should run"""
    if os.environ.get("JCAPY_REDUCED_MOTION"):
        return False
    if not sys.stdout.isatty():
        return False
    return True
