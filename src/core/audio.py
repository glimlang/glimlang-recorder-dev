"""
Audio recording functionality for the Screen Recorder application.
Handles microphone input and system audio loopback recording.
"""

import os
import queue
import tempfile
import threading
import datetime as dt
from typing import Any, Optional, Callable

# Optional dependencies - will be checked at runtime
try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    sd = None
    sf = None


class AudioRecorder:
    """
    Handles audio recording from microphone or system loopback.
    Supports Windows WASAPI loopback for system audio capture.
    """
    
    def __init__(
        self, 
        samplerate: int, 
        channels: int, 
        device: Optional[int], 
        loopback: bool = False,
        status_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize audio recorder.
        
        Args:
            samplerate: Audio sample rate (e.g., 48000)
            channels: Number of audio channels (1 for mono, 2 for stereo)
            device: Audio device ID (None for default)
            loopback: Whether to use system audio loopback (Windows only)
            status_callback: Optional callback for status updates
        """
        if sd is None or sf is None:
            raise RuntimeError("Audio dependencies missing (sounddevice, soundfile)")
            
        self.samplerate = int(samplerate)
        self.channels = int(channels)
        self.device = device
        self.loopback = bool(loopback)
        self.status_callback = status_callback or (lambda msg: None)
        
        # Internal state
        self._q = queue.Queue(maxsize=64)
        self._stop = threading.Event()
        self.wav_path = os.path.join(
            tempfile.gettempdir(), 
            dt.datetime.now().strftime("_audio_%Y%m%d_%H%M%S.wav")
        )
        
        # Runtime objects (avoid referencing optional modules in annotations)
        self._sf = None
        self._stream = None
        self._writer_thread = None

    def start(self) -> None:
        """Start audio recording."""
        if sd is None or sf is None:
            raise RuntimeError("Audio dependencies not available")
            
        try:
            # Create audio file writer
            self._sf = sf.SoundFile(
                self.wav_path, 
                mode='w', 
                samplerate=self.samplerate, 
                channels=self.channels, 
                subtype='PCM_16'
            )
            
            # Configure stream settings
            extra_settings = None
            if self.loopback and os.name == 'nt' and hasattr(sd, 'WasapiSettings'):
                try:
                    extra_settings = sd.WasapiSettings(exclusive=False)  # Use available parameter
                    self.status_callback("Using Windows WASAPI for system audio")
                except Exception as ex:
                    self.status_callback(f"WASAPI setup failed: {ex}")
                    extra_settings = None
                    
            if self.loopback and os.name != 'nt':
                raise RuntimeError('System audio loopback is only supported on Windows WASAPI')
            
            # Create and start audio stream
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype='int16',
                device=self.device,
                callback=self._audio_callback,
                extra_settings=extra_settings
            )
            self._stream.start()
            
            # Start writer thread
            self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
            self._writer_thread.start()
            
            self.status_callback(f"Audio recording started: {self.wav_path}")
            
        except Exception as ex:
            self._cleanup()
            raise RuntimeError(f"Failed to start audio recording: {ex}")

    def stop(self) -> None:
        """Stop audio recording and cleanup resources."""
        self._stop.set()
        
        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
        except Exception:
            pass
            
        if self._writer_thread:
            self._writer_thread.join(timeout=3)
            
        if self._sf is not None:
            try:
                self._sf.flush()
                self._sf.close()
            except Exception:
                pass
                
        self.status_callback("Audio recording stopped")

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        """Audio stream callback - processes incoming audio data."""
        if status:
            # Log audio stream status issues if needed
            pass
            
        try:
            # Queue audio data for writing (non-blocking)
            self._q.put_nowait(indata.copy())
        except queue.Full:
            # Drop frames if queue is full (prevents blocking)
            pass

    def _writer_loop(self) -> None:
        """Background thread that writes queued audio data to file."""
        while not self._stop.is_set() or not self._q.empty():
            try:
                data = self._q.get(timeout=0.2)
            except queue.Empty:
                continue
                
            if self._sf is not None:
                try:
                    self._sf.write(data)
                except Exception:
                    # Continue recording even if individual writes fail
                    pass

    def _cleanup(self) -> None:
        """Internal cleanup method."""
        if self._sf is not None:
            try:
                self._sf.close()
            except Exception:
                pass
            self._sf = None


def get_audio_devices(loopback: bool = False) -> list[tuple[str, Optional[int]]]:
    """
    Get list of available audio devices.
    
    Args:
        loopback: If True, get output devices for loopback recording
        
    Returns:
        List of (device_name, device_id) tuples
    """
    devices: list[tuple[str, Optional[int]]] = [("Default", None)]
    
    if sd is None:
        return devices
        
    try:
        for idx, device_info in enumerate(sd.query_devices()):
            try:
                if isinstance(device_info, dict):
                    # Check if device supports input (for microphone) or output (for loopback)
                    if loopback:
                        max_channels = int(device_info.get('max_output_channels', 0))
                    else:
                        max_channels = int(device_info.get('max_input_channels', 0))
                        
                    if max_channels > 0:
                        name = device_info.get('name', f'Device {idx}')
                        devices.append((f"{idx}: {name}", idx))
                else:
                    # Fallback for non-dict device info
                    devices.append((f"{idx}: {str(device_info)}", idx))
                    
            except Exception:
                # Skip problematic devices
                continue
                
    except Exception:
        # Return default if device enumeration fails
        pass
        
    return devices


def is_audio_available() -> bool:
    """Check if audio recording dependencies are available."""
    return sd is not None and sf is not None
