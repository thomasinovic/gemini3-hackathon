import gradio as gr
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from transcribe_voxtral import transcribe_video
from analyze_prompt import get_highlight_timestamps
from download_playbyplay import fetch_cdn_playbyplay, save_json
from game_id_lookup import lookup_game_id
from playbyplay_to_transcript import playbyplay_to_transcript
from video_editor import create_highlight_reel

def find_game(game_date, team_a, team_b, season):
    load_dotenv()
    if not game_date or not team_a or not team_b:
        return None, "Please provide date and both teams.", gr.update(interactive=False)

    try:
        try:
            game_id = lookup_game_id(game_date, team_a, team_b, season=season or None)
        except TypeError:
            game_id = lookup_game_id(game_date, team_a, team_b)
    except TimeoutError:
        return None, "Error: NBA stats lookup timed out. Please try again.", gr.update(interactive=False)
    except ValueError as exc:
        return None, f"Error: {exc}", gr.update(interactive=False)

    data_dir = Path("data_nba")
    data_dir.mkdir(parents=True, exist_ok=True)
    playbyplay_json_path = data_dir / f"playbyplay_{game_id}.json"
    playbyplay_transcript_path = data_dir / f"playbyplay_{game_id}_transcript.json"

    if playbyplay_transcript_path.exists():
        with open(playbyplay_transcript_path, "r", encoding="utf-8") as handle:
            playbyplay_segments = json.load(handle)
    else:
        payload = fetch_cdn_playbyplay(game_id)
        save_json(payload, playbyplay_json_path)
        playbyplay_segments = playbyplay_to_transcript(payload)
        with open(playbyplay_transcript_path, "w", encoding="utf-8") as handle:
            json.dump(playbyplay_segments, handle, ensure_ascii=False, indent=2)

    season_label = f" (season {season})" if season else ""
    return (
        playbyplay_segments,
        f"Game found: {game_id}{season_label}. Play-by-play ready.",
        gr.update(interactive=True),
    )


def generate_highlights(prompt, video_file, video_path_input, playbyplay_segments):
    load_dotenv()

    video_path = None
    if video_path_input:
        video_path = video_path_input
    elif isinstance(video_file, dict):
        video_path = video_file.get("path") or video_file.get("name")
    elif isinstance(video_file, str):
        video_path = video_file

    if not video_path:
        video_path = os.getenv("DEFAULT_TEST_VIDEO_PATH", "sample_video.mp4")

    if not os.path.exists(video_path):
        return None, f"Error: Could not find video file at {video_path}"

    print("=== Step 1: Transcribing Video ===")
    os.makedirs("assets/transcripts", exist_ok=True)
    transcript_path = os.path.join(
        "assets/transcripts",
        f"{os.path.splitext(os.path.basename(video_path))[0]}_transcript.json",
    )
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as handle:
            transcript = json.load(handle)
        print(f"Loaded cached transcript: {transcript_path}")
    else:
        transcript = transcribe_video(video_path)
        if transcript:
            with open(transcript_path, "w", encoding="utf-8") as handle:
                json.dump(transcript, handle, ensure_ascii=False, indent=2)
            print(f"Saved transcript: {transcript_path}")

    if not transcript:
        return None, "No audio detected or transcription failed."

    print(f"\n=== Step 2: Analyzing LLM Prompt ===\nUser Prompt: '{prompt}'")

    highlights = get_highlight_timestamps(
        transcript,
        prompt,
        playbyplay_segments=playbyplay_segments,
        dry_run=False,
    )

    if not highlights:
        return None, "No matching highlights found by the LLM."

    print("\n=== Step 3: Rendering Highlight Reel ===")
    base_name = os.path.basename(video_path)
    os.makedirs("assets", exist_ok=True)
    output_path = os.path.join("assets", f"gradio_highlights_{base_name}")

    create_highlight_reel(
        input_video=video_path,
        timestamps=highlights,
        output_video=output_path,
        dry_run=False,
    )

    return output_path, f"Success! Custom highlight reel saved."

with gr.Blocks(title="AI Video Highlight Editor") as app:
    gr.Markdown("# AI Video Highlight Editor")
    gr.Markdown("Upload a video, provide match info, and extract highlights from commentary.")

    playbyplay_state = gr.State(None)
    
    with gr.Row():
        with gr.Column():
            game_date_input = gr.Textbox(
                label="Game Date (YYYY-MM-DD)",
                placeholder="2024-06-17",
                lines=1,
            )
            season_input = gr.Textbox(
                label="Season (optional)",
                placeholder="2023-24",
                lines=1,
            )
            team_a_input = gr.Textbox(
                label="Team A",
                placeholder="Dallas Mavericks",
                lines=1,
            )
            team_b_input = gr.Textbox(
                label="Team B",
                placeholder="Boston Celtics",
                lines=1,
            )
            find_game_btn = gr.Button("Find Game", variant="secondary")
            find_status = gr.Textbox(label="Game Lookup", interactive=False)
            video_path_input = gr.Textbox(
                label="Video Path (no upload)",
                placeholder="sample_video.mp4",
                lines=1,
            )
            video_input = gr.File(
                label="Video Upload (optional)",
                file_types=["video"],
                type="filepath",
                interactive=False,
            )
            prompt_input = gr.Textbox(
                label="Prompt", 
                placeholder="Show me all the blocks and rejections.", 
                lines=2
            )
            video_path_input = gr.Textbox(
                label="Video Path",
                placeholder="Path to your video file.",
                lines=1
            )
            voice_prompt_input = gr.Audio(
                label="Voice Prompt (Overrides Text Prompt)",
                type="filepath",
                sources=["microphone", "upload"]
            )
            submit_btn = gr.Button("Generate Highlights", variant="primary")
            
        with gr.Column():
            video_output = gr.Video(label="Result Reel")
            status_output = gr.Textbox(label="Status", interactive=False)
            
    submit_btn.click(
        fn=generate_highlights,
        inputs=[prompt_input, video_input, video_path_input, playbyplay_state],
        outputs=[video_output, status_output]
    )

    find_game_btn.click(
        fn=find_game,
        inputs=[game_date_input, team_a_input, team_b_input, season_input],
        outputs=[playbyplay_state, find_status, video_input],
    )

if __name__ == "__main__":
    app.launch(server_name="localhost", server_port=7860, share=True)
