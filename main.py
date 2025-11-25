import os
import argparse
import sys
import logging
from utils import read_video, save_video, is_youtube_url, download_youtube_video, cleanup_downloaded_video, read_video_in_batches
from utils.youtube_utils import parse_timestamp
from trackers import PlayerTracker, BallTracker
from team_assigner import TeamAssigner
from court_keypoint_detector import CourtKeypointDetector
from ball_aquisition import BallAquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from tactical_view_converter import TacticalViewConverter
from speed_and_distance_calculator import SpeedAndDistanceCalculator
from drawers import (
    PlayerTracksDrawer, 
    BallTracksDrawer,
    CourtKeypointDrawer,
    TeamBallControlDrawer,
    FrameNumberDrawer,
    PassInterceptionDrawer,
    TacticalViewDrawer,
    SpeedAndDistanceDrawer
)
from configs import(
    STUBS_DEFAULT_PATH,
    PLAYER_DETECTOR_PATH,
    BALL_DETECTOR_PATH,
    COURT_KEYPOINT_DETECTOR_PATH,
    OUTPUT_VIDEO_PATH
)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Basketball Video Analysis - Analyze local files or YouTube videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Analyze local video file
  python3 main.py --file input_videos/game.mp4
  
  # Analyze YouTube video
  python3 main.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Analyze specific segment (2 minutes to 5 minutes)
  python3 main.py --file input_videos/game.mp4 --start-time 2:00 --end-time 5:00
  
  # YouTube video segment
  python3 main.py --youtube "URL" --start-time 1:30 --end-time 3:45
        '''
    )
    
    # Logging
    parser.add_argument('--log-file', type=str, default=None,
                        help='Log file path for verbose output (default: print to console)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--device', type=str, choices=['cpu', 'cuda', 'mps'], default='cpu',
                        help='Device: cpu (low memory), cuda (NVIDIA GPU), mps (Apple Silicon GPU)')
    
    # Video source (mutually exclusive)
    video_source = parser.add_mutually_exclusive_group(required=True)
    video_source.add_argument('--file', type=str, metavar='PATH',
                              help='Path to local video file')
    video_source.add_argument('--youtube', type=str, metavar='URL',
                              help='YouTube video URL')
    
    # Optional arguments
    parser.add_argument('--output_video', type=str, default=None, 
                        help='Path to output video file (default: auto-generated based on input)')
    parser.add_argument('--start-time', type=str, default=None,
                        help='Start time (format: HH:MM:SS, MM:SS, or seconds)')
    parser.add_argument('--end-time', type=str, default=None,
                        help='End time (format: HH:MM:SS, MM:SS, or seconds)')
    parser.add_argument('--stub_path', type=str, default=STUBS_DEFAULT_PATH,
                        help='Path to stub directory for caching')
    parser.add_argument('--keep-youtube', action='store_true',
                        help='Keep downloaded YouTube video (default: delete after processing)')
    
    return parser.parse_args()

def setup_logging(args):
    """
    Configure logging based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
    """
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    if args.log_file:
        # Log to file
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(args.log_file),
                logging.StreamHandler(sys.stdout)  # Also print to console
            ]
        )
        logging.info(f"Logging to file: {args.log_file}")
    else:
        # Log to console only
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)]
        )

def main():
    args = parse_args()
    
    # Detect and display available hardware acceleration
    import torch
    print("\n🔍 Hardware Detection:")
    print(f"   CPU: ✅ Available")
    cuda_available = torch.cuda.is_available()
    mps_available = torch.backends.mps.is_available()
    print(f"   CUDA (NVIDIA GPU): {'✅ Available' if cuda_available else '❌ Not available'}")
    if cuda_available:
        print(f"      └─ {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB)")
    print(f"   MPS (Apple Silicon): {'✅ Available' if mps_available else '❌ Not available'}")
    print()
    
    # Determine input source and video path
    video_path = None
    video_title = None
    is_youtube = False
    cleanup_after = False
    
    if args.youtube:
        # Download YouTube video
        print(f"📺 Downloading YouTube video...")
        is_youtube = True
        
        # Parse timestamps for YouTube download
        start_time_str = args.start_time
        end_time_str = args.end_time
        
        video_path, video_title = download_youtube_video(
            args.youtube, 
            output_dir='input_videos',
            start_time=start_time_str,
            end_time=end_time_str
        )
        
        if video_path is None:
            print("❌ Failed to download YouTube video. Exiting.")
            sys.exit(1)
        
        cleanup_after = not args.keep_youtube
        
    elif args.file:
        # Use local file
        video_path = args.file
        video_title = os.path.splitext(os.path.basename(video_path))[0]
        
        if not os.path.exists(video_path):
            print(f"❌ Error: File not found: {video_path}")
            sys.exit(1)
    
    # Generate output filename if not provided
    if args.output_video is None:
        # Use video title (sanitized) for output filename
        from utils.youtube_utils import sanitize_filename
        safe_title = sanitize_filename(video_title)
        args.output_video = os.path.join('output_videos', f'{safe_title}_output.mov')
    
    # Check if model files exist
    missing_models = []
    for model_path in [PLAYER_DETECTOR_PATH, BALL_DETECTOR_PATH, COURT_KEYPOINT_DETECTOR_PATH]:
        if not os.path.exists(model_path):
            missing_models.append(model_path)
    
    if missing_models:
        print("\n❌ Error: Missing model files!")
        print("   The following models were not found:")
        for path in missing_models:
            print(f"   - {path}")
        print("\n   Please download/transfer these models to the 'models/' directory.")
        print("   If you are on a remote server, use 'scp' to upload them from your local machine.")
        sys.exit(1)

    # Initialize Trackers and Detectors
    player_tracker = PlayerTracker(PLAYER_DETECTOR_PATH)
    ball_tracker = BallTracker(BALL_DETECTOR_PATH)
    court_keypoint_detector = CourtKeypointDetector(COURT_KEYPOINT_DETECTOR_PATH)
    team_assigner = TeamAssigner()
    ball_aquisition_detector = BallAquisitionDetector()
    pass_and_interception_detector = PassAndInterceptionDetector()
    tactical_view_converter = TacticalViewConverter(court_image_path="./images/basketball_court.png")
    speed_and_distance_calculator = SpeedAndDistanceCalculator(
        tactical_view_converter.width,
        tactical_view_converter.height,
        tactical_view_converter.actual_width_in_meters,
        tactical_view_converter.actual_height_in_meters
    )
    
    # Initialize Drawers
    player_tracks_drawer = PlayerTracksDrawer()
    ball_tracks_drawer = BallTracksDrawer()
    court_keypoint_drawer = CourtKeypointDrawer()
    team_ball_control_drawer = TeamBallControlDrawer()
    frame_number_drawer = FrameNumberDrawer()
    pass_and_interceptions_drawer = PassInterceptionDrawer()
    tactical_view_drawer = TacticalViewDrawer()
    speed_and_distance_drawer = SpeedAndDistanceDrawer()

    print(f"🎬 Processing: {video_title}")
    print(f"💾 Output will be saved to: {args.output_video}")
    
    # Parse timestamps if provided
    start_sec = parse_timestamp(args.start_time) if args.start_time else None
    end_sec = parse_timestamp(args.end_time) if args.end_time else None
    
    # Batch processing setup - adaptive based on hardware
    if args.device == 'cuda':
        import torch
        # T4 GPU has 16GB VRAM - use larger batches
        BATCH_SIZE = 50  # Process fewer frames to avoid OOM
        if torch.cuda.is_available():
            print(f"🚀 GPU mode enabled: {torch.cuda.get_device_name(0)}")
            print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            print("⚠️  CUDA requested but not available. Falling back to CPU mode.")
            BATCH_SIZE = 30
    elif args.device == 'mps':
        import torch
        # Apple M-series with unified memory - moderate batches
        BATCH_SIZE = 100  # Process moderate frames with Apple GPU
        if torch.backends.mps.is_available():
            print("🍎 Apple Silicon GPU (MPS) mode enabled")
            print(f"   Device: {torch.backends.mps.device if hasattr(torch.backends.mps, 'device') else 'MPS'}")
        else:
            print("⚠️  MPS requested but not available. Falling back to CPU mode.")
            BATCH_SIZE = 30
    else:
        # CPU mode - conservative for low memory (< 2GB)
        BATCH_SIZE = 30  # Process 30 frames at a time to keep memory under 2GB
        print("💻 CPU mode: Using small batches for low memory usage")
    
    # Initialize video writer (we need the first frame to set it up)
    video_writer = None
    
    # Use the batch generator
    batch_generator = read_video_in_batches(video_path, batch_size=BATCH_SIZE, start_time=start_sec, end_time=end_sec)
    
    total_frames_processed = 0
    
    import cv2
    
    for batch_idx, video_frames in enumerate(batch_generator):
        print(f"📦 Processing Batch {batch_idx+1} ({len(video_frames)} frames)...")
        
        # Initialize video writer on first batch
        if video_writer is None and len(video_frames) > 0:
            if not os.path.exists(os.path.dirname(args.output_video)):
                os.makedirs(os.path.dirname(args.output_video))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MOV format for macOS
            video_writer = cv2.VideoWriter(args.output_video, fourcc, 24, 
                                         (video_frames[0].shape[1], video_frames[0].shape[0]))

        # --- Analysis Pipeline (Per Batch) ---
        
        # 1. Object Detection
        # Run player, ball, and court detection sequentially to avoid OOM on GPU
        
        # Note: We disable stubs for batch processing to ensure fresh tracking
        player_tracks = player_tracker.get_object_tracks(video_frames, read_from_stub=False)
        if args.device == 'cuda': torch.cuda.empty_cache()
        
        ball_tracks = ball_tracker.get_object_tracks(video_frames, read_from_stub=False)
        if args.device == 'cuda': torch.cuda.empty_cache()
        
        court_keypoints_per_frame = court_keypoint_detector.get_court_keypoints(video_frames, read_from_stub=False)
        if args.device == 'cuda': torch.cuda.empty_cache()
        
        
        # 3. Ball Refinement
        ball_tracks = ball_tracker.remove_wrong_detections(ball_tracks)
        ball_tracks = ball_tracker.interpolate_ball_positions(ball_tracks)
        
        # 4. Team Assignment
        player_assignment = team_assigner.get_player_teams_across_frames(video_frames, player_tracks, read_from_stub=False)
        
        # 5. Ball Possession
        ball_aquisition = ball_aquisition_detector.detect_ball_possession(player_tracks, ball_tracks)
        
        # 6. Events
        passes = pass_and_interception_detector.detect_passes(ball_aquisition, player_assignment)
        interceptions = pass_and_interception_detector.detect_interceptions(ball_aquisition, player_assignment)
        
        # 7. Tactical View
        court_keypoints_per_frame = tactical_view_converter.validate_keypoints(court_keypoints_per_frame)
        tactical_player_positions = tactical_view_converter.transform_players_to_tactical_view(court_keypoints_per_frame, player_tracks)
        
        # 8. Stats
        player_distances_per_frame = speed_and_distance_calculator.calculate_distance(tactical_player_positions)
        player_speed_per_frame = speed_and_distance_calculator.calculate_speed(player_distances_per_frame)
        
        # --- Drawing Pipeline ---
        
        output_video_frames = player_tracks_drawer.draw(video_frames, player_tracks, player_assignment, ball_aquisition)
        output_video_frames = ball_tracks_drawer.draw(output_video_frames, ball_tracks)
        output_video_frames = court_keypoint_drawer.draw(output_video_frames, court_keypoints_per_frame)
        output_video_frames = frame_number_drawer.draw(output_video_frames) # Note: Frame number might reset per batch, ideally needs offset
        output_video_frames = team_ball_control_drawer.draw(output_video_frames, player_assignment, ball_aquisition)
        output_video_frames = pass_and_interceptions_drawer.draw(output_video_frames, passes, interceptions)
        output_video_frames = speed_and_distance_drawer.draw(output_video_frames, player_tracks, player_distances_per_frame, player_speed_per_frame)
        output_video_frames = tactical_view_drawer.draw(output_video_frames,
                                                        tactical_view_converter.court_image_path,
                                                        tactical_view_converter.width,
                                                        tactical_view_converter.height,
                                                        tactical_view_converter.key_points,
                                                        tactical_player_positions,
                                                        player_assignment,
                                                        ball_aquisition)
                                                        
        # Write frames to video
        for frame in output_video_frames:
            video_writer.write(frame)
            
        total_frames_processed += len(video_frames)
        
        # Memory cleanup - delete all intermediate variables
        import gc
        # List of variables to clean up
        cleanup_vars = [
            'video_frames', 'output_video_frames', 'player_tracks', 'ball_tracks',
            'court_keypoints_per_frame', 'tactical_player_positions', 'player_assignment',
            'ball_aquisition', 'passes', 'interceptions', 'player_speeds',
            'player_distances_per_frame', 'player_speed_per_frame'
        ]
        # Safely delete each variable
        for var_name in cleanup_vars:
            try:
                exec(f'del {var_name}')
            except: pass
        gc.collect()
        
    if video_writer:
        video_writer.release()
    
    print(f"✅ Analysis complete! Processed {total_frames_processed} frames.")
    print(f"📁 Output saved to: {args.output_video}")
    
    # Cleanup downloaded YouTube video if needed
    if cleanup_after and video_path:
        cleanup_downloaded_video(video_path)

if __name__ == '__main__':
    main()
    