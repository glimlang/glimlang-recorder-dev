"""
Professional AI-Style UI for Screen Recorder
Modern tabbed interface with attractive colors and professional design.
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


class ModernRecorderApp(ttk.Frame):
    """
    Modern, professional screen recorder application with AI-style design.
    Features tabbed interface, attractive colors, and comprehensive controls.
    """
    
    def __init__(self, master: tk.Tk):
        """Initialize the modern recorder application."""
        super().__init__(master)
        self.master = master
        
        # Configure modern styling
        self._setup_modern_style()
        
        # Application state
        self.recording = False
        self.recorder: Optional[ScreenRecorder] = None
        
        # Initialize UI variables
        self._init_variables()
        
        # Build modern interface
        self._build_modern_ui()
        self._update_button_states()
        
        # Setup event handlers
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize device lists
        self._refresh_audio_devices()
        self._refresh_cameras()
        
        # Check FFmpeg availability
        self._check_ffmpeg_startup()

    def _setup_modern_style(self) -> None:
        """Setup modern AI-style theme and colors."""
        self.pack(fill="both", expand=True)
        
        # Configure window (smaller by default, not maximized)
        self.master.title("🎬 AI Screen Recorder Pro")
        self.master.geometry("1000x680")
        
        # Create modern style
        style = ttk.Style()
        
        # Import theme system and choose a softer, user-friendly default theme
        try:
            from .themes import get_theme, get_available_themes
            self.current_theme = "ocean"  # softer palette by default
            self.colors = get_theme(self.current_theme)
            self.available_themes = get_available_themes()
        except ImportError:
            # Fallback to a calm dark palette
            self.colors = {
                'bg_primary': '#1B2B3A',      # Calm dark blue
                'bg_secondary': '#223546',
                'bg_tertiary': '#2C3E50',
                'accent_blue': '#3498DB',
                'accent_purple': '#9B59B6',
                'accent_green': '#27AE60',
                'accent_orange': '#F39C12',
                'accent_red': '#E74C3C',
                'text_primary': '#ECF0F1',
                'text_secondary': '#BDC3C7',
                'border': '#34495E',
            }
        
        # Apply background based on theme
        self.master.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles
        style.theme_use('clam')
        
        # Configure Notebook (tabs)
        style.configure('Modern.TNotebook', 
                       background=self.colors['bg_primary'],
                       borderwidth=0,
                       tabmargins=[0, 0, 0, 0])
        
        style.configure('Modern.TNotebook.Tab',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'],
                       padding=[20, 10],
                       borderwidth=1,
                       focuscolor='none')
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colors['bg_tertiary']),
                           ('active', self.colors['accent_blue'])],
                 foreground=[('selected', self.colors['text_primary']),
                           ('active', self.colors['text_primary'])])
        
        # Configure Frames
        style.configure('Modern.TFrame', 
                       background=self.colors['bg_tertiary'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_tertiary'],
                       relief='solid',
                       borderwidth=1)
        
        # Configure Labels
        style.configure('Modern.TLabel',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10))
        
        style.configure('Title.TLabel',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['accent_blue'],
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 9))
        
        # Configure Buttons
        style.configure('Primary.TButton',
                       background=self.colors['accent_blue'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Primary.TButton',
                 background=[('active', '#4493E1'),
                           ('pressed', '#3D7FC4')])
        
        style.configure('Success.TButton',
                       background=self.colors['accent_green'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Success.TButton',
                 background=[('active', '#46C759'),
                           ('pressed', '#3DB84C')])
        
        style.configure('Danger.TButton',
                       background=self.colors['accent_red'],
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Danger.TButton',
                 background=[('active', '#E55A5A'),
                           ('pressed', '#CC5151')])
        
        # Configure Entry
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       insertcolor=self.colors['text_primary'])
        
        # Configure Combobox
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1)

    def _init_variables(self) -> None:
        """Initialize all Tkinter variables for UI controls."""
        # Basic recording settings
        self.var_output = tk.StringVar(value=self._default_output_path())
        self.var_fps = tk.StringVar(value="30")
        self.var_status = tk.StringVar(value="🟢 Ready to record")

        # Screen capture settings
        self.var_monitor_index = tk.IntVar(value=0)
        self.var_use_region = tk.BooleanVar(value=False)
        self.var_region_left = tk.IntVar(value=0)
        self.var_region_top = tk.IntVar(value=0)
        self.var_region_width = tk.IntVar(value=1920)
        self.var_region_height = tk.IntVar(value=1080)

        # Audio settings
        self.var_record_audio = tk.BooleanVar(value=True)
        self.var_system_audio = tk.BooleanVar(value=False)
        self.var_audio_device = tk.StringVar(value="Default")
        self.var_save_audio_separately = tk.BooleanVar(value=False)
        self.var_ffmpeg_path = tk.StringVar(value=os.environ.get('FFMPEG_PATH', ''))

        # Video quality and effects
        self.var_video_quality = tk.StringVar(value="high")
        self.var_hardware_acceleration = tk.BooleanVar(value=True)
        self.var_mouse_highlight = tk.BooleanVar(value=True)
        self.var_mouse_radius = tk.IntVar(value=20)
        self.var_mouse_alpha = tk.DoubleVar(value=0.35)
        self.var_mouse_color = (0, 255, 255)  # BGR format

        # Webcam settings
        self.var_use_webcam = tk.BooleanVar(value=False)
        self.var_webcam_index = tk.IntVar(value=0)
        self.var_pip_position = tk.StringVar(value="bottom-right")
        self.var_pip_width_pct = tk.IntVar(value=20)

        # Advanced settings
        self.var_use_segments = tk.BooleanVar(value=False)
        self.var_segment_duration = tk.IntVar(value=60)
        self.var_show_preview = tk.BooleanVar(value=False)

        # Audio device list
        self._audio_devices = [("Default", None)]

    def _build_modern_ui(self) -> None:
        """Build the modern tabbed interface."""
        # Main container with gradient effect
        main_container = tk.Frame(self, bg=self.colors['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header section
        self._build_header(main_container)
        
        # Tabbed interface
        self._build_tabbed_interface(main_container)
        
        # Control section
        self._build_control_section(main_container)
        
        # Status section
        self._build_status_section(main_container)

    def _build_header(self, parent) -> None:
        """Build the modern header section."""
        header_frame = tk.Frame(parent, bg=self.colors['bg_primary'], height=64)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)

        # Title and icon
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        title_frame.pack(side="left", fill="y")

        title_label = tk.Label(title_frame,
                              text="AI Screen Recorder Pro",
                              bg=self.colors['bg_primary'],
                              fg=self.colors['accent_blue'],
                              font=('Segoe UI', 18, 'bold'))
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(title_frame,
                                 text="Clean, professional recording with friendly colors",
                                 bg=self.colors['bg_primary'],
                                 fg=self.colors['text_secondary'],
                                 font=('Segoe UI', 10))
        subtitle_label.pack(anchor="w")

        # Quick stats
        stats_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        stats_frame.pack(side="right", fill="y")

        # Recording indicator
        self.recording_indicator = tk.Label(stats_frame,
                                          text="Standby",
                                          bg=self.colors['bg_primary'],
                                          fg=self.colors['text_secondary'],
                                          font=('Segoe UI', 11, 'bold'))
        self.recording_indicator.pack(anchor="e", pady=(10, 0))

    def _build_tabbed_interface(self, parent) -> None:
        """Build the main tabbed interface."""
        # Create notebook with modern style
        self.notebook = ttk.Notebook(parent, style='Modern.TNotebook')
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))
        
        # Tab 1: Recording Settings
        self._build_recording_tab()
        
        # Tab 2: Audio & Effects
        self._build_audio_effects_tab()
        
        # Tab 3: Advanced Settings
        self._build_advanced_tab()
        
        # Tab 4: System & Performance
        self._build_system_tab()

    def _build_recording_tab(self) -> None:
        """Build the main recording settings tab."""
        tab_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(tab_frame, text="📹 Recording")
        
        # Create scrollable content
        canvas = tk.Canvas(tab_frame, bg=self.colors['bg_tertiary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Output Settings Card
        self._build_card(scrollable_frame, "📁 Output Settings", self._build_output_controls)
        
        # Screen Capture Card
        self._build_card(scrollable_frame, "🖥️ Screen Capture", self._build_screen_controls)
        
        # Quality Settings Card
        self._build_card(scrollable_frame, "⚙️ Quality & Performance", self._build_quality_controls)

    def _build_audio_effects_tab(self) -> None:
        """Build the audio and effects tab."""
        tab_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(tab_frame, text="🎵 Audio & Effects")
        
        # Create scrollable content
        canvas = tk.Canvas(tab_frame, bg=self.colors['bg_tertiary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Audio Settings Card
        self._build_card(scrollable_frame, "🎤 Audio Recording", self._build_audio_controls)
        
        # Effects Card
        self._build_card(scrollable_frame, "✨ Visual Effects", self._build_effects_controls)
        
        # Webcam Card
        self._build_card(scrollable_frame, "📷 Webcam Overlay", self._build_webcam_controls)

    def _build_advanced_tab(self) -> None:
        """Build the advanced settings tab."""
        tab_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(tab_frame, text="🔧 Advanced")
        
        # Create scrollable content
        canvas = tk.Canvas(tab_frame, bg=self.colors['bg_tertiary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Advanced Recording Card
        self._build_card(scrollable_frame, "⚙️ Advanced Recording", self._build_advanced_controls)
        
        # FFmpeg Configuration Card
        self._build_card(scrollable_frame, "🛠️ FFmpeg Configuration", self._build_ffmpeg_controls)

    def _build_system_tab(self) -> None:
        """Build the system and performance tab."""
        tab_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(tab_frame, text="🖥️ System")
        
        # Create scrollable content
        canvas = tk.Canvas(tab_frame, bg=self.colors['bg_tertiary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Theme Selection Card
        self._build_card(scrollable_frame, "🎨 Theme Selection", self._build_theme_selector)
        
        # System Information Card
        self._build_card(scrollable_frame, "💻 System Information", self._build_system_info)
        
        # Performance Monitoring Card
        self._build_card(scrollable_frame, "📊 Performance Monitoring", self._build_performance_monitor)

    def _build_card(self, parent, title: str, content_builder) -> None:
        """Build a modern card with title and content."""
        # Card container
        card_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='solid', borderwidth=1)
        card_frame.pack(fill="x", padx=10, pady=10)
        
        # Card header
        header_frame = tk.Frame(card_frame, bg=self.colors['accent_blue'], height=40)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame,
                              text=title,
                              bg=self.colors['accent_blue'],
                              fg='white',
                              font=('Segoe UI', 12, 'bold'))
        title_label.pack(side="left", padx=15, pady=10)
        
        # Card content
        content_frame = tk.Frame(card_frame, bg=self.colors['bg_secondary'])
        content_frame.pack(fill="x", padx=15, pady=15)
        
        # Build content using the provided function
        content_builder(content_frame)

    def _build_output_controls(self, parent) -> None:
        """Build output file controls."""
        # Output path
        path_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        path_row.pack(fill="x", pady=(0, 10))

        tk.Label(path_row, text="📁 Output File:",
                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                 font=('Segoe UI', 10)).pack(side="left")

        self.output_entry = tk.Entry(path_row, textvariable=self.var_output,
                                     bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                     insertbackground=self.colors['text_primary'],
                                     font=('Segoe UI', 10), relief='flat', borderwidth=5)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(10, 5))

        browse_btn = tk.Button(path_row, text="Browse", command=self._browse_output,
                                bg=self.colors['accent_purple'], fg='white',
                                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                                padx=15, cursor='hand2')
        browse_btn.pack(side="right")

        # FPS setting
        fps_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        fps_row.pack(fill="x")

        tk.Label(fps_row, text="🎬 Frame Rate (FPS):",
                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                 font=('Segoe UI', 10)).pack(side="left")

        fps_entry = tk.Entry(fps_row, textvariable=self.var_fps, width=10,
                             bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                             insertbackground=self.colors['text_primary'],
                             font=('Segoe UI', 10), relief='flat', borderwidth=5)
        fps_entry.pack(side="left", padx=(10, 0))

        tk.Label(fps_row, text="(Recommended: 30 for quality, 15-20 for long sessions)",
                 bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                 font=('Segoe UI', 9)).pack(side="left", padx=(10, 0))

    def _build_screen_controls(self, parent) -> None:
        """Build screen capture controls."""
        # Monitor selection
        monitor_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        monitor_row.pack(fill="x", pady=(0, 10))
        
        tk.Label(monitor_row, text="🖥️ Monitor:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10)).pack(side="left")
        
        monitor_entry = tk.Entry(monitor_row, textvariable=self.var_monitor_index, width=5,
                               bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'],
                               font=('Segoe UI', 10), relief='flat', borderwidth=5)
        monitor_entry.pack(side="left", padx=(10, 0))
        
        tk.Label(monitor_row, text="(0 = all monitors)",
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                font=('Segoe UI', 9)).pack(side="left", padx=(10, 0))
        
        # Region capture
        region_check = tk.Checkbutton(parent, text="📐 Capture specific region",
                                    variable=self.var_use_region,
                                    command=self._toggle_region_controls,
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_primary'],
                                    font=('Segoe UI', 10), relief='flat')
        region_check.pack(anchor="w", pady=(0, 10))
        
        # Region coordinates
        self.region_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        self.region_frame.pack(fill="x")
        
        coords = [("Left", self.var_region_left), ("Top", self.var_region_top),
                 ("Width", self.var_region_width), ("Height", self.var_region_height)]
        
        for i, (label, var) in enumerate(coords):
            coord_frame = tk.Frame(self.region_frame, bg=self.colors['bg_secondary'])
            coord_frame.pack(side="left", padx=(0, 15))
            
            tk.Label(coord_frame, text=f"{label}:",
                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                    font=('Segoe UI', 9)).pack()
            
            entry = tk.Entry(coord_frame, textvariable=var, width=8,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                           insertbackground=self.colors['text_primary'],
                           font=('Segoe UI', 9), relief='flat', borderwidth=3)
            entry.pack()
            
            # Store entries for enable/disable
            if not hasattr(self, 'region_entries'):
                self.region_entries = []
            self.region_entries.append(entry)

    def _build_quality_controls(self, parent) -> None:
        """Build quality and performance controls."""
        # Quality selection
        quality_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        quality_row.pack(fill="x", pady=(0, 10))
        
        tk.Label(quality_row, text="⭐ Video Quality:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10)).pack(side="left")
        
        quality_frame = tk.Frame(quality_row, bg=self.colors['bg_secondary'])
        quality_frame.pack(side="left", padx=(10, 0))
        
        qualities = [("Low", "low"), ("Medium", "medium"), ("High", "high"), ("Ultra", "ultra")]
        for text, value in qualities:
            rb = tk.Radiobutton(quality_frame, text=text, variable=self.var_video_quality, value=value,
                              bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                              selectcolor=self.colors['accent_blue'],
                              font=('Segoe UI', 9), relief='flat')
            rb.pack(side="left", padx=(0, 10))
        
        # Hardware acceleration
        hw_check = tk.Checkbutton(parent, text="🚀 Hardware Acceleration (GPU)",
                                variable=self.var_hardware_acceleration,
                                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                selectcolor=self.colors['bg_primary'],
                                font=('Segoe UI', 10), relief='flat')
        hw_check.pack(anchor="w")

    def _build_audio_controls(self, parent) -> None:
        """Build audio recording controls."""
        # Audio enable
        audio_check = tk.Checkbutton(parent, text="🎤 Record Audio",
                                   variable=self.var_record_audio,
                                   bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                   selectcolor=self.colors['bg_primary'],
                                   font=('Segoe UI', 10, 'bold'), relief='flat')
        audio_check.pack(anchor="w", pady=(0, 10))
        
        # System audio
        system_check = tk.Checkbutton(parent, text="🔊 System Audio (Windows)",
                                    variable=self.var_system_audio,
                                    command=self._refresh_audio_devices,
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_primary'],
                                    font=('Segoe UI', 10), relief='flat')
        system_check.pack(anchor="w", pady=(0, 10))
        
        # Separate audio save
        separate_check = tk.Checkbutton(parent, text="💾 Save Audio Separately",
                                      variable=self.var_save_audio_separately,
                                      bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                      selectcolor=self.colors['bg_primary'],
                                      font=('Segoe UI', 10), relief='flat')
        separate_check.pack(anchor="w", pady=(0, 10))
        
        # Device selection
        device_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        device_row.pack(fill="x")
        
        tk.Label(device_row, text="🎧 Audio Device:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10)).pack(side="left")
        
        self.audio_combo = ttk.Combobox(device_row, textvariable=self.var_audio_device,
                                       style='Modern.TCombobox', state="readonly")
        self.audio_combo.pack(side="left", fill="x", expand=True, padx=(10, 5))
        
        refresh_btn = tk.Button(device_row, text="🔄", command=self._refresh_audio_devices,
                              bg=self.colors['accent_green'], fg='white',
                              font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                              width=3, cursor='hand2')
        refresh_btn.pack(side="right")

    def _build_effects_controls(self, parent) -> None:
        """Build visual effects controls."""
        # Mouse highlighting
        mouse_check = tk.Checkbutton(parent, text="🖱️ Mouse Highlighting",
                                   variable=self.var_mouse_highlight,
                                   bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                   selectcolor=self.colors['bg_primary'],
                                   font=('Segoe UI', 10, 'bold'), relief='flat')
        mouse_check.pack(anchor="w", pady=(0, 10))
        
        # Mouse settings
        mouse_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        mouse_frame.pack(fill="x")
        
        # Radius
        tk.Label(mouse_frame, text="Radius:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).pack(side="left")
        
        radius_entry = tk.Entry(mouse_frame, textvariable=self.var_mouse_radius, width=8,
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                              insertbackground=self.colors['text_primary'],
                              font=('Segoe UI', 9), relief='flat', borderwidth=3)
        radius_entry.pack(side="left", padx=(5, 15))
        
        # Opacity
        tk.Label(mouse_frame, text="Opacity:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).pack(side="left")
        
        opacity_entry = tk.Entry(mouse_frame, textvariable=self.var_mouse_alpha, width=8,
                               bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'],
                               font=('Segoe UI', 9), relief='flat', borderwidth=3)
        opacity_entry.pack(side="left", padx=(5, 15))
        
        # Color picker
        color_btn = tk.Button(mouse_frame, text="🎨 Pick Color", command=self._pick_mouse_color,
                            bg=self.colors['accent_orange'], fg='white',
                            font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                            padx=10, cursor='hand2')
        color_btn.pack(side="right")

    def _build_webcam_controls(self, parent) -> None:
        """Build webcam overlay controls."""
        # Webcam enable
        webcam_check = tk.Checkbutton(parent, text="📷 Webcam Overlay",
                                    variable=self.var_use_webcam,
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_primary'],
                                    font=('Segoe UI', 10, 'bold'), relief='flat')
        webcam_check.pack(anchor="w", pady=(0, 10))
        
        # Webcam settings
        webcam_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        webcam_frame.pack(fill="x")
        
        # Camera index
        tk.Label(webcam_frame, text="📹 Camera:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).pack(side="left")
        
        cam_entry = tk.Entry(webcam_frame, textvariable=self.var_webcam_index, width=5,
                           bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                           insertbackground=self.colors['text_primary'],
                           font=('Segoe UI', 9), relief='flat', borderwidth=3)
        cam_entry.pack(side="left", padx=(5, 15))
        
        # Position
        tk.Label(webcam_frame, text="📍 Position:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).pack(side="left")
        
        pos_combo = ttk.Combobox(webcam_frame, textvariable=self.var_pip_position,
                               style='Modern.TCombobox', state="readonly", width=12,
                               values=["top-left", "top-right", "bottom-left", "bottom-right"])
        pos_combo.pack(side="left", padx=(5, 15))
        
        # Size
        tk.Label(webcam_frame, text="📏 Size %:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).pack(side="left")
        
        size_entry = tk.Entry(webcam_frame, textvariable=self.var_pip_width_pct, width=5,
                            bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                            insertbackground=self.colors['text_primary'],
                            font=('Segoe UI', 9), relief='flat', borderwidth=3)
        size_entry.pack(side="left", padx=(5, 0))
        
        # Detect cameras
        detect_btn = tk.Button(webcam_frame, text="🔍 Detect", command=self._refresh_cameras,
                             bg=self.colors['accent_blue'], fg='white',
                             font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                             padx=10, cursor='hand2')
        detect_btn.pack(side="right")

    def _build_advanced_controls(self, parent) -> None:
        """Build advanced recording controls."""
        # Segment recording
        segment_check = tk.Checkbutton(parent, text="📂 Split into Segments (for long recordings)",
                                     variable=self.var_use_segments,
                                     bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                     selectcolor=self.colors['bg_primary'],
                                     font=('Segoe UI', 10), relief='flat')
        segment_check.pack(anchor="w", pady=(0, 10))
        
        # Segment duration
        duration_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        duration_row.pack(fill="x", pady=(0, 10))
        
        tk.Label(duration_row, text="⏱️ Segment Duration (minutes):",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10)).pack(side="left")
        
        duration_entry = tk.Entry(duration_row, textvariable=self.var_segment_duration, width=8,
                                bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                insertbackground=self.colors['text_primary'],
                                font=('Segoe UI', 10), relief='flat', borderwidth=5)
        duration_entry.pack(side="left", padx=(10, 0))
        
        # Preview mode
        preview_check = tk.Checkbutton(parent, text="👁️ Show Preview Window",
                                     variable=self.var_show_preview,
                                     bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                     selectcolor=self.colors['bg_primary'],
                                     font=('Segoe UI', 10), relief='flat')
        preview_check.pack(anchor="w")

    def _build_ffmpeg_controls(self, parent) -> None:
        """Build FFmpeg configuration controls."""
        # Info text
        info_label = tk.Label(parent,
                            text="FFmpeg is required for audio merging. Set path below or add to system PATH.",
                            bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                            font=('Segoe UI', 9), wraplength=400, justify="left")
        info_label.pack(anchor="w", pady=(0, 10))
        
        # FFmpeg path
        path_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        path_row.pack(fill="x")
        
        tk.Label(path_row, text="🛠️ FFmpeg Path:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10)).pack(side="left")
        
        ffmpeg_entry = tk.Entry(path_row, textvariable=self.var_ffmpeg_path,
                              bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                              insertbackground=self.colors['text_primary'],
                              font=('Segoe UI', 10), relief='flat', borderwidth=5)
        ffmpeg_entry.pack(side="left", fill="x", expand=True, padx=(10, 5))
        
        browse_btn = tk.Button(path_row, text="Browse", command=self._browse_ffmpeg,
                             bg=self.colors['accent_purple'], fg='white',
                             font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                             padx=10, cursor='hand2')
        browse_btn.pack(side="right", padx=(0, 5))
        
        test_btn = tk.Button(path_row, text="Test", command=self._test_ffmpeg,
                           bg=self.colors['accent_green'], fg='white',
                           font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                           padx=10, cursor='hand2')
        test_btn.pack(side="right")

    def _build_theme_selector(self, parent) -> None:
        """Build theme selection controls."""
        # Theme info
        info_label = tk.Label(parent,
                            text="Choose your preferred AI-style color theme for the interface.",
                            bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                            font=('Segoe UI', 9), wraplength=400, justify="left")
        info_label.pack(anchor="w", pady=(0, 10))
        
        # Theme selection
        theme_row = tk.Frame(parent, bg=self.colors['bg_secondary'])
        theme_row.pack(fill="x")
        
        tk.Label(theme_row, text="🎨 Color Theme:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10)).pack(side="left")
        
        # Theme dropdown
        if hasattr(self, 'available_themes'):
            theme_values = self.available_themes
        else:
            theme_values = ["default", "cyberpunk", "ocean", "forest", "space", "neon", "minimal"]
        
        self.var_theme = tk.StringVar(value=getattr(self, 'current_theme', 'default'))
        theme_combo = ttk.Combobox(theme_row, textvariable=self.var_theme,
                                 style='Modern.TCombobox', state="readonly",
                                 values=theme_values)
        theme_combo.pack(side="left", fill="x", expand=True, padx=(10, 5))
        theme_combo.bind('<<ComboboxSelected>>', self._change_theme)
        
        # Apply button
        apply_btn = tk.Button(theme_row, text="Apply Theme", command=self._apply_theme,
                            bg=self.colors['accent_purple'], fg='white',
                            font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0,
                            padx=15, cursor='hand2')
        apply_btn.pack(side="right")

    def _change_theme(self, event=None) -> None:
        """Handle theme selection change."""
        # This will be called when the combobox selection changes
        pass

    def _apply_theme(self) -> None:
        """Apply the selected theme to the interface."""
        try:
            from .themes import get_theme
            new_theme = self.var_theme.get()
            self.colors = get_theme(new_theme)
            self.current_theme = new_theme
            
            # Show success message
            self._set_status(f"🎨 Theme '{new_theme}' applied! Restart app for full effect.")
            
            messagebox.showinfo(
                "Theme Applied", 
                f"✨ Theme '{new_theme}' has been applied!\n\n"
                "Some changes may require restarting the application for full effect."
            )
            
        except ImportError:
            messagebox.showwarning(
                "Theme System Unavailable",
                "Theme system is not available. Using default colors."
            )
        except Exception as e:
            messagebox.showerror("Theme Error", f"Failed to apply theme: {e}")

    def _build_system_info(self, parent) -> None:
        """Build system information display."""
        import platform
        import psutil
        
        # System info
        info_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        info_frame.pack(fill="x")
        
        # OS Info
        os_row = tk.Frame(info_frame, bg=self.colors['bg_secondary'])
        os_row.pack(fill="x", pady=2)
        tk.Label(os_row, text="💻 Operating System:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(side="left")
        tk.Label(os_row, text=f"{platform.system()} {platform.release()}",
                bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'],
                font=('Segoe UI', 10)).pack(side="left", padx=(10, 0))
        
        # CPU Info
        cpu_row = tk.Frame(info_frame, bg=self.colors['bg_secondary'])
        cpu_row.pack(fill="x", pady=2)
        tk.Label(cpu_row, text="🔧 CPU Cores:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(side="left")
        tk.Label(cpu_row, text=f"{psutil.cpu_count()} cores",
                bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'],
                font=('Segoe UI', 10)).pack(side="left", padx=(10, 0))
        
        # Memory Info
        memory = psutil.virtual_memory()
        mem_row = tk.Frame(info_frame, bg=self.colors['bg_secondary'])
        mem_row.pack(fill="x", pady=2)
        tk.Label(mem_row, text="💾 RAM:",
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(side="left")
        tk.Label(mem_row, text=f"{memory.total // (1024**3)} GB",
                bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'],
                font=('Segoe UI', 10)).pack(side="left", padx=(10, 0))

    def _build_performance_monitor(self, parent) -> None:
        """Build performance monitoring display."""
        # Performance indicators
        self.perf_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        self.perf_frame.pack(fill="x")
        
        # CPU Usage
        self.cpu_label = tk.Label(self.perf_frame, text="⚡ CPU: 0%",
                                 bg=self.colors['bg_secondary'], fg=self.colors['accent_green'],
                                 font=('Segoe UI', 10, 'bold'))
        self.cpu_label.pack(side="left", padx=(0, 20))
        
        # Memory Usage
        self.mem_label = tk.Label(self.perf_frame, text="💾 Memory: 0%",
                                 bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'],
                                 font=('Segoe UI', 10, 'bold'))
        self.mem_label.pack(side="left", padx=(0, 20))
        
        # Recording Stats
        self.stats_label = tk.Label(self.perf_frame, text="📊 Frames: 0",
                                   bg=self.colors['bg_secondary'], fg=self.colors['accent_purple'],
                                   font=('Segoe UI', 10, 'bold'))
        self.stats_label.pack(side="left")
        
        # Start performance monitoring
        self._update_performance_monitor()

    def _build_control_section(self, parent) -> None:
        """Build the main control buttons section."""
        control_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Button container
        button_container = tk.Frame(control_frame, bg=self.colors['bg_primary'])
        button_container.pack(expand=True)
        
        # Start button
        self.btn_start = tk.Button(button_container,
                                  text="🎬 Start Recording",
                                  command=self._start_recording,
                                  bg=self.colors['accent_green'],
                                  fg='white',
                                  font=('Segoe UI', 14, 'bold'),
                                  relief='flat',
                                  borderwidth=0,
                                  padx=30,
                                  pady=15,
                                  cursor='hand2')
        self.btn_start.pack(side="left", padx=(0, 15))
        
        # Stop button
        self.btn_stop = tk.Button(button_container,
                                 text="⏹️ Stop Recording",
                                 command=self._stop_recording,
                                 bg=self.colors['accent_red'],
                                 fg='white',
                                 font=('Segoe UI', 14, 'bold'),
                                 relief='flat',
                                 borderwidth=0,
                                 padx=30,
                                 pady=15,
                                 cursor='hand2')
        self.btn_stop.pack(side="left")

    def _build_status_section(self, parent) -> None:
        """Build the status display section."""
        status_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='solid', borderwidth=1)
        status_frame.pack(fill="x")
        
        # Status header
        header_frame = tk.Frame(status_frame, bg=self.colors['accent_blue'], height=30)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📊 Status",
                bg=self.colors['accent_blue'], fg='white',
                font=('Segoe UI', 11, 'bold')).pack(side="left", padx=10, pady=5)
        
        # Status content
        content_frame = tk.Frame(status_frame, bg=self.colors['bg_secondary'])
        content_frame.pack(fill="x", padx=10, pady=10)
        
        self.status_label = tk.Label(content_frame,
                                   textvariable=self.var_status,
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_primary'],
                                   font=('Segoe UI', 11),
                                   anchor="w")
        self.status_label.pack(fill="x")

    # Helper methods and event handlers
    def _toggle_region_controls(self) -> None:
        """Enable/disable region coordinate controls."""
        state = tk.NORMAL if self.var_use_region.get() else tk.DISABLED
        for entry in getattr(self, 'region_entries', []):
            entry.configure(state=state)

    def _update_button_states(self) -> None:
        """Update button states based on recording status."""
        if self.recording:
            self.btn_start.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.NORMAL)
            self.recording_indicator.configure(text="🔴 Recording", fg=self.colors['accent_red'])
        else:
            self.btn_start.configure(state=tk.NORMAL)
            self.btn_stop.configure(state=tk.DISABLED)
            self.recording_indicator.configure(text="⚫ Standby", fg=self.colors['text_secondary'])

    def _update_performance_monitor(self) -> None:
        """Update performance monitoring display."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_label.configure(text=f"⚡ CPU: {cpu_percent:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            self.mem_label.configure(text=f"💾 Memory: {mem_percent:.1f}%")
            
            # Update colors based on usage
            if cpu_percent > 80:
                self.cpu_label.configure(fg=self.colors['accent_red'])
            elif cpu_percent > 60:
                self.cpu_label.configure(fg=self.colors['accent_orange'])
            else:
                self.cpu_label.configure(fg=self.colors['accent_green'])
                
            if mem_percent > 80:
                self.mem_label.configure(fg=self.colors['accent_red'])
            elif mem_percent > 60:
                self.mem_label.configure(fg=self.colors['accent_orange'])
            else:
                self.mem_label.configure(fg=self.colors['accent_blue'])
                
        except ImportError:
            pass
        
        # Schedule next update
        self.master.after(2000, self._update_performance_monitor)

    def _pick_mouse_color(self) -> None:
        """Open color picker for mouse highlight color."""
        color = colorchooser.askcolor(title="Choose mouse highlight color")
        if color and color[0]:
            r, g, b = map(int, color[0])
            self.var_mouse_color = (b, g, r)  # Store as BGR for OpenCV

    def _browse_output(self) -> None:
        """Browse for output file location."""
        default_name = dt.datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
        initial_dir = self._get_documents_folder()
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            initialfile=default_name,
            initialdir=initial_dir,
            title="Choose output file"
        )
        if path:
            self.var_output.set(path)

    def _get_documents_folder(self) -> str:
        """Return the user's Documents folder (Windows) or home/Documents fallback."""
        # Try HOME/Documents
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        if os.path.isdir(docs):
            return docs
        # Fallback to home
        return os.path.expanduser("~")

    def _default_output_path(self) -> str:
        """Default output path under Documents with a timestamped filename."""
        base = self._get_documents_folder()
        name = dt.datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
        return os.path.join(base, name)

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

    def _refresh_audio_devices(self) -> None:
        """Refresh the list of available audio devices."""
        loopback_mode = self.var_system_audio.get()
        self._audio_devices = get_audio_devices(loopback=loopback_mode)
        
        if hasattr(self, 'audio_combo'):
            device_labels = [label for label, _ in self._audio_devices]
            self.audio_combo['values'] = device_labels
            
            current_selection = self.var_audio_device.get()
            if current_selection not in device_labels:
                self.var_audio_device.set(device_labels[0])

    def _refresh_cameras(self) -> None:
        """Detect available cameras."""
        cameras = probe_cameras()
        if cameras:
            self.var_webcam_index.set(cameras[0])
            self._set_status(f"🎥 Cameras detected: {cameras}")
        else:
            self._set_status("⚠️ No cameras detected")

    def _test_ffmpeg(self) -> None:
        """Test FFmpeg functionality."""
        ffmpeg_path, source = find_ffmpeg_path(self.var_ffmpeg_path.get())
        
        if not ffmpeg_path:
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg not found.\n\n"
                "Please download FFmpeg from https://ffmpeg.org/download.html\n"
                "and set the path using the Browse button."
            )
            return
            
        success, message = test_ffmpeg(ffmpeg_path)
        
        if success:
            messagebox.showinfo(
                "FFmpeg Test Successful",
                f"✅ FFmpeg is working!\n\n"
                f"Source: {source}\n"
                f"Path: {ffmpeg_path}\n"
                f"Version: {message}"
            )
            self._set_status(f"✅ FFmpeg OK: {message}")
        else:
            messagebox.showerror(
                "FFmpeg Test Failed",
                f"❌ FFmpeg test failed:\n{message}"
            )

    def _check_ffmpeg_startup(self) -> None:
        """Check FFmpeg availability on startup."""
        ffmpeg_path, source = find_ffmpeg_path(self.var_ffmpeg_path.get())
        
        if ffmpeg_path:
            self._set_status(f"🟢 Ready to record. FFmpeg found: {source}")
        else:
            self._set_status("🟡 Ready. Note: FFmpeg not found - audio merging disabled")

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
            show_preview=self.var_show_preview.get(),
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
        """Update status message."""
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
            self._set_status(f"❌ Error: {ex}")

    def _stop_recording(self) -> None:
        """Stop current recording."""
        if not self.recording or not self.recorder:
            return
            
        try:
            self._set_status("⏹️ Stopping recording...")
            self.recorder.stop()
            
            # Check for errors
            last_error = self.recorder.get_last_error()
            if last_error:
                self._set_status(f"⚠️ Recording completed with warnings: {last_error}")
            else:
                self._set_status(f"✅ Recording saved: {self.recorder.cfg.output_path}")
                
        except Exception as ex:
            messagebox.showerror("Stop Error", str(ex))
            self._set_status(f"❌ Stop error: {ex}")
        finally:
            self.recording = False
            self._update_button_states()

    def _on_close(self) -> None:
        """Handle application close event."""
        try:
            if self.recorder and self.recording:
                self.recorder.stop()
        except Exception:
            pass
        self.master.destroy()


def create_modern_app() -> tk.Tk:
    """Create and configure the modern application window."""
    root = tk.Tk()
    
    # Create modern application
    app = ModernRecorderApp(root)
    
    # Configure window properties
    root.minsize(800, 560)
    # Start in a comfortable window size, not maximized
    try:
        root.geometry("1000x680")
    except Exception:
        pass
    
    return root
