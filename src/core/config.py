"""
Configuration management for the Screen Recorder application.
Contains all configuration settings and data structures.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RecorderConfig:
    """Configuration settings for the screen recorder."""
    
    # Basic recording settings
    fps: int
    output_path: str
    monitor_index: int = 0  # 0 = full virtual screen in mss
    region: tuple | None = None  # (left, top, width, height)
    show_preview: bool = False
    
    # Mouse highlight settings
    mouse_highlight: bool = False
    mouse_color: tuple[int, int, int] = (0, 255, 255)  # BGR (yellow)
    mouse_radius: int = 20
    mouse_alpha: float = 0.35
    
    # Audio recording settings
    record_audio: bool = True  # Enable audio by default so voice is included
    audio_device: int | None = None
    audio_samplerate: int = 44100  # Standard CD quality
    audio_channels: int = 2        # Stereo for better quality
    system_audio_loopback: bool = False  # Windows WASAPI loopback for system audio
    save_audio_separately: bool = False  # Save audio as separate WAV file
    
    # Audio-Video synchronization settings
    precise_timing: bool = True    # Use precise frame timing for better sync
    sync_compensation: bool = True # Enable audio sync compensation in FFmpeg
    
    # Webcam Picture-in-Picture settings
    use_webcam: bool = False
    webcam_index: int = 0
    pip_position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right
    pip_width_pct: int = 20  # percent of video width
    
    # Video quality settings
    video_quality: str = "high"  # "low", "medium", "high", "ultra"
    hardware_acceleration: bool = True  # Try hardware encoders first
    use_segments: bool = False  # Split into segments for long recordings
    segment_duration_minutes: int = 60  # Max segment length
    
    # Performance settings
    buffer_size: int = 30  # Frame buffer size
    thread_pool_size: int = 4  # Number of processing threads
    
    # External tools
    ffmpeg_path: str | None = None
