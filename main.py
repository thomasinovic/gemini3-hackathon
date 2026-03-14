import json
import os
from dotenv import load_dotenv
from transcribe_voxtral import transcribe_video
from analyze_prompt import get_highlight_timestamps
from video_editor import create_highlight_reel

def main():
    load_dotenv()
    
    video_path = os.getenv("DEFAULT_TEST_VIDEO_PATH", "sample_video.mp4")
    playbyplay_path = os.getenv(
        "PLAYBYPLAY_TRANSCRIPT_PATH",
        "data_nba/playbyplay_0042300405_transcript.json",
    )
    
    if not os.path.exists(video_path):
        print(f"Error: Could not find video file at {video_path}")
        return

    print("=== Step 1: Transcribing Video ===")
    transcript = transcribe_video(video_path)
    
    if not transcript:
        print("No audio detected or transcription failed. Exiting.")
        return

    playbyplay_segments = None
    if os.path.exists(playbyplay_path):
        with open(playbyplay_path, "r", encoding="utf-8") as handle:
            playbyplay_segments = json.load(handle)

    print("\n=== Step 2: Analyzing LLM Prompt ===")
    
    # Here are some sample prompts you can try:
    sample_prompts = [
        "Show me all the blocks and rejections.",
        "Give me the best dunks and slams.",
        "Show me the assists and nice passes."
    ]
    
    # Pick a sample prompt to run (using index 1: dunks and slams by default)
    user_prompt = sample_prompts[1]
    print(f"User Prompt: '{user_prompt}'")
    
    highlights = get_highlight_timestamps(
        transcript,
        user_prompt,
        playbyplay_segments=playbyplay_segments,
        dry_run=False,
    )
    
    if not highlights:
        print("No matching highlights found by the LLM. Exiting.")
        return
        
    for idx, segment in enumerate(highlights):
        print(f"Highlight {idx + 1}: [{segment['start']}s - {segment['end']}s]")

    print("\n=== Step 3: Rendering Highlight Reel ===")
    base_name = os.path.basename(video_path)
    output_path = os.path.join("assets", f"highlights_{base_name}")
    
    create_highlight_reel(
        input_video=video_path,
        timestamps=highlights,
        output_video=output_path,
        dry_run=False
    )
    print(f"\nSuccess! Custom highlight reel saved to {output_path}")

if __name__ == "__main__":
    main()
