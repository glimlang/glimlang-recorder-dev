"""
Screen Recorder - A cross-platform Python desktop screen recording application.

This package provides modular components for screen recording with audio,
video overlays, and comprehensive user interface controls.
"""

__version__ = "1.0.0"
__author__ = "Screen Recorder Team"

from .core.config import RecorderConfig
from .core.video import ScreenRecorder
from .core.audio import AudioRecorder
from .ui.main_window import RecorderApp, create_app

__all__ = [
    "RecorderConfig",
    "ScreenRecorder", 
    "AudioRecorder",
    "RecorderApp",
    "create_app"
]
