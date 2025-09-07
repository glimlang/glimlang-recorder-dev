"""
AI-Style Color Themes for the Modern Screen Recorder
Additional color schemes and styling options.
"""

# AI-Inspired Color Palettes
THEMES = {
    "default": {
        'bg_primary': '#0D1117',      # GitHub dark background
        'bg_secondary': '#161B22',     # Secondary background
        'bg_tertiary': '#21262D',      # Card background
        'accent_blue': '#58A6FF',      # AI blue accent
        'accent_purple': '#BC8CFF',    # AI purple accent
        'accent_green': '#56D364',     # Success green
        'accent_orange': '#FF9500',    # Warning orange
        'accent_red': '#FF6B6B',       # Error red
        'text_primary': '#F0F6FC',     # Primary text
        'text_secondary': '#8B949E',   # Secondary text
        'border': '#30363D',           # Border color
    },
    
    "cyberpunk": {
        'bg_primary': '#0F0F0F',
        'bg_secondary': '#1A1A1A',
        'bg_tertiary': '#252525',
        'accent_blue': '#00FFFF',      # Cyan
        'accent_purple': '#FF00FF',    # Magenta
        'accent_green': '#00FF00',     # Neon green
        'accent_orange': '#FFA500',    # Orange
        'accent_red': '#FF0040',       # Hot pink
        'text_primary': '#FFFFFF',
        'text_secondary': '#CCCCCC',
        'border': '#444444',
    },
    
    "ocean": {
        'bg_primary': '#0A1628',       # Deep ocean
        'bg_secondary': '#1B2B3A',     # Ocean depths
        'bg_tertiary': '#2C3E50',      # Deep blue
        'accent_blue': '#3498DB',      # Ocean blue
        'accent_purple': '#9B59B6',    # Sea purple
        'accent_green': '#27AE60',     # Sea green
        'accent_orange': '#F39C12',    # Coral
        'accent_red': '#E74C3C',       # Coral red
        'text_primary': '#ECF0F1',     # Sea foam
        'text_secondary': '#BDC3C7',   # Light blue-gray
        'border': '#34495E',
    },
    
    "forest": {
        'bg_primary': '#1B2F1B',       # Dark forest
        'bg_secondary': '#2D4A2D',     # Forest shadow
        'bg_tertiary': '#3E5E3E',      # Tree trunk
        'accent_blue': '#4A90E2',      # Sky blue
        'accent_purple': '#8E44AD',    # Violet
        'accent_green': '#27AE60',     # Forest green
        'accent_orange': '#E67E22',    # Autumn orange
        'accent_red': '#C0392B',       # Berry red
        'text_primary': '#EAFFE0',     # Light green
        'text_secondary': '#A0C090',   # Forest gray
        'border': '#5A7A5A',
    },
    
    "space": {
        'bg_primary': '#0A0A0F',       # Deep space
        'bg_secondary': '#151520',     # Nebula
        'bg_tertiary': '#202030',      # Starfield
        'accent_blue': '#4169E1',      # Royal blue
        'accent_purple': '#8A2BE2',    # Blue violet
        'accent_green': '#32CD32',     # Lime green
        'accent_orange': '#FF6347',    # Tomato
        'accent_red': '#DC143C',       # Crimson
        'text_primary': '#F8F8FF',     # Ghost white
        'text_secondary': '#C0C0C0',   # Silver
        'border': '#483D8B',           # Dark slate blue
    },
    
    "neon": {
        'bg_primary': '#000000',       # Pure black
        'bg_secondary': '#111111',     # Almost black
        'bg_tertiary': '#222222',      # Dark gray
        'accent_blue': '#00BFFF',      # Deep sky blue
        'accent_purple': '#DA70D6',    # Orchid
        'accent_green': '#ADFF2F',     # Green yellow
        'accent_orange': '#FF1493',    # Deep pink
        'accent_red': '#FF4500',       # Orange red
        'text_primary': '#FFFFFF',     # Pure white
        'text_secondary': '#DDDDDD',   # Light gray
        'border': '#555555',           # Medium gray
    },
    
    "minimal": {
        'bg_primary': '#FAFAFA',       # Very light gray
        'bg_secondary': '#F5F5F5',     # Light gray
        'bg_tertiary': '#EEEEEE',      # Lighter gray
        'accent_blue': '#2196F3',      # Material blue
        'accent_purple': '#9C27B0',    # Material purple
        'accent_green': '#4CAF50',     # Material green
        'accent_orange': '#FF9800',    # Material orange
        'accent_red': '#F44336',       # Material red
        'text_primary': '#212121',     # Dark gray
        'text_secondary': '#757575',   # Medium gray
        'border': '#E0E0E0',           # Light border
    }
}

def get_theme(theme_name: str = "default"):
    """Get color theme by name."""
    return THEMES.get(theme_name, THEMES["default"])

def get_available_themes():
    """Get list of available theme names."""
    return list(THEMES.keys())

# Gradient definitions for advanced styling
GRADIENTS = {
    "ai_blue": ["#1e3c72", "#2a5298"],
    "ai_purple": ["#667eea", "#764ba2"],
    "sunset": ["#ff7e5f", "#feb47b"],
    "ocean": ["#2b5876", "#4e4376"],
    "forest": ["#134e5e", "#71b280"],
    "neon": ["#ff006e", "#8338ec"],
}

# Animation configurations
ANIMATIONS = {
    "button_hover": {
        "duration": 200,  # milliseconds
        "easing": "ease-out",
    },
    "tab_switch": {
        "duration": 150,
        "easing": "ease-in-out",
    },
    "status_update": {
        "duration": 300,
        "easing": "ease-out",
    }
}

# Professional design constants
DESIGN = {
    "border_radius": 8,
    "shadow_blur": 10,
    "shadow_offset": (0, 2),
    "card_padding": 15,
    "button_padding": (20, 10),
    "icon_size": 16,
    "title_font_size": 12,
    "body_font_size": 10,
    "small_font_size": 9,
}
