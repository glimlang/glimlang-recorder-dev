"""Core recording functionality."""

from .config import RecorderConfig
from .video import ScreenRecorder
from .audio import AudioRecorder

__all__ = ["RecorderConfig", "ScreenRecorder", "AudioRecorder"]
