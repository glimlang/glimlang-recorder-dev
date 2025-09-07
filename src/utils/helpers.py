"""
Utility functions for the Screen Recorder application.
Contains helper functions and common utilities.
"""

import os
import shutil
import subprocess
from typing import Optional, Tuple


def fourcc_code(code: str) -> int:
    """
    Compute FOURCC integer code from a 4-char string without using cv2 helper.
    
    Args:
        code: 4-character string representing the codec
        
    Returns:
        Integer FOURCC code
    """
    if not isinstance(code, str) or len(code) != 4:
        return 0
    c1, c2, c3, c4 = code[0], code[1], code[2], code[3]
    return (
        (ord(c1) & 255)
        | ((ord(c2) & 255) << 8)
        | ((ord(c3) & 255) << 16)
        | ((ord(c4) & 255) << 24)
    )


def find_ffmpeg_path(config_path: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Find FFmpeg executable path using multiple search strategies.
    
    Args:
        config_path: User-provided FFmpeg path from configuration
        
    Returns:
        Tuple of (ffmpeg_path, source_description)
    """
    search_paths = []
    
    # 1. Check user-provided path in config
    if config_path:
        cand = config_path.strip()
        if cand:
            search_paths.append(f"Config path: {cand}")
            if os.path.isdir(cand):
                exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
                cand = os.path.join(cand, exe)
            if os.path.isfile(cand):
                return cand, f"User configuration: {cand}"
    
    # 2. Check FFMPEG_PATH environment variable
    env_path = os.environ.get('FFMPEG_PATH', '').strip()
    if env_path:
        search_paths.append(f"FFMPEG_PATH env: {env_path}")
        cand = env_path
        if os.path.isdir(cand):
            exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
            cand = os.path.join(cand, exe)
        if os.path.isfile(cand):
            return cand, f"FFMPEG_PATH environment: {env_path}"
    
    # 3. Check system PATH
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        search_paths.append(f"System PATH: {ffmpeg}")
        return ffmpeg, f"System PATH: {ffmpeg}"
    
    # 4. Check common Windows locations
    if os.name == 'nt':
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
            os.path.expanduser(r"~\Downloads\ffmpeg\bin\ffmpeg.exe")
        ]
        for path in common_paths:
            search_paths.append(f"Common location: {path}")
            if os.path.isfile(path):
                return path, f"Common location: {path}"
    
    # Not found - return search details for error reporting
    search_summary = "\n".join(f"- {path}" for path in search_paths[-5:])
    return None, f"Not found. Searched:\n{search_summary}"


def test_ffmpeg(ffmpeg_path: str) -> Tuple[bool, str]:
    """
    Test if FFmpeg executable is working.
    
    Args:
        ffmpeg_path: Path to FFmpeg executable
        
    Returns:
        Tuple of (success, message)
    """
    try:
        proc = subprocess.run(
            [ffmpeg_path, '-version'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=5
        )
        if proc.returncode == 0:
            # Extract version info
            version_line = proc.stdout.split('\n')[0] if proc.stdout else "Unknown version"
            return True, version_line
        else:
            return False, f"FFmpeg test failed: {proc.stderr}"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg test timed out"
    except FileNotFoundError:
        return False, f"FFmpeg executable not found or not executable: {ffmpeg_path}"
    except Exception as ex:
        return False, f"FFmpeg test error: {ex}"


def get_ffmpeg_error_message(config_path: Optional[str] = None) -> str:
    """
    Generate comprehensive error message for missing FFmpeg.
    
    Args:
        config_path: User-provided FFmpeg path from configuration
        
    Returns:
        Detailed error message with troubleshooting steps
    """
    _, search_details = find_ffmpeg_path(config_path)
    
    error_msg = f"FFmpeg not found. {search_details}"
    error_msg += "\n\nTo fix this:"
    error_msg += "\n1. Download FFmpeg from https://ffmpeg.org/download.html"
    error_msg += "\n2. Extract it and note the path to ffmpeg.exe"
    error_msg += "\n3. Either:"
    error_msg += "\n   - Set the path in the 'FFmpeg path' field in the Audio section"
    error_msg += "\n   - Add FFmpeg's bin folder to your system PATH"
    error_msg += "\n   - Set FFMPEG_PATH environment variable"
    
    return error_msg
