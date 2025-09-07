#!/usr/bin/env python3
"""
Quick Production Test
Tests the enhanced recording system with basic functionality.
"""

import sys
import os
import time

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test if all imports work correctly."""
    try:
        from src.core.video import ScreenRecorder
        from src.core.config import RecorderConfig
        print("✅ Imports successful")
        return True
    except Exception as ex:
        print(f"❌ Import failed: {ex}")
        return False

def test_basic_recording():
    """Test basic recording functionality."""
    try:
        from src.core.video import ScreenRecorder
        from src.core.config import RecorderConfig
        
        print("🎬 Testing basic recording functionality...")
        
        # Create output directory
        os.makedirs("./test_output", exist_ok=True)
        
        # Basic configuration
        config = RecorderConfig(
            fps=30,
            output_path="./test_output/basic_test.mp4",
            record_audio=False,  # Disable audio for simpler test
            video_quality="medium"
        )
        
        print(f"📋 Configuration: {config.fps} FPS, Quality: {config.video_quality}")
        
        # Track status messages
        status_messages = []
        def status_handler(msg):
            status_messages.append(msg)
            print(f"📝 {msg}")
        
        # Create recorder
        recorder = ScreenRecorder(config, status_callback=status_handler)
        print("✅ Recorder created successfully")
        
        # Test that recorder has the expected methods
        if not hasattr(recorder, 'start'):
            print("❌ Recorder missing 'start' method")
            return False
        
        if not hasattr(recorder, 'stop'):
            print("❌ Recorder missing 'stop' method")
            return False
        
        print("✅ Recorder has required methods")
        
        # Test quick recording
        print("🚀 Starting test recording...")
        recorder.start()
        time.sleep(3)  # Record for 3 seconds
        print("🛑 Stopping recording...")
        recorder.stop()
        
        # Wait for finalization
        time.sleep(2)
        
        # Check results
        if os.path.exists(config.output_path):
            file_size = os.path.getsize(config.output_path)
            print(f"✅ Video file created: {file_size:,} bytes")
            
            # Show status messages
            if status_messages:
                print(f"📋 Status messages received: {len(status_messages)}")
                for msg in status_messages[-3:]:  # Show last 3 messages
                    print(f"   • {msg}")
            
            return True
        else:
            print("❌ Video file not created")
            return False
            
    except Exception as ex:
        print(f"❌ Test failed: {ex}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run quick production tests."""
    print("🧪 Quick Production Test")
    print("=" * 40)
    
    test_count = 0
    passed_count = 0
    
    # Test 1: Imports
    test_count += 1
    if test_imports():
        passed_count += 1
    
    # Test 2: Basic recording
    test_count += 1
    if test_basic_recording():
        passed_count += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed_count}/{test_count} passed")
    
    if passed_count == test_count:
        print("🎉 All tests passed! Production system is working!")
    else:
        print("⚠️  Some tests failed - check the output above")

if __name__ == "__main__":
    main()
