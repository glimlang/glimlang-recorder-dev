"""
Clean configuration for the screen recorder.
Simplified settings with essential options only.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RecorderConfig:
    """
    Clean, simplified configuration for screen recording.
    Contains only essential settings for a clutter-free experience.
    """
    
    # Essential recording settings
    fps: int = 30
    output_path: str = "recording.mp4"
    
    # Basic audio settings
    record_audio: bool = True
    audio_device: int | None = None
    audio_samplerate: int = 44100
    audio_channels: int = 2
    
    # Essential video settings
    video_quality: str = "high"  # "low", "medium", "high", "ultra"
    hardware_acceleration: bool = True
    
    # Basic capture settings
    monitor_index: int = 0
    region: tuple[int, int, int, int] | None = None
    
    # Minimal optional features (all disabled by default for clean experience)
    show_preview: bool = False
    mouse_highlight: bool = False
    use_webcam: bool = False
    save_audio_separately: bool = False
    use_segments: bool = False
    
    # Performance settings (optimized defaults)
    buffer_size: int = 30
    thread_pool_size: int = 4
    precise_timing: bool = True
    sync_compensation: bool = True
    
    # FFmpeg path (auto-detected)
    ffmpeg_path: str | None = None
    
    # Advanced settings (hidden from UI, using optimal defaults)
    system_audio_loopback: bool = False
    webcam_index: int = 0
    pip_position: str = "bottom-right"
    pip_width_pct: int = 20
    segment_duration_minutes: int = 60
    mouse_color: tuple[int, int, int] = (0, 255, 255)
    mouse_radius: int = 20
    mouse_alpha: float = 0.35
    show_recording_indicator: bool = False
