"""
Clean and Simple Screen Recorder GUI
Minimal interface with essential features only.
"""

import os
import sys
import datetime as dt
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Handle imports
try:
    from ..core.config import RecorderConfig
    from ..core.video import ScreenRecorder
    from ..core.audio import is_audio_available
    from ..utils.helpers import find_ffmpeg_path
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.config import RecorderConfig
    from core.video import ScreenRecorder
    from core.audio import is_audio_available
    from utils.helpers import find_ffmpeg_path


class SimpleRecorderApp(ttk.Frame):
    """
    Simple and clean screen recorder interface.
    Essential features only - no clutter.
    """
    
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True, padx=20, pady=20)
        master.title("Screen Recorder")
        
        # Application state
        self.recording = False
        self.recorder: Optional[ScreenRecorder] = None
        
        # Initialize variables
        self._init_variables()
        
        # Build clean UI
        self._build_clean_ui()
        self._update_button_states()
        
        # Setup event handlers
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Check dependencies
        self._check_dependencies()

    def _init_variables(self) -> None:
        """Initialize essential UI variables only."""
        # Essential settings only
        self.var_output = tk.StringVar()
        self.var_fps = tk.StringVar(value="30")
        self.var_status = tk.StringVar(value="Ready to record")
        self.var_record_audio = tk.BooleanVar(value=True)
        self.var_video_quality = tk.StringVar(value="high")

    def _build_clean_ui(self) -> None:
        """Build clean, minimal interface."""
        # Title
        title_label = ttk.Label(self, text="🎬 Screen Recorder", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Output file section
        self._build_output_section()
        
        # Recording settings
        self._build_settings_section()
        
        # Control buttons
        self._build_controls_section()
        
        # Status
        self._build_status_section()

    def _build_output_section(self) -> None:
        """Build output file selection."""
        frame = ttk.LabelFrame(self, text="📁 Output File", padding=10)
        frame.pack(fill="x", pady=(0, 15))
        
        # Output path
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill="x", pady=5)
        
        ttk.Entry(path_frame, textvariable=self.var_output, 
                 font=("Arial", 9)).pack(side="left", fill="x", expand=True)
        
        ttk.Button(path_frame, text="Browse...", 
                  command=self._browse_output).pack(side="right", padx=(10, 0))

    def _build_settings_section(self) -> None:
        """Build essential recording settings."""
        frame = ttk.LabelFrame(self, text="⚙️ Settings", padding=10)
        frame.pack(fill="x", pady=(0, 15))
        
        # Settings grid
        settings_frame = ttk.Frame(frame)
        settings_frame.pack(fill="x")
        
        # Frame rate
        ttk.Label(settings_frame, text="Frame Rate:").grid(row=0, column=0, sticky="w", pady=5)
        fps_combo = ttk.Combobox(settings_frame, textvariable=self.var_fps, 
                                values=["15", "20", "24", "30", "60"], width=8, state="readonly")
        fps_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # Video quality
        ttk.Label(settings_frame, text="Quality:").grid(row=1, column=0, sticky="w", pady=5)
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.var_video_quality,
                                   values=["low", "medium", "high", "ultra"], width=8, state="readonly")
        quality_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # Audio recording
        ttk.Label(settings_frame, text="Audio:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Checkbutton(settings_frame, text="Record audio", 
                       variable=self.var_record_audio).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=5)

    def _build_controls_section(self) -> None:
        """Build recording control buttons."""
        frame = ttk.Frame(self)
        frame.pack(pady=20)
        
        # Start button (large and prominent)
        self.btn_start = ttk.Button(frame, text="🔴 Start Recording", 
                                   command=self._start_recording)
        self.btn_start.pack(side="left", padx=(0, 10))
        
        # Stop button
        self.btn_stop = ttk.Button(frame, text="⏹️ Stop Recording", 
                                  command=self._stop_recording)
        self.btn_stop.pack(side="left")
        
        # Configure button styles for better visibility
        style = ttk.Style()
        style.configure("Start.TButton")

    def _build_status_section(self) -> None:
        """Build status display."""
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(frame, text="Status:").pack(side="left")
        status_label = ttk.Label(frame, textvariable=self.var_status, 
                               foreground="blue")
        status_label.pack(side="left", padx=(10, 0))

    def _update_button_states(self) -> None:
        """Update button states based on recording status."""
        if self.recording:
            self.btn_start.state(["disabled"])
            self.btn_stop.state(["!disabled"])
            self.btn_start.configure(text="🔴 Recording...")
        else:
            self.btn_start.state(["!disabled"])
            self.btn_stop.state(["disabled"])
            self.btn_start.configure(text="🔴 Start Recording")

    def _browse_output(self) -> None:
        """Browse for output file location."""
        default_name = dt.datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save recording as..."
        )
        if path:
            self.var_output.set(path)

    def _make_output_path(self) -> str:
        """Generate output file path with default if not specified."""
        path = self.var_output.get().strip()
        if not path:
            default_name = dt.datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
            path = os.path.join(os.getcwd(), default_name)
            self.var_output.set(path)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def _create_config(self) -> RecorderConfig:
        """Create simple recording configuration."""
        return RecorderConfig(
            fps=int(self.var_fps.get()),
            output_path=self._make_output_path(),
            record_audio=self.var_record_audio.get(),
            video_quality=self.var_video_quality.get(),
            hardware_acceleration=True,
            # Keep it simple - use defaults for everything else
            monitor_index=0,
            region=None,
            show_preview=False,
            mouse_highlight=False,
            use_webcam=False,
            save_audio_separately=False,
            use_segments=False
        )

    def _set_status(self, message: str) -> None:
        """Update status message."""
        self.var_status.set(message)
        self.master.update_idletasks()

    def _start_recording(self) -> None:
        """Start screen recording."""
        if self.recording:
            return
            
        try:
            # Check audio dependencies if audio is enabled
            if self.var_record_audio.get() and not is_audio_available():
                response = messagebox.askyesno(
                    "Audio Not Available",
                    "Audio recording requires additional packages.\n"
                    "Continue without audio?"
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
            self._set_status("Recording...")
            
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to start recording:\n{ex}")
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
                self._set_status(f"Recording completed with warnings")
                messagebox.showwarning("Warning", f"Recording completed with warnings:\n{last_error}")
            else:
                self._set_status("Recording saved successfully")
                messagebox.showinfo("Success", f"Recording saved:\n{self.recorder.cfg.output_path}")
                
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to stop recording:\n{ex}")
            self._set_status(f"Stop error: {ex}")
        finally:
            self.recording = False
            self._update_button_states()

    def _check_dependencies(self) -> None:
        """Check for required dependencies."""
        ffmpeg_path, source = find_ffmpeg_path("")
        
        if ffmpeg_path:
            self._set_status("Ready to record")
        else:
            self._set_status("Ready (audio disabled - FFmpeg not found)")
            self.var_record_audio.set(False)

    def _on_close(self) -> None:
        """Handle application close."""
        try:
            if self.recorder and self.recording:
                self.recorder.stop()
        except Exception:
            pass
        self.master.destroy()


def create_clean_app() -> tk.Tk:
    """Create clean, simple screen recorder app."""
    root = tk.Tk()
    
    # Configure window
    root.geometry("500x400")
    root.minsize(450, 350)
    root.resizable(True, False)
    
    # Configure theme
    try:
        style = ttk.Style(root)
        if sys.platform == 'win32':
            style.theme_use('vista')
    except Exception:
        pass
    
    # Create application
    app = SimpleRecorderApp(root)
    
    return root


# For backward compatibility
RecorderApp = SimpleRecorderApp
create_app = create_clean_app
