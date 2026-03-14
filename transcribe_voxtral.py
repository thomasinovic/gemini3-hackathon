"""
Feature: Voxtral/Mistral Video Transcription

This module is responsible for transcribing local video or audio files 
using the Mistral API (Voxtral). It returns detailed transcripts with timestamps.

Use Cases:
1. Custom Video Transcription: Process any local video file (e.g., NBA clips, custom recordings) 
   and get accurate text with start and duration timestamps.
2. Direct API Integration: Offload heavy ML compute to Mistral's remote endpoints.
"""

import config
import os
import subprocess
from mistralai.client import Mistral


def transcribe_video(video_path: str, api_key: str = config.MISTRAL_API_KEY) -> list:
    """
    Transcribes a video file using the Mistral API.
    
    Args:
        video_path (str): The path to the local video file.
        api_key (str): The Mistral API key to authenticate the request.
        dry_run (bool): If True, returns a mock transcript. Default is False.
        
    Returns:
        list: A list of dictionaries containing 'text', 'start', and 'transcript'.
    """
        
    print(f"Extracting audio from {video_path}...")
    audio_path = "temp_audio.mp3"
    
    # Extract audio using ffmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed to extract audio from {video_path}. Ensure the file exists and has an audio stream.") from e
        
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Failed to create {audio_path}. Check if ffmpeg is installed and working correctly.")
    
    print(f"Sending {audio_path} to Mistral API...")
    client = Mistral(api_key=api_key)
    
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file, 
            model="voxtral-v1",
            language="en",
            timestamps=True
        )
        
    # Clean up temporary audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    return [
        {
            "text": segment.text, 
            "start": segment.start, 
            "transcript": segment.text,
        } 
        for segment in response.segments
    ]

if __name__ == "__main__":
    print("Testing Mistral transcription script...")
    mock_transcript = transcribe_video(config.DEFAULT_TEST_VIDEO_PATH)
    for segment in mock_transcript:
        print(f"[{segment['start']}s]: {segment['text']}")
