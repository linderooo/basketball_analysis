import os
import re
import yt_dlp
from pathlib import Path

def is_youtube_url(url):
    """
    Check if the given string is a valid YouTube URL.
    
    Args:
        url (str): The URL string to check.
    
    Returns:
        bool: True if it's a YouTube URL, False otherwise.
    """
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
    return bool(re.match(youtube_regex, url))

def sanitize_filename(filename):
    """
    Remove invalid characters from filename.
    
    Args:
        filename (str): The filename to sanitize.
    
    Returns:
        str: Sanitized filename safe for filesystem.
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized

def parse_timestamp(timestamp):
    """
    Convert timestamp string to seconds.
    Supports formats: "MM:SS" or "HH:MM:SS" or just seconds as integer
    
    Args:
        timestamp (str): Time string to parse.
    
    Returns:
        int: Time in seconds, or None if invalid.
    """
    if timestamp is None:
        return None
    
    try:
        # Try parsing as integer (seconds)
        return int(timestamp)
    except ValueError:
        pass
    
    # Try parsing as time format
    parts = timestamp.split(':')
    try:
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, IndexError):
        pass
    
    return None

def download_youtube_video(youtube_url, output_dir='input_videos', start_time=None, end_time=None):
    """
    Download a YouTube video and return the path to the downloaded file.
    
    Args:
        youtube_url (str): The YouTube URL to download.
        output_dir (str): Directory to save the downloaded video (default: 'input_videos').
        start_time (str): Start time for download (format: "HH:MM:SS", "MM:SS", or seconds).
        end_time (str): End time for download (format: "HH:MM:SS", "MM:SS", or seconds).
    
    Returns:
        tuple: (video_path, video_title) - Path to downloaded video and its title,
               or (None, None) if download fails.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse timestamps
        start_sec = parse_timestamp(start_time)
        end_sec = parse_timestamp(end_time)
        
        # Configure yt-dlp options with sanitized filename template
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer mp4, fallback to best available
            'outtmpl': os.path.join(output_dir, '%(title).200B.%(ext)s'),  # Use 200 byte limit to avoid long names
            'quiet': False,
            'no_warnings': False,
            'restrictfilenames': True,  # This will remove problematic characters including /
        }
        
        # Initialize postprocessor args with faststart to move moov atom
        postprocessor_args = ['-movflags', '+faststart']
        
        # Add download range if timestamps are specified
        if start_sec is not None or end_sec is not None:
            if start_sec is not None:
                postprocessor_args.extend(['-ss', str(start_sec)])
            if end_sec is not None:
                if start_sec is not None:
                    duration = end_sec - start_sec
                    postprocessor_args.extend(['-t', str(duration)])
                else:
                    postprocessor_args.extend(['-to', str(end_sec)])
            
            print(f"⏱️  Downloading segment: {start_time or '00:00'} to {end_time or 'end'}")
            
        # Add postprocessor args to options
        ydl_opts['postprocessor_args'] = {'ffmpeg': postprocessor_args}
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_title = info.get('title', 'youtube_video')
            
            # Get the actual filename that yt-dlp created (with restricted characters)
            downloaded_file = ydl.prepare_filename(info)
            
            if os.path.exists(downloaded_file):
                print(f"✅ Downloaded: {video_title}")
                return downloaded_file, video_title
            else:
                # Try to find the file - yt-dlp might have saved it with a slightly different name
                # Look for any mp4/mkv/webm files in the output directory that were just created
                import glob
                import time
                recent_files = []
                for pattern in ['*.mp4', '*.mkv', '*.webm']:
                    files = glob.glob(os.path.join(output_dir, '**', pattern), recursive=True)
                    # Get files modified in the last 60 seconds
                    recent_files.extend([f for f in files if time.time() - os.path.getmtime(f) < 60])
                
                if recent_files:
                    # Use the most recently modified file
                    downloaded_file = max(recent_files, key=os.path.getmtime)
                    print(f"✅ Downloaded: {video_title}")
                    print(f"📁 File location: {downloaded_file}")
                    return downloaded_file, video_title
                else:
                    print(f"❌ Download failed: Could not locate downloaded file")
                    return None, None
                
    except Exception as e:
        print(f"❌ Error downloading YouTube video: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def cleanup_downloaded_video(video_path):
    """
    Delete a downloaded video file.
    
    Args:
        video_path (str): Path to the video file to delete.
    """
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"🗑️  Cleaned up: {os.path.basename(video_path)}")
    except Exception as e:
        print(f"⚠️  Warning: Could not delete {video_path}: {e}")
