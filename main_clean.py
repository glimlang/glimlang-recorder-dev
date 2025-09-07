#!/usr/bin/env python3
"""
Clean Screen Recorder - Simplified Version
Essential features only for a clean user experience.
"""

import sys
import os

def main():
    """Launch the clean screen recorder application."""
    # Set working directory and Python path
    app_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(app_dir, 'src')
    
    # Change to app directory and add src to path
    os.chdir(app_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    try:
        # Import after path setup
        import tkinter as tk
        from ui.clean_window import create_clean_app
        
        # Create and run the clean app
        root = create_clean_app()
        
        print("🎬 Clean Screen Recorder started!")
        print("✨ Simple and focused interface")
        
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
