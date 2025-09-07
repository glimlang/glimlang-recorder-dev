# GUI Screen Recorder

A clean, simple, and powerful screen recording application with audio support.

## Features

- **Screen Recording**: High-quality screen capture with configurable frame rates
- **Audio Recording**: Synchronized audio recording with microphone support
- **Video Quality**: Multiple quality presets (Low, Medium, High, Ultra)
- **Simple Interface**: Clean, intuitive GUI for easy operation
- **Production Ready**: Optimized for reliable, long-duration recording

## Installation

1. **Install Python 3.8 or higher**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required for audio):
   - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Add to system PATH or specify path in the application

## Usage

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Configure recording:**
   - Choose output file location
   - Set frame rate (recommended: 30 FPS)
   - Enable audio if needed
   - Select video quality

3. **Record:**
   - Click "Start Recording"
   - Perform your screen actions
   - Click "Stop Recording" when done

## Requirements

- **Python**: 3.8+
- **Operating System**: Windows (primary), Linux/macOS (experimental)
- **Dependencies**: See `requirements.txt`
- **FFmpeg**: Required for audio recording

## File Structure

```
GUIScreenRecorder/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── src/
    ├── core/           # Core recording functionality
    ├── ui/             # User interface
    └── utils/          # Helper utilities
```

## Troubleshooting

**Audio not working:**
- Ensure FFmpeg is installed and in PATH
- Check audio device selection in the interface

**Performance issues:**
- Try lower frame rates (15-20 FPS)
- Use "Medium" or "Low" quality settings

**Large file sizes:**
- Use "Low" or "Medium" quality
- Consider shorter recording sessions

## License

This project is open source. Feel free to use and modify as needed.
