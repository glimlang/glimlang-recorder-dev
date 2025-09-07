"""
User interface for the Screen Recorder application.
Provides Tkinter-based GUI for configuring and controlling recording.
"""

import os
import sys
import datetime as dt
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

# Handle imports for both direct execution and module imports
try:
    from ..core.config import RecorderConfig
    from ..core.video import ScreenRecorder, probe_cameras
    from ..core.audio import get_audio_devices, is_audio_available
    from ..utils.helpers import find_ffmpeg_path, test_ffmpeg
except ImportError:
    # Absolute imports fallback
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.config import RecorderConfig
    from core.video import ScreenRecorder, probe_cameras
    from core.audio import get_audio_devices, is_audio_available
    from utils.helpers import find_ffmpeg_path, test_ffmpeg


class RecorderApp(ttk.Frame):
    """
    Main application window for the screen recorder.
    Provides comprehensive UI for all recording features and settings.
    """
    
    def __init__(self, master: tk.Tk):
        """
        Initialize the recorder application UI.
        
        Args:
            master: Root Tkinter window
        """
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True, padx=12, pady=12)
        master.title("GUI Screen Recorder")
        
        # Application state
        self.recording = False
        self.recorder: Optional[ScreenRecorder] = None
        
        # Initialize UI variables
        self._init_variables()
        
        # Build user interface
        self._build_ui()
        self._update_button_states()
        
        # Setup event handlers
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize device lists
        self._refresh_audio_devices()
        self._refresh_cameras()
        
        # Check FFmpeg availability
        self._check_ffmpeg_startup()

    def _init_variables(self) -> None:
        """Initialize all Tkinter variables for UI controls."""
        # Basic recording settings
        self.var_output = tk.StringVar()
        self.var_fps = tk.StringVar(value="20")
        self.var_status = tk.StringVar(value="Ready")
        self.var_preview = tk.BooleanVar(value=False)
        
        # Screen capture settings
        self.var_monitor_index = tk.IntVar(value=0)
        self.var_use_region = tk.BooleanVar(value=False)
        self.var_region_left = tk.IntVar(value=0)
        self.var_region_top = tk.IntVar(value=0)
        self.var_region_width = tk.IntVar(value=1920)
        self.var_region_height = tk.IntVar(value=1080)
        
        # Mouse highlight settings
        self.var_mouse_highlight = tk.BooleanVar(value=True)
        self.var_mouse_radius = tk.IntVar(value=20)
        self.var_mouse_color = (0, 255, 255)  # BGR format
        self.var_mouse_alpha = tk.DoubleVar(value=0.35)
        
        # Audio settings
        self.var_record_audio = tk.BooleanVar(value=True)  # Enable audio by default
        self.var_system_audio = tk.BooleanVar(value=False)
        self.var_audio_device = tk.StringVar(value="Default")
        self.var_ffmpeg_path = tk.StringVar(value=os.environ.get('FFMPEG_PATH', ''))
        self.var_save_audio_separately = tk.BooleanVar(value=False)  # Save audio as separate file
        
        # Webcam settings
        self.var_use_webcam = tk.BooleanVar(value=False)
        self.var_webcam_index = tk.IntVar(value=0)
        self.var_pip_position = tk.StringVar(value="bottom-right")
        self.var_pip_width_pct = tk.IntVar(value=20)
        
        # Video quality and performance settings
        self.var_video_quality = tk.StringVar(value="high")
        self.var_hardware_acceleration = tk.BooleanVar(value=True)
        self.var_use_segments = tk.BooleanVar(value=False)
        self.var_segment_duration = tk.IntVar(value=60)
        
        # Audio device list
        self._audio_devices: list[tuple[str, Optional[int]]] = [("Default", None)]

    def _build_ui(self) -> None:
        """Build the complete user interface."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        
        # Output settings section
        self._build_output_section(main_frame)
        
        # Screen capture section
        self._build_screen_section(main_frame)
        
        # Mouse highlight section
        self._build_mouse_section(main_frame)
        
        # Audio section
        self._build_audio_section(main_frame)
        
        # Webcam section
        self._build_webcam_section(main_frame)
        
        # Quality and performance section
        self._build_quality_section(main_frame)
        
        # Control buttons
        self._build_controls_section(main_frame)
        
        # Status bar
        self._build_status_section(main_frame)

    def _build_output_section(self, parent: ttk.Widget) -> None:
        """Build output file configuration section."""
        section = ttk.Frame(parent)
        section.pack(fill="x", pady=(0, 8))
        
        # Output path row
        row = ttk.Frame(section)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Output MP4:").pack(side="left")
        ttk.Entry(row, textvariable=self.var_output, width=50).pack(
            side="left", padx=6, fill="x", expand=True
        )
        ttk.Button(row, text="Browse…", command=self._browse_output).pack(side="left")
        
        # FPS row
        row = ttk.Frame(section)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="FPS:").pack(side="left")
        ttk.Entry(row, textvariable=self.var_fps, width=6).pack(side="left", padx=6)

    def _build_screen_section(self, parent: ttk.Widget) -> None:
        """Build screen capture configuration section."""
        section = ttk.LabelFrame(parent, text="Screen Capture")
        section.pack(fill="x", pady=6)
        
        # Monitor selection
        row1 = ttk.Frame(section)
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Monitor index (0 = all):").pack(side="left")
        ttk.Entry(row1, textvariable=self.var_monitor_index, width=6).pack(side="left", padx=6)
        
        # Region selection
        row2 = ttk.Frame(section)
        row2.pack(fill="x", pady=4)
        ttk.Checkbutton(
            row2, 
            text="Capture specific region", 
            variable=self.var_use_region, 
            command=self._toggle_region_controls
        ).pack(side="left")
        
        # Region coordinates
        ttk.Label(row2, text="Left").pack(side="left", padx=(10, 2))
        self.ent_left = ttk.Entry(row2, textvariable=self.var_region_left, width=6)
        self.ent_left.pack(side="left")
        
        ttk.Label(row2, text="Top").pack(side="left", padx=(10, 2))
        self.ent_top = ttk.Entry(row2, textvariable=self.var_region_top, width=6)
        self.ent_top.pack(side="left")
        
        ttk.Label(row2, text="Width").pack(side="left", padx=(10, 2))
        self.ent_width = ttk.Entry(row2, textvariable=self.var_region_width, width=6)
        self.ent_width.pack(side="left")
        
        ttk.Label(row2, text="Height").pack(side="left", padx=(10, 2))
        self.ent_height = ttk.Entry(row2, textvariable=self.var_region_height, width=6)
        self.ent_height.pack(side="left")
        
        # Preview option
        row3 = ttk.Frame(section)
        row3.pack(fill="x", pady=4)
        ttk.Checkbutton(
            row3, 
            text="Show preview window (press 'Q' to close)", 
            variable=self.var_preview
        ).pack(side="left")
        
        self._toggle_region_controls()

    def _build_mouse_section(self, parent: ttk.Widget) -> None:
        """Build mouse highlight configuration section."""
        section = ttk.LabelFrame(parent, text="Mouse Highlight")
        section.pack(fill="x", pady=6)
        
        row = ttk.Frame(section)
        row.pack(fill="x", pady=4)
        
        ttk.Checkbutton(
            row, 
            text="Show mouse cursor", 
            variable=self.var_mouse_highlight
        ).pack(side="left")
        
        ttk.Label(row, text="Radius").pack(side="left", padx=(10, 2))
        ttk.Entry(row, textvariable=self.var_mouse_radius, width=6).pack(side="left")
        
        ttk.Label(row, text="Opacity").pack(side="left", padx=(10, 2))
        ttk.Entry(row, textvariable=self.var_mouse_alpha, width=6).pack(side="left")
        
        ttk.Button(row, text="Pick Color", command=self._pick_mouse_color).pack(
            side="left", padx=6
        )

    def _build_audio_section(self, parent: ttk.Widget) -> None:
        """Build audio recording configuration section."""
        section = ttk.LabelFrame(parent, text="Audio Recording")
        section.pack(fill="x", pady=6)
        
        # Audio enable controls
        row1 = ttk.Frame(section)
        row1.pack(fill="x", pady=4)
        ttk.Checkbutton(
            row1, 
            text="Record audio", 
            variable=self.var_record_audio
        ).pack(side="left")
        
        ttk.Checkbutton(
            row1, 
            text="System audio (Windows)", 
            variable=self.var_system_audio, 
            command=self._refresh_audio_devices
        ).pack(side="left", padx=(10, 0))
        
        ttk.Checkbutton(
            row1, 
            text="Save audio separately", 
            variable=self.var_save_audio_separately
        ).pack(side="left", padx=(10, 0))
        
        # Device selection
        row2 = ttk.Frame(section)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Device:").pack(side="left")
        
        self.cmb_audio = ttk.Combobox(
            row2, 
            textvariable=self.var_audio_device, 
            width=50, 
            state="readonly",
            values=[label for label, _ in self._audio_devices]
        )
        self.cmb_audio.pack(side="left", padx=6, fill="x", expand=True)
        
        ttk.Button(row2, text="Refresh", command=self._refresh_audio_devices).pack(
            side="left", padx=6
        )
        
        # FFmpeg path configuration
        ttk.Label(
            section, 
            text="FFmpeg is required for audio merging. Set path below or add to system PATH."
        ).pack(anchor="w", padx=2, pady=(4, 0))
        
        row3 = ttk.Frame(section)
        row3.pack(fill="x", pady=4)
        ttk.Label(row3, text="FFmpeg path:").pack(side="left")
        
        ttk.Entry(row3, textvariable=self.var_ffmpeg_path, width=40).pack(
            side="left", padx=6, fill="x", expand=True
        )
        
        ttk.Button(row3, text="Browse…", command=self._browse_ffmpeg).pack(
            side="left", padx=2
        )
        ttk.Button(row3, text="Test", command=self._test_ffmpeg).pack(side="left")

    def _build_webcam_section(self, parent: ttk.Widget) -> None:
        """Build webcam picture-in-picture configuration section."""
        section = ttk.LabelFrame(parent, text="Webcam Picture-in-Picture")
        section.pack(fill="x", pady=6)
        
        # Webcam enable and selection
        row1 = ttk.Frame(section)
        row1.pack(fill="x", pady=4)
        
        ttk.Checkbutton(
            row1, 
            text="Include webcam overlay", 
            variable=self.var_use_webcam
        ).pack(side="left")
        
        ttk.Label(row1, text="Camera:").pack(side="left", padx=(10, 2))
        ttk.Entry(row1, textvariable=self.var_webcam_index, width=6).pack(side="left")
        
        ttk.Button(row1, text="Detect", command=self._refresh_cameras).pack(
            side="left", padx=6
        )
        
        # Position and size controls
        row2 = ttk.Frame(section)
        row2.pack(fill="x", pady=4)
        
        ttk.Label(row2, text="Position:").pack(side="left")
        ttk.Combobox(
            row2, 
            textvariable=self.var_pip_position, 
            state="readonly",
            values=["top-left", "top-right", "bottom-left", "bottom-right"]
        ).pack(side="left", padx=6)
        
        ttk.Label(row2, text="Size %:").pack(side="left", padx=(10, 2))
        ttk.Entry(row2, textvariable=self.var_pip_width_pct, width=6).pack(side="left")

    def _build_quality_section(self, parent: ttk.Widget) -> None:
        """Build quality and performance settings."""
        section = ttk.LabelFrame(parent, text="Quality & Performance", padding=(6, 6))
        section.pack(fill="x", pady=6)
        
        # Video quality row
        row1 = ttk.Frame(section)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="Video Quality:").pack(side="left")
        quality_combo = ttk.Combobox(
            row1, 
            textvariable=self.var_video_quality, 
            state="readonly",
            values=["low", "medium", "high", "ultra"],
            width=8
        )
        quality_combo.pack(side="left", padx=6)
        
        # Hardware acceleration
        ttk.Checkbutton(
            row1, 
            text="Hardware Acceleration", 
            variable=self.var_hardware_acceleration
        ).pack(side="left", padx=20)
        
        # Segment recording row
        row2 = ttk.Frame(section)
        row2.pack(fill="x", pady=2)
        
        ttk.Checkbutton(
            row2, 
            text="Split into segments (for long recordings)", 
            variable=self.var_use_segments
        ).pack(side="left")
        
        ttk.Label(row2, text="Duration (min):").pack(side="left", padx=(10, 2))
        ttk.Entry(row2, textvariable=self.var_segment_duration, width=6).pack(side="left")

    def _build_controls_section(self, parent: ttk.Widget) -> None:
        """Build recording control buttons."""
        section = ttk.Frame(parent)
        section.pack(fill="x", pady=10)
        
        self.btn_start = ttk.Button(
            section, 
            text="Start Recording", 
            command=self._start_recording
        )
        self.btn_start.pack(side="left")
        
        self.btn_stop = ttk.Button(
            section, 
            text="Stop Recording", 
            command=self._stop_recording
        )
        self.btn_stop.pack(side="left", padx=6)

    def _build_status_section(self, parent: ttk.Widget) -> None:
        """Build status display."""
        ttk.Label(parent, textvariable=self.var_status).pack(
            anchor="w", pady=(6, 0)
        )

    def _toggle_region_controls(self) -> None:
        """Enable/disable region coordinate controls based on checkbox."""
        state = "!disabled" if self.var_use_region.get() else "disabled"
        for entry in (self.ent_left, self.ent_top, self.ent_width, self.ent_height):
            entry.state([state])

    def _update_button_states(self) -> None:
        """Update start/stop button states based on recording status."""
        if self.recording:
            self.btn_start.state(["disabled"])
            self.btn_stop.state(["!disabled"])
        else:
            self.btn_start.state(["!disabled"])
            self.btn_stop.state(["disabled"])

    def _pick_mouse_color(self) -> None:
        """Open color picker for mouse highlight color."""
        color = colorchooser.askcolor(title="Choose mouse highlight color")
        if color and color[0]:
            r, g, b = map(int, color[0])
            self.var_mouse_color = (b, g, r)  # Store as BGR for OpenCV

    def _browse_output(self) -> None:
        """Browse for output file location."""
        default_name = dt.datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            initialfile=default_name,
            title="Choose output file"
        )
        if path:
            self.var_output.set(path)

    def _browse_ffmpeg(self) -> None:
        """Browse for FFmpeg executable."""
        initial_dir = self.var_ffmpeg_path.get() or os.environ.get('ProgramFiles', 'C:/')
        
        if os.name == 'nt':
            path = filedialog.askopenfilename(
                title="Select ffmpeg.exe",
                initialdir=initial_dir,
                filetypes=[("FFmpeg executable", "ffmpeg.exe"), ("All files", "*.*")]
            )
        else:
            path = filedialog.askopenfilename(
                title="Select ffmpeg binary", 
                initialdir=initial_dir
            )
            
        if path:
            self.var_ffmpeg_path.set(path)
            # Test the selected FFmpeg
            success, message = test_ffmpeg(path)
            if success:
                self._set_status(f"FFmpeg selected: {os.path.basename(path)}")
            else:
                self._set_status(f"Warning: FFmpeg test failed - {message}")

    def _refresh_audio_devices(self) -> None:
        """Refresh the list of available audio devices."""
        loopback_mode = self.var_system_audio.get()
        self._audio_devices = get_audio_devices(loopback=loopback_mode)
        
        if hasattr(self, 'cmb_audio'):
            device_labels = [label for label, _ in self._audio_devices]
            self.cmb_audio['values'] = device_labels
            
            current_selection = self.var_audio_device.get()
            if current_selection not in device_labels:
                self.var_audio_device.set(device_labels[0])

    def _refresh_cameras(self) -> None:
        """Detect available cameras."""
        cameras = probe_cameras()
        if cameras:
            self.var_webcam_index.set(cameras[0])
            self._set_status(f"Cameras detected: {cameras}")
        else:
            self._set_status("No cameras detected")

    def _get_selected_audio_device_id(self) -> Optional[int]:
        """Get the device ID for the currently selected audio device."""
        selected_label = self.var_audio_device.get()
        for label, device_id in self._audio_devices:
            if label == selected_label:
                return device_id
        return None

    def _make_output_path(self) -> str:
        """Generate output file path with default if not specified."""
        path = self.var_output.get().strip()
        if not path:
            default_name = dt.datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
            path = os.path.join(os.getcwd(), default_name)
            
        # Ensure output directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def _parse_fps(self) -> int:
        """Parse and validate FPS setting."""
        try:
            fps = int(self.var_fps.get())
            if fps <= 0:
                raise ValueError("FPS must be positive")
            return fps
        except ValueError:
            raise ValueError("FPS must be a positive integer")

    def _validate_region(self) -> Optional[tuple[int, int, int, int]]:
        """Validate and return region coordinates if enabled."""
        if not self.var_use_region.get():
            return None
            
        try:
            left = int(self.var_region_left.get())
            top = int(self.var_region_top.get())
            width = int(self.var_region_width.get())
            height = int(self.var_region_height.get())
            
            if left < 0 or top < 0 or width <= 0 or height <= 0:
                raise ValueError("Invalid region coordinates")
                
            return (left, top, width, height)
        except ValueError:
            raise ValueError("Region coordinates must be valid positive integers")

    def _create_config(self) -> RecorderConfig:
        """Create recording configuration from UI settings."""
        return RecorderConfig(
            fps=self._parse_fps(),
            output_path=self._make_output_path(),
            monitor_index=int(self.var_monitor_index.get()),
            region=self._validate_region(),
            show_preview=self.var_preview.get(),
            # Mouse highlight
            mouse_highlight=self.var_mouse_highlight.get(),
            mouse_color=self.var_mouse_color,
            mouse_radius=int(self.var_mouse_radius.get()),
            mouse_alpha=float(self.var_mouse_alpha.get()),
            # Audio
            record_audio=self.var_record_audio.get(),
            audio_device=self._get_selected_audio_device_id(),
            system_audio_loopback=self.var_system_audio.get(),
            save_audio_separately=self.var_save_audio_separately.get(),
            # Webcam
            use_webcam=self.var_use_webcam.get(),
            webcam_index=int(self.var_webcam_index.get()),
            pip_position=self.var_pip_position.get(),
            pip_width_pct=int(self.var_pip_width_pct.get()),
            # Quality and performance
            video_quality=self.var_video_quality.get(),
            hardware_acceleration=self.var_hardware_acceleration.get(),
            use_segments=self.var_use_segments.get(),
            segment_duration_minutes=int(self.var_segment_duration.get()),
            # FFmpeg
            ffmpeg_path=self.var_ffmpeg_path.get().strip() or None,
        )

    def _set_status(self, message: str) -> None:
        """Update status message and refresh UI."""
        self.var_status.set(message)
        self.master.update_idletasks()

    def _start_recording(self) -> None:
        """Start screen recording with current configuration."""
        if self.recording:
            return
            
        try:
            # Validate audio dependencies
            if self.var_record_audio.get() and not is_audio_available():
                response = messagebox.askyesno(
                    "Audio Dependencies Missing",
                    "Audio recording requires sounddevice and soundfile packages.\n"
                    "Continue without audio recording?"
                )
                if not response:
                    return
                self.var_record_audio.set(False)
            
            # Create configuration
            config = self._create_config()
            
            # Create and start recorder
            self.recorder = ScreenRecorder(config, status_callback=self._set_status)
            self.recorder.start()
            
            # Update UI state
            self.recording = True
            self._update_button_states()
            
        except Exception as ex:
            messagebox.showerror("Recording Error", str(ex))
            self._set_status(f"Error: {ex}")

    def _stop_recording(self) -> None:
        """Stop current recording."""
        if not self.recording or not self.recorder:
            return
            
        try:
            self._set_status("Stopping recording...")
            self.recorder.stop()
            
            # Check for errors
            last_error = self.recorder.get_last_error()
            if last_error:
                self._set_status(f"Recording completed with warnings: {last_error}")
            else:
                self._set_status(f"Recording saved: {self.recorder.cfg.output_path}")
                
        except Exception as ex:
            messagebox.showerror("Stop Error", str(ex))
            self._set_status(f"Stop error: {ex}")
        finally:
            self.recording = False
            self._update_button_states()

    def _test_ffmpeg(self) -> None:
        """Test FFmpeg functionality and show results."""
        ffmpeg_path, source = find_ffmpeg_path(self.var_ffmpeg_path.get())
        
        if not ffmpeg_path:
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg not found.\n\n"
                "Please download FFmpeg from https://ffmpeg.org/download.html\n"
                "and set the path using the Browse button."
            )
            self._set_status("FFmpeg not found")
            return
            
        success, message = test_ffmpeg(ffmpeg_path)
        
        if success:
            messagebox.showinfo(
                "FFmpeg Test Successful",
                f"✓ FFmpeg is working!\n\n"
                f"Source: {source}\n"
                f"Path: {ffmpeg_path}\n"
                f"Version: {message}"
            )
            self._set_status(f"FFmpeg OK: {message}")
        else:
            messagebox.showerror(
                "FFmpeg Test Failed",
                f"FFmpeg test failed:\n{message}\n\n"
                f"Path tested: {ffmpeg_path}"
            )
            self._set_status(f"FFmpeg test failed: {message}")

    def _check_ffmpeg_startup(self) -> None:
        """Check FFmpeg availability on startup."""
        ffmpeg_path, source = find_ffmpeg_path(self.var_ffmpeg_path.get())
        
        if ffmpeg_path:
            self._set_status(f"Ready. FFmpeg found: {source}")
        else:
            self._set_status("Ready. Note: FFmpeg not found - audio merging disabled")

    def _on_close(self) -> None:
        """Handle application close event."""
        try:
            if self.recorder and self.recording:
                self.recorder.stop()
        except Exception:
            pass
        self.master.destroy()


def create_app() -> tk.Tk:
    """
    Create and configure the main application window.
    
    Returns:
        Configured Tkinter root window
    """
    root = tk.Tk()
    
    # Configure theme
    try:
        style = ttk.Style(root)
        if sys.platform == 'win32':
            style.theme_use('vista')
    except Exception:
        pass
    
    # Create application
    app = RecorderApp(root)
    
    # Configure window
    root.minsize(600, 700)
    
    return root
