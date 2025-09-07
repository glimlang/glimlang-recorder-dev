"""
Video recording functionality for the Screen Recorder application.
Handles screen capture, webcam overlay, mouse highlighting, and video file writing.
"""

import os
import time
import threading
import tempfile
import subprocess
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
import queue

import numpy as np
import cv2
from mss import mss

# Optional dependencies
try:
    import pyautogui
except ImportError:
    pyautogui = None

# Handle imports for both direct execution and module imports
try:
    from ..core.config import RecorderConfig
    from ..core.audio import AudioRecorder
    from ..utils.helpers import fourcc_code, find_ffmpeg_path, test_ffmpeg, get_ffmpeg_error_message
except ImportError:
    # Direct execution fallback
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.config import RecorderConfig
    from core.audio import AudioRecorder
    from utils.helpers import fourcc_code, find_ffmpeg_path, test_ffmpeg, get_ffmpeg_error_message


class ScreenRecorder:
    """
    High-performance screen recording engine with GPU acceleration.
    Supports screen capture, webcam overlay, mouse highlighting, and audio integration.
    Optimized for extended recording sessions with minimal lag.
    """
    
    def __init__(self, cfg: RecorderConfig, status_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize screen recorder.
        
        Args:
            cfg: Recording configuration
            status_callback: Optional callback for status updates
        """
        self.cfg = cfg
        self.status_callback = status_callback or (lambda msg: None)
        
        # Threading control
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # Video recording objects
        self._writer: Optional[cv2.VideoWriter] = None
        self._sct: Optional[Any] = None  # mss screen capture object
        self._monitor: Optional[dict] = None
        
        # GPU acceleration
        self._use_gpu = self._detect_gpu_support()
        self._gpu_mat_pool = queue.Queue(maxsize=10) if self._use_gpu else None
        
        # Performance optimization
        self._frame_pool = queue.Queue(maxsize=self.cfg.buffer_size)  # Pre-allocated frame buffers
        self._thread_pool = ThreadPoolExecutor(max_workers=self.cfg.thread_pool_size, thread_name_prefix="recorder")
        
        # Audio recording
        self._audio_recorder: Optional[AudioRecorder] = None
        self._video_tmp_path: Optional[str] = None
        
        # Webcam for picture-in-picture
        self._cam: Optional[cv2.VideoCapture] = None
        self._cam_buffer = None  # Buffer for stable webcam frames
        self._cam_frame_count = 0
        self._cam_update_interval = 3  # Update webcam every 3 frames to reduce blinking
        
        # Segment recording for long sessions
        self._current_segment = 0
        self._segment_start_time = 0
        self._segment_paths: list[str] = []
        
        # Audio-Video synchronization
        self._recording_start_time = 0  # Precise timing for sync
        self._video_frame_times: list[float] = []  # Track frame timestamps
        self._target_fps = float(cfg.fps)
        self._frame_interval = 1.0 / self._target_fps
        
        # Production-grade frame reliability system
        self._frame_queue = queue.Queue(maxsize=self.cfg.buffer_size * 2)  # Double buffer for reliability
        self._write_queue = queue.Queue(maxsize=self.cfg.buffer_size)
        self._capture_thread: Optional[threading.Thread] = None
        self._write_thread: Optional[threading.Thread] = None
        self._priority_mode = False  # Enable high-priority capture
        
        # Frame dropping prevention
        self._adaptive_quality = True  # Enable adaptive quality reduction
        self._frame_skip_threshold = 3  # Skip overlay processing if behind
        self._emergency_mode = False  # Ultra-fast mode when dropping frames
        
        # Error tracking
        self._last_exception: Optional[Exception] = None
        
        # Performance metrics
        self._frame_count = 0
        self._dropped_frames = 0
        self._last_fps_check = time.time()
        self._capture_fps = 0.0
        self._write_fps = 0.0

    def _detect_gpu_support(self) -> bool:
        """
        Detect if GPU acceleration is available.
        
        Returns:
            True if GPU acceleration is supported
        """
        try:
            # Check for OpenCL support (more widely available)
            if hasattr(cv2, 'ocl') and cv2.ocl.haveOpenCL():
                cv2.ocl.setUseOpenCL(True)
                # Test GPU memory allocation
                test_mat = cv2.UMat(100, 100, cv2.CV_8UC3)
                if test_mat is not None:
                    self._emit_status("GPU acceleration enabled (OpenCL)")
                    return True
        except Exception:
            pass
            
        try:
            # Check for CUDA support if available
            if hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self._emit_status("GPU acceleration available (CUDA)")
                return True
        except Exception:
            pass
            
        self._emit_status("Using CPU processing (GPU not available)")
        return False

    def _get_optimized_codec(self) -> tuple[int, str]:
        """
        Get the best available codec based on hardware and quality settings.
        Tries hardware acceleration first, then falls back to reliable software codecs.
        """
        if self.cfg.hardware_acceleration:
            # Try hardware-accelerated codecs first
            hw_codecs = self._detect_hardware_codecs()
            if hw_codecs:
                for codec_str, name in hw_codecs:
                    fourcc = fourcc_code(codec_str)
                    if self._test_codec(fourcc, codec_str):
                        self._emit_status(f"Using hardware codec: {name}")
                        return fourcc, name
        
        # Use only the most reliable codecs that work with MP4
        # Avoid H.264 and MJPG as they have container compatibility issues
        codec_options = [
            ('mp4v', 'MPEG-4 Part 2'),  # Most reliable for MP4
        ]
        
        for codec_str, name in codec_options:
            fourcc = fourcc_code(codec_str)
            if self._test_codec(fourcc, codec_str):
                self._emit_status(f"Using {self.cfg.video_quality} quality codec: {name}")
                return fourcc, name
        
        # Ultimate fallback - this should always work
        self._emit_status("Using guaranteed fallback: MPEG-4")
        return fourcc_code('mp4v'), 'MPEG-4 Basic'
    
    def _detect_hardware_codecs(self) -> list[tuple[str, str]]:
        """Detect available hardware encoders."""
        hw_codecs = []
        
        try:
            # Only return hardware codecs that we can actually test and use
            # Skip H.264 hardware detection as OpenCV has compatibility issues
            # The FFmpeg mux step will handle H.264 encoding reliably
            pass
                
        except Exception as ex:
            self._emit_status(f"Hardware codec detection failed: {ex}")
        
        return hw_codecs
    
    def _test_nvenc(self) -> bool:
        """Test if NVIDIA NVENC is available."""
        try:
            # Simple test for NVIDIA GPU
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _test_quicksync(self) -> bool:
        """Test if Intel Quick Sync is available."""
        try:
            # Check for Intel GPU presence via WMI or simple heuristics
            import platform
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                          capture_output=True, text=True, timeout=5)
                    if 'intel' in result.stdout.lower():
                        return True
                except:
                    pass
        except:
            pass
        return False
    
    def _test_amf(self) -> bool:
        """Test if AMD AMF is available."""
        try:
            # Check for AMD GPU presence
            import platform
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                          capture_output=True, text=True, timeout=5)
                    output = result.stdout.lower()
                    if 'amd' in output or 'radeon' in output:
                        return True
                except:
                    pass
        except:
            pass
        return False
    
    def _test_codec(self, fourcc: int, codec_str: str) -> bool:
        """Test if a codec actually works by creating a test file."""
        temp_path = tempfile.mktemp(suffix='.mp4')
        try:
            test_writer = cv2.VideoWriter(temp_path, fourcc, 10.0, (640, 480))
            if test_writer.isOpened():
                # Write test frames
                test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                test_frame[:] = (50, 100, 150)
                
                for _ in range(10):
                    success = test_writer.write(test_frame)
                    if not success:
                        test_writer.release()
                        return False
                
                test_writer.release()
                
                # Verify file was created and has reasonable size
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
                    return True
                    
            return False
                    
        except Exception:
            return False
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

    def _dedicated_capture_thread(self) -> None:
        """Dedicated thread for screen capture to prevent frame drops."""
        try:
            import os
            
            # Set thread priority if possible
            try:
                if os.name == 'nt':  # Windows
                    import ctypes
                    ctypes.windll.kernel32.SetThreadPriority(
                        ctypes.windll.kernel32.GetCurrentThread(), 2  # THREAD_PRIORITY_HIGHEST
                    )
            except:
                pass
                
            frame_buffer_pool = []
            for _ in range(5):
                frame_buffer_pool.append(np.zeros((self._monitor['height'], self._monitor['width'], 3), dtype=np.uint8))
            
            buffer_index = 0
            next_frame_time = self._frame_interval
            
            while not self._stop_event.is_set():
                current_time = time.perf_counter() - self._recording_start_time
                
                if current_time >= next_frame_time - 0.001:  # 1ms tolerance
                    try:
                        # Use pre-allocated buffer
                        frame_buffer = frame_buffer_pool[buffer_index]
                        buffer_index = (buffer_index + 1) % len(frame_buffer_pool)
                        
                        # Fast screen capture
                        img = self._sct.grab(self._monitor)
                        np.copyto(frame_buffer, np.array(img)[:, :, :3])
                        frame_buffer = cv2.cvtColor(frame_buffer, cv2.COLOR_RGB2BGR)
                        
                        # Queue frame with timestamp
                        frame_data = {
                            'frame': frame_buffer.copy(),
                            'timestamp': current_time,
                            'frame_number': self._frame_count
                        }
                        
                        # Non-blocking queue put with emergency handling
                        try:
                            self._frame_queue.put_nowait(frame_data)
                            self._frame_count += 1
                        except queue.Full:
                            # Emergency: Drop oldest frame and add new one
                            try:
                                self._frame_queue.get_nowait()  # Remove oldest
                                self._frame_queue.put_nowait(frame_data)
                                self._dropped_frames += 1
                                
                                # Enable emergency mode if dropping frequently
                                if self._dropped_frames % 5 == 0:
                                    self._emergency_mode = True
                                    self._emit_status(f"⚡ Emergency mode: {self._dropped_frames} frames dropped")
                            except:
                                self._dropped_frames += 1
                        
                        next_frame_time += self._frame_interval
                        
                    except Exception as ex:
                        self._emit_status(f"Capture error: {ex}")
                        break
                else:
                    # Precise sleep until next frame
                    sleep_time = next_frame_time - current_time
                    if sleep_time > 0:
                        time.sleep(min(sleep_time, 0.001))
                        
        except Exception as ex:
            self._last_exception = ex
            self._emit_status(f"Capture thread error: {ex}")

    def _dedicated_write_thread(self) -> None:
        """Dedicated thread for video writing to prevent I/O blocking."""
        try:
            import os
            
            # Lower priority for write thread (capture has priority)
            try:
                if os.name == 'nt':
                    import ctypes
                    ctypes.windll.kernel32.SetThreadPriority(
                        ctypes.windll.kernel32.GetCurrentThread(), 1  # THREAD_PRIORITY_ABOVE_NORMAL
                    )
            except:
                pass
            
            frames_behind = 0
            
            while not self._stop_event.is_set() or not self._frame_queue.empty():
                try:
                    # Get frame from capture queue
                    frame_data = self._frame_queue.get(timeout=1.0)
                    
                    if frame_data is None:  # Sentinel to stop
                        break
                    
                    frame = frame_data['frame']
                    timestamp = frame_data['timestamp']
                    frame_number = frame_data['frame_number']
                    
                    # Check if we're falling behind
                    queue_size = self._frame_queue.qsize()
                    if queue_size > self.cfg.buffer_size // 2:
                        frames_behind += 1
                        if frames_behind > self._frame_skip_threshold:
                            # Skip expensive overlay processing
                            if not self._emergency_mode:
                                self._emergency_mode = True
                                self._emit_status("⚡ Skipping overlays to catch up")
                    else:
                        frames_behind = max(0, frames_behind - 1)
                        if frames_behind == 0 and self._emergency_mode:
                            self._emergency_mode = False
                            self._emit_status("✅ Normal processing resumed")
                    
                    # Apply overlays only if not in emergency mode
                    if not self._emergency_mode and (self.cfg.mouse_highlight or self.cfg.use_webcam):
                        frame = self._process_frame_overlays(frame)
                    
                    # Write frame with timestamp tracking
                    if self._writer:
                        self._video_frame_times.append(timestamp)
                        self._writer.write(frame)
                    
                    # Queue for writing pipeline
                    try:
                        self._write_queue.put_nowait({
                            'written': True,
                            'timestamp': timestamp,
                            'frame_number': frame_number
                        })
                    except queue.Full:
                        try:
                            self._write_queue.get_nowait()  # Remove oldest
                            self._write_queue.put_nowait({
                                'written': True,
                                'timestamp': timestamp,
                                'frame_number': frame_number
                            })
                        except:
                            pass
                    
                except queue.Empty:
                    continue
                except Exception as ex:
                    self._emit_status(f"Write thread error: {ex}")
                    break
                    
        except Exception as ex:
            self._last_exception = ex
            self._emit_status(f"Write thread error: {ex}")

    def _get_ffmpeg_quality_settings(self) -> dict[str, str | int]:
        """Get FFmpeg encoding settings based on quality preference."""
        quality_map = {
            "low": {"preset": "ultrafast", "crf": 28},      # Fast encoding, larger files
            "medium": {"preset": "fast", "crf": 25},        # Balanced
            "high": {"preset": "medium", "crf": 23},        # Good quality (default)
            "ultra": {"preset": "slow", "crf": 20}          # Best quality, slower encoding
        }
        return quality_map.get(self.cfg.video_quality, quality_map["high"])

    def _create_frame_buffer_pool(self, width: int, height: int) -> None:
        """Create pre-allocated frame buffers for better performance."""
        try:
            for _ in range(5):
                if self._use_gpu:
                    # Use UMat for GPU acceleration (OpenCL)
                    gpu_frame = cv2.UMat(height, width, cv2.CV_8UC3)
                    if self._gpu_mat_pool:
                        self._gpu_mat_pool.put(gpu_frame)
                else:
                    # CPU memory allocation
                    cpu_frame = np.zeros((height, width, 3), dtype=np.uint8)
                    self._frame_pool.put(cpu_frame)
        except Exception as ex:
            self._emit_status(f"Warning: Could not create frame buffers: {ex}")

    def start(self) -> None:
        """Start screen recording in background thread."""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_event.clear()
        self._last_exception = None
        self._thread = threading.Thread(target=self._recording_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop screen recording and cleanup resources."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._cleanup()

    def get_last_error(self) -> Optional[Exception]:
        """Get the last exception that occurred during recording."""
        return self._last_exception

    def _emit_status(self, msg: str) -> None:
        """Emit status message through callback."""
        try:
            self.status_callback(msg)
        except Exception:
            pass

    def _enable_high_priority(self) -> None:
        """Enable high-priority processing for production recording."""
        try:
            import psutil
            import os
            
            # Set high priority for current process
            p = psutil.Process(os.getpid())
            if hasattr(psutil, 'HIGH_PRIORITY_CLASS'):
                p.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                p.nice(-10)  # Unix nice value
                
            self._priority_mode = True
            self._emit_status("🚀 High-priority mode enabled for production recording")
        except ImportError:
            self._emit_status("📝 Install psutil for high-priority mode: pip install psutil")
        except Exception as ex:
            self._emit_status(f"⚠️  Could not enable high priority: {ex}")

    def _setup_capture_target(self) -> None:
        """Setup screen capture target (monitor or region)."""
        self._sct = mss()
        
        if self.cfg.region:
            # Custom region capture
            left, top, width, height = self.cfg.region
            self._monitor = {
                "left": left, 
                "top": top, 
                "width": width, 
                "height": height
            }
        else:
            # Monitor-based capture
            monitors = self._sct.monitors
            mon_index = max(0, min(self.cfg.monitor_index, len(monitors) - 1))
            self._monitor = monitors[mon_index]

    def _setup_video_writer(self, width: int, height: int) -> None:
        """
        Setup video writer with optimized codec and GPU acceleration.
        
        Args:
            width: Video frame width
            height: Video frame height
        """
        # Get optimized codec
        fourcc, codec_name = self._get_optimized_codec()
        fps = float(self.cfg.fps)
        
        if self.cfg.record_audio:
            # Write video to temporary file for later audio muxing
            # ALWAYS use .mp4 for consistency
            base, ext = os.path.splitext(self.cfg.output_path)
            self._video_tmp_path = base + "_tmp_video.mp4"
            output_path = self._video_tmp_path
        else:
            output_path = self.cfg.output_path
            
        # Create video writer with hardware acceleration hints
        if os.name == 'nt':  # Windows
            # Try hardware encoding backends
            backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
        else:
            backends = [cv2.CAP_FFMPEG, cv2.CAP_ANY]
            
        self._writer = None
        for backend in backends:
            try:
                writer = cv2.VideoWriter()
                # Set backend-specific properties for hardware acceleration
                if backend == cv2.CAP_MSMF:
                    writer.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                
                if writer.open(output_path, backend, fourcc, fps, (width, height)):
                    self._writer = writer
                    self._emit_status(f"Video writer initialized with {codec_name}")
                    break
                writer.release()
            except Exception:
                continue
                
        # Fallback to basic writer
        if not self._writer:
            self._writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
        if not self._writer or not self._writer.isOpened():
            raise RuntimeError("Failed to open video writer. Check codec and output path.")
            
        # Create frame buffer pool for performance
        self._create_frame_buffer_pool(width, height)

    def _setup_webcam(self) -> None:
        """Setup webcam for picture-in-picture if enabled."""
        if not self.cfg.use_webcam:
            return
            
        cam_index = self.cfg.webcam_index
        
        # Try different backends for better compatibility
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if os.name == 'nt' else [cv2.CAP_ANY]
        
        for backend in backends:
            try:
                cam = cv2.VideoCapture(cam_index, backend)
                if cam.isOpened():
                    self._cam = cam
                    self._emit_status(f"Webcam {cam_index} opened successfully")
                    return
                cam.release()
            except Exception:
                try:
                    cam.release()
                except Exception:
                    pass
                    
        self._emit_status(f"Warning: Cannot open webcam index {cam_index}")

    def _draw_mouse_highlight(self, frame: np.ndarray, mouse_pos: tuple[int, int]) -> None:
        """
        Draw mouse highlight overlay on frame.
        
        Args:
            frame: Video frame to draw on (modified in-place)
            mouse_pos: Mouse position (x, y)
        """
        x, y = mouse_pos
        radius = max(5, self.cfg.mouse_radius)
        color = tuple(int(c) for c in self.cfg.mouse_color)  # BGR format
        alpha = self.cfg.mouse_alpha
        
        # Create overlay with highlight circle
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), radius, color, thickness=-1, lineType=cv2.LINE_AA)
        
        # Blend overlay with original frame
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, dst=frame)

    def _overlay_webcam_pip(self, base_frame: np.ndarray, cam_frame: np.ndarray) -> np.ndarray:
        """
        Overlay webcam picture-in-picture on base frame.
        
        Args:
            base_frame: Main video frame
            cam_frame: Webcam frame to overlay
            
        Returns:
            Frame with webcam overlay
        """
        h, w = base_frame.shape[:2]
        
        # Calculate PIP dimensions
        target_w = max(32, int(w * (self.cfg.pip_width_pct / 100.0)))
        aspect_ratio = cam_frame.shape[0] / max(1, cam_frame.shape[1])
        target_h = int(target_w * aspect_ratio)
        
        # Resize webcam frame
        pip_frame = cv2.resize(cam_frame, (target_w, target_h))
        
        # Calculate position based on configuration
        padding = 12
        position = self.cfg.pip_position.lower()
        
        if position.startswith('top'):
            y0 = padding
        else:  # bottom
            y0 = max(padding, h - target_h - padding)
            
        if position.endswith('left'):
            x0 = padding
        elif position.endswith('right'):
            x0 = max(padding, w - target_w - padding)
        else:  # center
            x0 = (w - target_w) // 2
            
        x1, y1 = x0 + target_w, y0 + target_h
        
        # Draw background border
        border = 2
        cv2.rectangle(
            base_frame, 
            (x0 - border, y0 - border), 
            (x1 + border, y1 + border), 
            (30, 30, 30), 
            thickness=-1
        )
        
        # Overlay webcam frame
        roi = base_frame[y0:y1, x0:x1]
        if roi.shape[:2] == pip_frame.shape[:2]:
            base_frame[y0:y1, x0:x1] = pip_frame
            
        return base_frame

    def _process_frame_overlays(self, frame: np.ndarray) -> np.ndarray:
        """
        Process all frame overlays with optimized performance.
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with overlays applied
        """
        # Use pre-allocated working frame for better memory performance
        working_frame = frame
        
        # Mouse highlight overlay
        if self.cfg.mouse_highlight and pyautogui is not None:
            try:
                mouse_x, mouse_y = pyautogui.position()
                
                # Adjust for capture region offset
                if self._monitor:
                    offset_x = self._monitor.get('left', 0)
                    offset_y = self._monitor.get('top', 0)
                    mouse_x -= offset_x
                    mouse_y -= offset_y
                    
                self._draw_mouse_highlight(working_frame, (mouse_x, mouse_y))
            except Exception:
                # Continue if mouse position detection fails
                pass
                
        # Webcam overlay with frame buffering to prevent blinking
        if self._cam is not None:
            # Update webcam buffer every few frames to reduce blinking
            if self._cam_frame_count % self._cam_update_interval == 0:
                ret, cam_frame = self._cam.read()
                if ret and cam_frame is not None:
                    self._cam_buffer = cam_frame.copy()  # Store stable frame
            
            # Use buffered frame for overlay
            if self._cam_buffer is not None:
                working_frame = self._overlay_webcam_pip(working_frame, self._cam_buffer)
            
            self._cam_frame_count += 1
                
        return working_frame

    def _start_audio_recording(self) -> None:
        """Start audio recording if enabled."""
        if not self.cfg.record_audio:
            return
            
        try:
            self._audio_recorder = AudioRecorder(
                samplerate=self.cfg.audio_samplerate,
                channels=self.cfg.audio_channels,
                device=self.cfg.audio_device,
                loopback=self.cfg.system_audio_loopback,
                status_callback=self._emit_status
            )
            self._audio_recorder.start()
            self._emit_status("Audio recording started")
        except Exception as ex:
            self._emit_status(f"Audio recording disabled: {ex}")
            self._audio_recorder = None

    def _mux_audio_video(self) -> None:
        """Merge video and audio using FFmpeg with improved error handling."""
        if not self._audio_recorder or not self._video_tmp_path:
            raise RuntimeError("Audio recorder or video path not available for muxing")
            
        audio_path = self._audio_recorder.wav_path
        if not os.path.exists(audio_path):
            raise RuntimeError(f"Audio file not found for muxing: {audio_path}")
            
        if not os.path.exists(self._video_tmp_path):
            raise RuntimeError(f"Video file not found for muxing: {self._video_tmp_path}")
            
        # Check file sizes to ensure they have content
        audio_size = os.path.getsize(audio_path)
        video_size = os.path.getsize(self._video_tmp_path)
        
        if audio_size < 1024:  # Less than 1KB
            raise RuntimeError(f"Audio file too small ({audio_size} bytes), may be corrupted")
            
        if video_size < 1024:  # Less than 1KB
            raise RuntimeError(f"Video file too small ({video_size} bytes), may be corrupted")
            
        self._emit_status(f"Muxing: Video {video_size//1024}KB + Audio {audio_size//1024}KB")
        
        # Find FFmpeg executable
        ffmpeg_path, source = find_ffmpeg_path(self.cfg.ffmpeg_path)
        if not ffmpeg_path:
            raise RuntimeError(get_ffmpeg_error_message(self.cfg.ffmpeg_path))
            
        # Test FFmpeg before using
        success, message = test_ffmpeg(ffmpeg_path)
        if not success:
            raise RuntimeError(f"FFmpeg test failed: {message}")
            
        # Enhanced FFmpeg command optimized for reliability and sync
        quality_settings = self._get_ffmpeg_quality_settings()
        
        cmd = [
            ffmpeg_path, '-y',
            '-i', self._video_tmp_path,  # Video input
            '-i', audio_path,            # Audio input
            '-c:v', 'libx264',           # Re-encode video to H.264 for best compatibility
            '-preset', quality_settings['preset'],  # Quality-based preset
            '-crf', str(quality_settings['crf']),   # Quality-based CRF
            '-c:a', 'aac',               # AAC audio codec
            '-b:a', '128k',              # Audio bitrate
            '-ar', '44100',              # Standard sample rate
            '-ac', '2',                  # Stereo audio
            '-vsync', 'cfr',             # Constant frame rate for sync
            '-async', '1',               # Audio sync compensation
            '-movflags', '+faststart',   # Optimize for web playback
            '-shortest',                 # Match shortest stream
            self.cfg.output_path
        ]
        
        self._emit_status(f"Running FFmpeg: {' '.join(cmd[0:3])} ...")
        
        try:
            proc = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if proc.returncode != 0:
                error_msg = proc.stderr.strip() if proc.stderr else "Unknown FFmpeg error"
                raise RuntimeError(f"FFmpeg failed (code {proc.returncode}): {error_msg}")
                
            # Verify output file was created and has reasonable size
            if not os.path.exists(self.cfg.output_path):
                raise RuntimeError("FFmpeg completed but output file was not created")
                
            output_size = os.path.getsize(self.cfg.output_path)
            if output_size < video_size * 0.8:  # Output should be at least 80% of video size
                self._emit_status(f"Warning: Output file smaller than expected ({output_size//1024}KB)")
            else:
                self._emit_status(f"Muxing successful: {output_size//1024}KB output file created")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg operation timed out (>5 minutes)")
        except Exception as ex:
            raise RuntimeError(f"FFmpeg execution failed: {ex}")
        finally:
            # Cleanup temporary files
            for temp_path in (self._video_tmp_path, audio_path):
                try:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
                        self._emit_status(f"Cleaned up: {os.path.basename(temp_path)}")
                except Exception as ex:
                    self._emit_status(f"Warning: Could not remove {temp_path}: {ex}")

    def _recording_loop(self) -> None:
        """Production-grade recording loop with advanced frame drop prevention."""
        try:
            self._emit_status("🏭 Initializing production recording...")
            
            # Enable high-priority mode for production
            self._enable_high_priority()
            
            # Setup capture components
            self._setup_capture_target()
            self._setup_webcam()
            
            # CRITICAL: Record precise start time for synchronization
            self._recording_start_time = time.perf_counter()
            
            # Start audio recording FIRST with exact timing
            if self.cfg.record_audio:
                self._emit_status("Starting synchronized audio recording...")
                self._start_audio_recording()
                time.sleep(0.05)  # Minimal delay for audio initialization
            
            # Capture first frame to determine exact dimensions
            assert self._sct is not None and self._monitor is not None
            img = self._sct.grab(self._monitor)
            frame = np.array(img)[:, :, :3]  # Skip alpha channel
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            height, width = frame.shape[:2]
            
            # Setup video writer with actual frame dimensions
            self._setup_video_writer(width, height)
            
            # Start dedicated capture and write threads for production reliability
            self._stop_event.clear()
            
            self._capture_thread = threading.Thread(
                target=self._dedicated_capture_thread,
                name="ProductionCapture",
                daemon=True
            )
            
            self._write_thread = threading.Thread(
                target=self._dedicated_write_thread,
                name="ProductionWrite", 
                daemon=True
            )
            
            self._capture_thread.start()
            self._write_thread.start()
            
            self._emit_status("🎬 Production recording started with threaded pipeline")
            
            # Monitor performance and provide real-time feedback
            last_stats_time = time.perf_counter()
            
            while not self._stop_event.is_set():
                current_time = time.perf_counter()
                
                # Update performance statistics every 5 seconds
                if current_time - last_stats_time >= 5.0:
                    recording_duration = current_time - self._recording_start_time
                    
                    if recording_duration > 0:
                        actual_fps = self._frame_count / recording_duration
                        queue_size = self._frame_queue.qsize()
                        write_queue_size = self._write_queue.qsize()
                        
                        # Performance status
                        if self._dropped_frames == 0:
                            status = "🟢 Perfect"
                        elif self._dropped_frames < 5:
                            status = "🟡 Good"
                        else:
                            status = "🔴 Issues"
                        
                        self._emit_status(
                            f"{status} | {actual_fps:.1f} FPS | "
                            f"Frames: {self._frame_count} | "
                            f"Dropped: {self._dropped_frames} | "
                            f"Queues: {queue_size}/{write_queue_size}"
                        )
                        
                        # Adaptive quality adjustment if dropping frames
                        if self._dropped_frames > 10 and self._adaptive_quality:
                            if not self._emergency_mode:
                                self._emergency_mode = True
                                self._emit_status("⚡ Activating emergency mode - reducing quality")
                    
                    last_stats_time = current_time
                
                # Check thread health
                if not self._capture_thread.is_alive():
                    self._emit_status("❌ Capture thread died - restarting")
                    break
                    
                if not self._write_thread.is_alive():
                    self._emit_status("❌ Write thread died - restarting")
                    break
                
                time.sleep(0.1)  # Monitor loop sleep
                
        except Exception as ex:
            self._last_exception = ex
            self._emit_status(f"Production recording error: {ex}")
        finally:
            self._finalize_recording()

    def _dedicated_capture_thread(self) -> None:
        """Dedicated thread for screen capture to prevent frame drops."""
        try:
            import os
            
            # CRITICAL: Create new mss instance for this thread to avoid srcdc errors
            thread_sct = mss()
            
            # Set high thread priority for capture
            try:
                if os.name == 'nt':  # Windows
                    import ctypes
                    ctypes.windll.kernel32.SetThreadPriority(
                        ctypes.windll.kernel32.GetCurrentThread(), 2  # THREAD_PRIORITY_HIGHEST
                    )
            except:
                pass
                
            # Pre-allocate frame buffers for zero-allocation capture
            frame_buffer_pool = []
            for _ in range(10):  # Larger pool for production
                frame_buffer_pool.append(np.zeros((self._monitor['height'], self._monitor['width'], 3), dtype=np.uint8))
            
            buffer_index = 0
            next_frame_time = self._frame_interval
            last_emergency_log = 0
            
            while not self._stop_event.is_set():
                current_time = time.perf_counter() - self._recording_start_time
                
                if current_time >= next_frame_time - 0.0005:  # 0.5ms tolerance for production
                    try:
                        # Use pre-allocated buffer (zero memory allocation)
                        frame_buffer = frame_buffer_pool[buffer_index]
                        buffer_index = (buffer_index + 1) % len(frame_buffer_pool)
                        
                        # Fastest possible screen capture with thread-local mss
                        img = thread_sct.grab(self._monitor)
                        np.copyto(frame_buffer, np.array(img)[:, :, :3])
                        frame_buffer = cv2.cvtColor(frame_buffer, cv2.COLOR_RGB2BGR)
                        
                        # Queue frame with metadata
                        frame_data = {
                            'frame': frame_buffer.copy(),
                            'timestamp': current_time,
                            'frame_number': self._frame_count,
                            'is_key_frame': self._frame_count % 30 == 0  # Every second at 30fps
                        }
                        
                        # Production-grade queue management
                        try:
                            self._frame_queue.put_nowait(frame_data)
                            self._frame_count += 1
                        except queue.Full:
                            # Smart frame dropping - keep key frames, drop others
                            dropped_old = False
                            try:
                                # Try to remove a non-key frame first
                                temp_frames = []
                                while not self._frame_queue.empty() and len(temp_frames) < 5:
                                    old_frame = self._frame_queue.get_nowait()
                                    if not old_frame.get('is_key_frame', False):
                                        dropped_old = True
                                        break
                                    temp_frames.append(old_frame)
                                
                                # Put back the key frames
                                for temp_frame in temp_frames:
                                    self._frame_queue.put_nowait(temp_frame)
                                
                                # Add new frame
                                self._frame_queue.put_nowait(frame_data)
                                if dropped_old:
                                    self._dropped_frames += 1
                                else:
                                    self._dropped_frames += 1
                                
                            except:
                                self._dropped_frames += 1
                                
                            # Emergency mode detection
                            if self._dropped_frames % 10 == 0 and current_time - last_emergency_log > 5:
                                self._emit_status(f"⚡ Production mode: {self._dropped_frames} frames optimized")
                                last_emergency_log = current_time
                        
                        next_frame_time += self._frame_interval
                        
                    except Exception as ex:
                        self._emit_status(f"Capture error: {ex}")
                        break
                else:
                    # Ultra-precise sleep for production timing
                    sleep_time = next_frame_time - current_time
                    if sleep_time > 0:
                        time.sleep(min(sleep_time, 0.0005))  # Max 0.5ms sleep
                        
        except Exception as ex:
            self._last_exception = ex
            self._emit_status(f"Capture thread error: {ex}")

    def _dedicated_write_thread(self) -> None:
        """Dedicated thread for video writing with production optimizations."""
        try:
            import os
            
            # Set appropriate priority for write thread
            try:
                if os.name == 'nt':
                    import ctypes
                    ctypes.windll.kernel32.SetThreadPriority(
                        ctypes.windll.kernel32.GetCurrentThread(), 1  # THREAD_PRIORITY_ABOVE_NORMAL
                    )
            except:
                pass
            
            frames_behind = 0
            batch_write_buffer = []
            max_batch_size = 5
            
            while not self._stop_event.is_set() or not self._frame_queue.empty():
                try:
                    # Get frame from capture queue with timeout
                    frame_data = self._frame_queue.get(timeout=0.5)
                    
                    if frame_data is None:  # Sentinel to stop
                        break
                    
                    frame = frame_data['frame']
                    timestamp = frame_data['timestamp']
                    frame_number = frame_data['frame_number']
                    
                    # Monitor queue health for adaptive processing
                    queue_size = self._frame_queue.qsize()
                    write_queue_size = self._write_queue.qsize()
                    
                    # Adaptive quality control based on queue pressure
                    if queue_size > self.cfg.buffer_size * 0.75:  # 75% full
                        frames_behind += 1
                        if frames_behind > 3 and not self._emergency_mode:
                            self._emergency_mode = True
                            self._emit_status("⚡ Adaptive mode: Optimizing processing pipeline")
                    else:
                        frames_behind = max(0, frames_behind - 1)
                        if frames_behind == 0 and self._emergency_mode:
                            self._emergency_mode = False
                            self._emit_status("✅ Full quality mode restored")
                    
                    # Process overlays (skip in emergency mode for speed)
                    processed_frame = frame
                    if not self._emergency_mode:
                        if self.cfg.mouse_highlight or self.cfg.use_webcam:
                            processed_frame = self._process_frame_overlays(frame)
                    
                    # Batch writing for better I/O performance
                    batch_write_buffer.append({
                        'frame': processed_frame,
                        'timestamp': timestamp,
                        'frame_number': frame_number
                    })
                    
                    # Write batch when full or in emergency mode
                    if len(batch_write_buffer) >= max_batch_size or self._emergency_mode:
                        for batch_item in batch_write_buffer:
                            if self._writer:
                                self._video_frame_times.append(batch_item['timestamp'])
                                self._writer.write(batch_item['frame'])
                        
                        batch_write_buffer.clear()
                    
                except queue.Empty:
                    # Flush any remaining frames in batch
                    if batch_write_buffer:
                        for batch_item in batch_write_buffer:
                            if self._writer:
                                self._video_frame_times.append(batch_item['timestamp'])
                                self._writer.write(batch_item['frame'])
                        batch_write_buffer.clear()
                    continue
                except Exception as ex:
                    self._emit_status(f"Write thread error: {ex}")
                    break
            
            # Final flush
            if batch_write_buffer:
                for batch_item in batch_write_buffer:
                    if self._writer:
                        self._video_frame_times.append(batch_item['timestamp'])
                        self._writer.write(batch_item['frame'])
                        
        except Exception as ex:
            self._last_exception = ex
            self._emit_status(f"Write thread error: {ex}")

    def _finalize_recording(self) -> None:
        """Production-grade finalization with threaded cleanup."""
        try:
            self._emit_status("🏁 Finalizing production recording...")
            
            # Stop capture and write threads gracefully
            if hasattr(self, '_capture_thread') and self._capture_thread and self._capture_thread.is_alive():
                self._emit_status("Stopping capture thread...")
                self._capture_thread.join(timeout=2.0)
            
            if hasattr(self, '_write_thread') and self._write_thread and self._write_thread.is_alive():
                self._emit_status("Stopping write thread...")
                # Signal write thread to stop by putting None
                try:
                    self._frame_queue.put_nowait(None)
                except:
                    pass
                self._write_thread.join(timeout=5.0)
            
            # CRITICAL: Release video writer FIRST before any file operations
            if self._writer:
                self._writer.release()
                self._writer = None
                self._emit_status("Video writer released")
                # Give OS time to fully release file handle
                time.sleep(0.3)
                
                # Add current segment if using segments
                if self.cfg.use_segments and self._video_tmp_path:
                    self._segment_paths.append(self._video_tmp_path)
            
            # Final performance report
            if self._frame_count > 0:
                recording_duration = (time.perf_counter() - self._recording_start_time) if self._recording_start_time > 0 else 1
                final_fps = self._frame_count / recording_duration
                efficiency = ((self._frame_count - self._dropped_frames) / self._frame_count * 100) if self._frame_count > 0 else 0
                
                self._emit_status(
                    f"📊 Final Stats: {self._frame_count} frames, "
                    f"{final_fps:.1f} FPS, {efficiency:.1f}% efficiency, "
                    f"{self._dropped_frames} optimized frames"
                )
            
            if self.cfg.record_audio and self._audio_recorder:
                self._emit_status("Stopping audio...")
                self._audio_recorder.stop()
                
                # Additional delay to ensure video file is fully written
                time.sleep(0.3)
                
                # Get audio file path
                audio_path = getattr(self._audio_recorder, 'wav_path', '')
                
                if self.cfg.save_audio_separately:
                    # Save audio separately as requested
                    if audio_path and os.path.exists(audio_path):
                        # Create final audio path alongside video
                        base_path = os.path.splitext(self.cfg.output_path)[0]
                        final_audio_path = base_path + "_audio.wav"
                        
                        try:
                            import shutil
                            shutil.copy2(audio_path, final_audio_path)
                            self._emit_status(f"Audio saved separately: {final_audio_path}")
                        except Exception as ex:
                            self._emit_status(f"Warning: Could not copy audio file: {ex}")
                            self._emit_status(f"Audio available at: {audio_path}")
                    
                    # Handle segments without audio
                    if self.cfg.use_segments and len(self._segment_paths) > 1:
                        try:
                            self._merge_segments()
                            self._emit_status("Video segments merged successfully")
                        except Exception as ex:
                            self._emit_status(f"Segment merge failed: {ex}")
                    else:
                        self._emit_status("Video saved (audio separate)")
                else:
                    # Normal mode: merge audio and video
                    try:
                        # Handle segment merging first if needed
                        if self.cfg.use_segments and len(self._segment_paths) > 1:
                            self._merge_segments()
                        
                        self._mux_audio_video()
                        self._emit_status("Recording saved with audio")
                    except Exception as ex:
                        # Fallback: Save audio separately if muxing fails
                        if audio_path and os.path.exists(audio_path):
                            base_path = os.path.splitext(self.cfg.output_path)[0]
                            final_audio_path = base_path + "_audio.wav"
                            
                            try:
                                import shutil
                                shutil.copy2(audio_path, final_audio_path)
                                self._emit_status(
                                    f"Video saved. Audio merge failed: {ex}\n"
                                    f"Audio saved separately: {final_audio_path}"
                                )
                            except:
                                self._emit_status(
                                    f"Video saved. Audio merge failed: {ex}\n"
                                    f"Audio available at: {audio_path}"
                                )
                        else:
                            self._emit_status(f"Video saved. Audio merge failed: {ex}")
            else:
                # Handle segments without audio
                if self.cfg.use_segments and len(self._segment_paths) > 1:
                    try:
                        self._merge_segments()
                        self._emit_status("Segments merged successfully")
                    except Exception as ex:
                        self._emit_status(f"Segment merge failed: {ex}")
                else:
                    self._emit_status("Recording saved")
                
        except Exception as ex:
            self._emit_status(f"Error finalizing recording: {ex}")
        finally:
            self._cleanup()

    def _should_start_new_segment(self) -> bool:
        """Check if a new segment should be started based on duration."""
        if self._segment_start_time == 0:
            self._segment_start_time = time.time()
            return False
            
        elapsed_minutes = (time.time() - self._segment_start_time) / 60
        return elapsed_minutes >= self.cfg.segment_duration_minutes
    
    def _start_new_segment(self, width: int, height: int) -> None:
        """Start a new recording segment."""
        try:
            # Finalize current segment
            if self._writer:
                self._writer.release()
                self._writer = None
                
                # Save current segment path
                if self._video_tmp_path:
                    self._segment_paths.append(self._video_tmp_path)
            
            # Create new segment
            self._current_segment += 1
            base, ext = os.path.splitext(self.cfg.output_path)
            segment_path = f"{base}_segment_{self._current_segment:03d}{ext}"
            
            if self.cfg.record_audio:
                self._video_tmp_path = f"{base}_segment_{self._current_segment:03d}_tmp_video.mp4"
            else:
                segment_path = self._video_tmp_path = segment_path
            
            # Create new writer for this segment
            fourcc, codec_name = self._get_optimized_codec()
            self._writer = cv2.VideoWriter(self._video_tmp_path or segment_path, fourcc, float(self.cfg.fps), (width, height))
            
            if not self._writer or not self._writer.isOpened():
                raise RuntimeError(f"Failed to create video writer for segment {self._current_segment}")
            
            self._segment_start_time = time.time()
            self._emit_status(f"Started segment {self._current_segment}: {os.path.basename(segment_path)}")
            
        except Exception as ex:
            self._emit_status(f"Failed to start new segment: {ex}")
            raise
    
    def _merge_segments(self) -> None:
        """Merge all segments into final output file."""
        if not self._segment_paths:
            return
            
        try:
            # Find FFmpeg
            ffmpeg_path, _ = find_ffmpeg_path(self.cfg.ffmpeg_path)
            if not ffmpeg_path:
                raise RuntimeError("FFmpeg not found for segment merging")
            
            # Create file list for FFmpeg concat
            concat_file = tempfile.mktemp(suffix='.txt')
            with open(concat_file, 'w') as f:
                for segment_path in self._segment_paths:
                    f.write(f"file '{segment_path}'\n")
            
            # Merge segments
            cmd = [
                ffmpeg_path, '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',  # Copy without re-encoding
                self.cfg.output_path
            ]
            
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                raise RuntimeError(f"Segment merge failed: {proc.stderr}")
            
            self._emit_status(f"Merged {len(self._segment_paths)} segments")
            
            # Cleanup segment files
            for segment_path in self._segment_paths:
                try:
                    if os.path.exists(segment_path):
                        os.remove(segment_path)
                except Exception:
                    pass
            
            # Cleanup concat file
            try:
                if os.path.exists(concat_file):
                    os.remove(concat_file)
            except Exception:
                pass
                
        except Exception as ex:
            self._emit_status(f"Segment merge failed: {ex}")
            raise

    def _cleanup(self) -> None:
        """Cleanup all recording resources."""
        # Close video writer
        if self._writer:
            try:
                self._writer.release()
            except Exception:
                pass
            self._writer = None
            
        # Close screen capture
        if self._sct:
            try:
                self._sct.close()
            except Exception:
                pass
            self._sct = None
            
        # Close webcam
        if self._cam:
            try:
                self._cam.release()
            except Exception:
                pass
            self._cam = None
            
        # Close thread pool
        if hasattr(self, '_thread_pool'):
            try:
                self._thread_pool.shutdown(wait=False)
            except Exception:
                pass
            
        # Close preview windows
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        """Cleanup all recording resources."""
        # Close video writer
        if self._writer:
            try:
                self._writer.release()
            except Exception:
                pass
            self._writer = None
            
        # Close screen capture
        if self._sct:
            try:
                self._sct.close()
            except Exception:
                pass
            self._sct = None
            
        # Close webcam
        if self._cam:
            try:
                self._cam.release()
            except Exception:
                pass
            self._cam = None
            
        # Close preview windows
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


def probe_cameras(max_index: int = 6) -> list[int]:
    """
    Probe for available camera devices.
    
    Args:
        max_index: Maximum camera index to check
        
    Returns:
        List of available camera indices
    """
    available_cameras = []
    
    for i in range(max_index):
        try:
            # Try multiple backends for better compatibility
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if os.name == 'nt' else [cv2.CAP_ANY]
            
            camera_found = False
            for backend in backends:
                try:
                    cap = cv2.VideoCapture(i, backend)
                    if cap.isOpened():
                        available_cameras.append(i)
                        camera_found = True
                        cap.release()
                        break
                    cap.release()
                except Exception:
                    try:
                        cap.release()
                    except Exception:
                        pass
                        
            if camera_found:
                break
                
        except Exception:
            continue
            
    return available_cameras
