"""
Entry point for the modern AI-style Screen Recorder application.
Launches the professional UI with attractive design and multiple tabs.
"""

import os
import sys
import tkinter as tk

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.ui.modern_window import create_modern_app
except ImportError:
    # Fallback for direct execution
    from ui.modern_window import create_modern_app


def main():
    """Main entry point for the modern screen recorder application."""
    try:
        # Create and run the modern application
        root = create_modern_app()
        
        # Set application icon if available
        try:
            # Try to set a custom icon (you can replace this with your own icon file)
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception:
            pass  # Ignore icon errors
        
        # Start the application
        print("🎬 Starting AI Screen Recorder Pro...")
        print("💡 Modern UI with professional design and AI-style colors")
        print("📱 Features: Tabbed interface, performance monitoring, and more!")
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
