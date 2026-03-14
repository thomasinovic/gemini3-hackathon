"""
Feature: Video Sub-clipper and Editor

This module is responsible for taking the original full-length NBA video and 
a list of target timestamps, then cutting and stitching those segments together 
to create the final highlight reel.

Use Cases:
1. Automated Editing: Remove all dead time and non-relevant plays from a match.
2. Fast Rendering: Uses standard FFmpeg subprocess commands for high-speed video manipulation 
   without loading heavy video files into system RAM.
"""

import os
import subprocess
from dotenv import load_dotenv

load_dotenv()
DEFAULT_VIDEO = os.getenv("DEFAULT_TEST_VIDEO_PATH", "input_video/NBA_20240617_DAL_BOS_1080p60_ABC_mkv.mp4")

def create_highlight_reel(
    input_video: str,
    timestamps: list,
    output_video: str = "output/highlights.mp4",
    dry_run: bool = False,
    pre_roll_seconds: float = 2.0,
    post_roll_seconds: float = 1.0,
):
    """
    Clips specific segments from an input video and concatenates them into a new file.
    
    Args:
        input_video (str): Path to the source full match video.
        timestamps (list): List of dictionaries containing 'start' and 'end' in seconds.
        output_video (str): Path for the final rendered highlight reel.
        dry_run (bool): If True, prints the FFmpeg commands instead of executing them.
    """
    if not timestamps:
        print("No timestamps provided. Skipping rendering.")
        return

    if dry_run:
        print(f"[TEST MODE] Simulating video edit for {input_video}")
        for idx, ts in enumerate(timestamps):
            adjusted_start = max(0.0, ts["start"] - pre_roll_seconds)
            adjusted_end = ts["end"] + post_roll_seconds
            print(f"  -> Would cut clip {idx}: {adjusted_start}s to {adjusted_end}s")
        print(f"  -> Would concatenate into {output_video}")
        return

    # Create temporary text file for FFmpeg concat demuxer
    list_file = "concat_list.txt"
    with open(list_file, "w") as f:
        for idx, ts in enumerate(timestamps):
            clip_name = f"temp_clip_{idx}.mp4"
            start_time = max(0.0, ts["start"] - pre_roll_seconds)
            end_time = ts["end"] + post_roll_seconds
            duration = end_time - start_time
            
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), 
                "-i", input_video, "-c", "copy", clip_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            f.write(f"file '{os.path.abspath(clip_name).replace(chr(92), '/')}'\n")

    print(f"Stitching clips together into {output_video}...")
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_video)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, 
        "-c", "copy", output_video
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cleanup temporary files
    os.remove(list_file)
    for idx in range(len(timestamps)):
        clip_name = f"temp_clip_{idx}.mp4"
        if os.path.exists(clip_name):
            os.remove(clip_name)
            
    print("Highlight reel rendered successfully!")

if __name__ == "__main__":
    print("Testing Video Editor script...")
    mock_timestamps = [
        {"start": 10.5, "end": 15.0},
        {"start": 45.0, "end": 52.5},
        {"start": 120.0, "end": 130.0},
    ]
    create_highlight_reel(DEFAULT_VIDEO, mock_timestamps, dry_run=False)
