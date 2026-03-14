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
from mistralai import Mistral

def transcribe_video(video_path: str, api_key: str = config.MISTRAL_API_KEY, dry_run: bool = False) -> list:
    """
    Transcribes a video file using the Mistral API.
    
    Args:
        video_path (str): The path to the local video file.
        api_key (str): The Mistral API key to authenticate the request.
        dry_run (bool): If True, returns a mock transcript. Default is False.
        
    Returns:
        list: A list of dictionaries containing 'text', 'start', and 'duration'.
    """
    if dry_run:
        print(f"[TEST MODE] Simulating Mistral API transcription for: {video_path}")
        return [
            {"text": "Stephen Curry with the ball.", "start": 0.0, "duration": 2.5},
            {"text": "He shoots from downtown... BANG!", "start": 2.5, "duration": 3.0}
        ]
        
    print(f"Extracting audio from {video_path}...")
    audio_path = "temp_audio.mp3"
    
    # Extract audio using ffmpeg
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    
    print(f"Sending {audio_path} to Mistral API...")
    client = Mistral(api_key=api_key)
    
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file, 
            model="voxtral-v1" # Use intended Mistral audio model
        )
        
    # Clean up temporary audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    # Map API response to expected [{text, start, duration}] structure
    return [
        {
            "text": segment.text, 
            "start": segment.start, 
            "duration": segment.end - segment.start
        } 
        for segment in response.segments
    ]

if __name__ == "__main__":
    print("Testing Mistral transcription script...")
    mock_transcript = transcribe_video(config.DEFAULT_TEST_VIDEO_PATH, dry_run=True)
    for segment in mock_transcript:
        print(f"[{segment['start']}s - {segment['start']+segment['duration']}s]: {segment['text']}")
