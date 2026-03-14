import os
from dotenv import load_dotenv
from transcribe_voxtral import transcribe_video
from video_editor import create_highlight_reel

def main():
    load_dotenv()
    
    video_path = os.getenv("DEFAULT_TEST_VIDEO_PATH", "sample_video.mp4")
    
    if not os.path.exists(video_path):
        print(f"Error: Could not find video file at {video_path}")
        return

    print("=== Step 1: Transcribing Video ===")
    transcript = transcribe_video(video_path)
    
    if not transcript:
        print("No audio detected or transcription failed. Exiting.")
        return

    print("=== Step 2: Selecting Highlights ===")
    # For demonstration, we'll just take the first 3 segments.
    # Later, you can add an LLM here to analyze the 'text' and pick the best plays!
    highlights = transcript[:3]
    
    for idx, segment in enumerate(highlights):
        print(f"Clip {idx + 1}: [{segment['start']}s - {segment['end']}s] -> {segment['text']}")

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
