"""
Feature: Voxtral/Mistral Video Transcription

This module is responsible for transcribing local video or audio files 
using the Mistral API (Voxtral). It returns detailed transcripts with timestamps.

Use Cases:
1. Custom Video Transcription: Process any local video file (e.g., NBA clips, custom recordings) 
   and get accurate text with start and duration timestamps.
2. Direct API Integration: Offload heavy ML compute to Mistral's remote endpoints.
"""

import os
import subprocess
import json
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

def transcribe_video(video_path: str, api_key: str = None) -> list:
    """
    Transcribes a video file using the Mistral API.
    
    Args:
        video_path (str): The path to the local video file.
        api_key (str): The Mistral API key to authenticate the request.
        dry_run (bool): If True, returns a mock transcript. Default is False.
        
    Returns:
        list: A list of dictionaries containing 'text', 'start', and 'transcript'.
    """
    
    if api_key is None:
        api_key = os.getenv("MISTRAL_API_KEY")
        
    base_name = os.path.splitext(video_path)[0]
    json_path = f"{base_name}_transcript.json"
    audio_path = f"{base_name}_audio.mp3"
    
    if os.path.exists(json_path):
        print(f"Transcript already exists at {json_path}. Loading...")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    if not os.path.exists(audio_path):
        print(f"Extracting audio from {video_path}...")
        
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
    else:
        print(f"Audio already extracted at {audio_path}.")
    
    print(f"Sending {audio_path} to Mistral API...")
    client = Mistral(api_key=api_key)
    model = "voxtral-mini-latest"
    
    with open(audio_path, "rb") as audio_file:
        transcription_response = client.audio.transcriptions.complete(
            model=model,
            file={
                "file_name": os.path.basename(audio_path),
                "content": audio_file
            },
            timestamp_granularities=["segment"] # or "word"
        )
        
    transcript_data = [
        {
            "start": segment.start, 
            "text": segment.text, 
        } 
        for segment in transcription_response.segments
    ]
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=4)
        print(f"Saved transcript to {json_path}")
    
    return transcript_data

if __name__ == "__main__":
    print("Testing Mistral transcription script...")
    test_video = os.getenv("DEFAULT_TEST_VIDEO_PATH", "sample_video.mp4")
    mock_transcript = transcribe_video(test_video)
    for segment in mock_transcript:
        print(f"[{segment['start']}s]: {segment['text']}")
