#!/usr/bin/env python3
"""
GUI Screen Recorder - Performance Optimized
Features: GPU acceleration, Enhanced audio integration, Modular architecture
"""

import sys
import os

def main():
    """Launch the GUI Screen Recorder application."""
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
        from ui.main_window import RecorderApp
        
        # Create application window
        root = tk.Tk()
        root.title("GUI Screen Recorder - Performance Optimized")
        root.geometry("600x500")
        
        # Initialize and run the app
        app = RecorderApp(root)
        
        print("🚀 GUI Screen Recorder started successfully!")
        print("✅ Features: GPU acceleration, Enhanced audio integration, Performance optimized")
        
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
