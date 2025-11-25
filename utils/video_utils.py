"""
A module for reading and writing video files.

This module provides utility functions to load video frames into memory and save
processed frames back to video files, with support for common video formats.
"""

import cv2
import os

def read_video(video_path, start_time=None, end_time=None):
    """
    Read all frames from a video file into memory.

    Args:
        video_path (str): Path to the input video file.
        start_time (float): Start time in seconds (optional).
        end_time (float): End time in seconds (optional).

    Returns:
        list: List of video frames as numpy arrays.
    """
    import psutil
    import sys
    
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties for memory estimation
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Calculate frame numbers from timestamps
    start_frame = int(start_time * fps) if start_time is not None else 0
    end_frame = int(end_time * fps) if end_time is not None else total_frames
    
    # Calculate frames to load
    frames_to_load = end_frame - start_frame
    if frames_to_load <= 0:
        frames_to_load = total_frames # Fallback if calc is wrong
        
    # Estimate memory usage: Width * Height * 3 channels * Frames
    bytes_per_frame = width * height * 3
    est_memory_bytes = bytes_per_frame * frames_to_load
    est_memory_gb = est_memory_bytes / (1024**3)
    
    # Get available system memory
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)
    
    print(f"📊 Video Diagnostics:")
    print(f"   Resolution: {width}x{height}")
    print(f"   Frames to load: {frames_to_load} (from {total_frames} total)")
    print(f"   Estimated RAM required: {est_memory_gb:.2f} GB")
    print(f"   Available RAM: {available_gb:.2f} GB")
    
    if est_memory_gb > available_gb * 0.8:
        print(f"⚠️  WARNING: This video requires {est_memory_gb:.2f} GB of RAM but only {available_gb:.2f} GB is available.")
        print(f"   The process will likely crash with 'Killed: 9'.")
        print(f"   👉 Solution: Use --start-time and --end-time to process a smaller segment.")
        print(f"   Example: --start-time 0:00 --end-time 1:00")

    
    frames = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames before start_time
        if frame_count < start_frame:
            frame_count += 1
            continue
        
        # Stop at end_time
        if end_frame is not None and frame_count >= end_frame:
            break
        
        frames.append(frame)
        frame_count += 1
    
    cap.release()
    
    if start_time is not None or end_time is not None:
        print(f"⏱️  Loaded {len(frames)} frames from {start_time or 0}s to {end_time or 'end'}s")
    
    return frames

def read_video_in_batches(video_path, batch_size=100, start_time=None, end_time=None):
    """
    Generator that yields batches of frames from a video file.
    
    Args:
        video_path (str): Path to the input video file.
        batch_size (int): Number of frames to yield per batch.
        start_time (float): Start time in seconds (optional).
        end_time (float): End time in seconds (optional).
        
    Yields:
        list: A batch of video frames as numpy arrays.
    """
    cap = cv2.VideoCapture(video_path)
    
    # Get video fps for timestamp calculations
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Calculate frame numbers from timestamps
    start_frame = int(start_time * fps) if start_time is not None else 0
    end_frame = int(end_time * fps) if end_time is not None else None
    
    current_batch = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames before start_time
        if frame_count < start_frame:
            frame_count += 1
            continue
        
        # Stop at end_time
        if end_frame is not None and frame_count >= end_frame:
            break
        
        current_batch.append(frame)
        
        # Yield batch if full
        if len(current_batch) >= batch_size:
            yield current_batch
            current_batch = []
            
        frame_count += 1
    
    # Yield remaining frames
    if current_batch:
        yield current_batch
    
    cap.release()

def save_video(ouput_video_frames,output_video_path):
    """
    Save a sequence of frames as a video file.

    Creates necessary directories if they don't exist and writes frames using XVID codec.

    Args:
        ouput_video_frames (list): List of frames to save.
        output_video_path (str): Path where the video should be saved.
    """
    # If folder doesn't exist, create it
    if not os.path.exists(os.path.dirname(output_video_path)):
        os.makedirs(os.path.dirname(output_video_path))

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video_path, fourcc, 24, (ouput_video_frames[0].shape[1], ouput_video_frames[0].shape[0]))
    for frame in ouput_video_frames:
        out.write(frame)
    out.release()