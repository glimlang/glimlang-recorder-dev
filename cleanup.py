#!/usr/bin/env python3
"""
Project Cleanup Script
Removes extra files and keeps only essential components.
"""

import os
import shutil

def cleanup_project():
    """Remove extra files and keep only essentials."""
    print("🧹 Cleaning up Screen Recorder project...")
    
    # Files to remove (extra tests and development artifacts)
    files_to_remove = [
        "test_codec_selection.py",
        "test_complete.py", 
        "test_enhancements.py",
        "test_integration.py",
        "test_sync.py",
        "test_video_fix.py",
        "test_production.py",
        "test_production_quick.py",
        "test_gui_integration.py",
        "test_features.py",
        "apply_audio_fix.py",
        "audio_debug.py",
        "src/core/video_backup.py",
        "src/core/clean_config.py",  # Not needed since we use the main config
    ]
    
    # Documentation files to remove (keep only essential ones)
    docs_to_remove = [
        "AUDIO_SOLUTION.md",
        "AUDIO_SOLUTION.pdf", 
        "BEST_APPROACH.md",
        "CLEANUP_SUMMARY.md",
        "CLEANUP_SUMMARY.pdf",
        "PERFORMANCE.md",
        "PROJECT_SUMMARY.md",
        "SYNC_SOLUTION.md"
    ]
    
    # Temporary/output files to remove
    temp_files = [
        "recording_*.mp4",
        "*_tmp_video.mp4",
        "*_audio.wav",
        "test_output/"
    ]
    
    removed_count = 0
    
    # Remove test files
    print("\n📝 Removing test files...")
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Removed: {file}")
                removed_count += 1
            except Exception as ex:
                print(f"   ⚠️  Could not remove {file}: {ex}")
    
    # Remove documentation files
    print("\n📚 Removing extra documentation...")
    for file in docs_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Removed: {file}")
                removed_count += 1
            except Exception as ex:
                print(f"   ⚠️  Could not remove {file}: {ex}")
    
    # Remove test output directory
    if os.path.exists("test_output"):
        try:
            shutil.rmtree("test_output")
            print(f"   ✅ Removed: test_output/")
            removed_count += 1
        except Exception as ex:
            print(f"   ⚠️  Could not remove test_output/: {ex}")
    
    # Remove temporary recording files
    print("\n🗑️  Removing temporary files...")
    for root, dirs, files in os.walk("."):
        for file in files:
            if (file.startswith("recording_") and file.endswith(".mp4")) or \
               (file.endswith("_tmp_video.mp4")) or \
               (file.endswith("_audio.wav") and "_20" in file):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"   ✅ Removed: {file}")
                    removed_count += 1
                except Exception as ex:
                    print(f"   ⚠️  Could not remove {file}: {ex}")
    
    print(f"\n🎉 Cleanup complete! Removed {removed_count} files/folders")
    
    # Show remaining structure
    print("\n📁 Clean project structure:")
    print("   ✅ main_clean.py (simplified launcher)")
    print("   ✅ main.py (full-featured launcher)")
    print("   ✅ requirements.txt")
    print("   ✅ README.md") 
    print("   ✅ src/")
    print("      ├── core/")
    print("      │   ├── video.py (recording engine)")
    print("      │   ├── audio.py (audio handling)")
    print("      │   └── config.py (configuration)")
    print("      ├── ui/")
    print("      │   ├── clean_window.py (simple interface)")
    print("      │   └── main_window.py (full interface)")
    print("      └── utils/")
    print("          └── helpers.py (utilities)")
    
    print("\n🚀 Your app is now clean and focused!")
    print("   • Use 'python main_clean.py' for simple interface")
    print("   • Use 'python main.py' for full-featured interface")

if __name__ == "__main__":
    cleanup_project()
