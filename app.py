import base64
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

    loading_html = (
        "<div class='status-row'>"
        "<div class='ball-spinner'></div>"
        "<span>Generating highlights...</span>"
        "</div>"
    )
    yield None, loading_html

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
        yield None, f"<span class='status-error'>Error: Could not find video file at {video_path}</span>"
        return

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
        yield None, "<span class='status-error'>No audio detected or transcription failed.</span>"
        return

    print(f"\n=== Step 2: Analyzing LLM Prompt ===\nUser Prompt: '{prompt}'")

    highlights = get_highlight_timestamps(
        transcript,
        prompt,
        playbyplay_segments=playbyplay_segments,
        dry_run=False,
    )

    if not highlights:
        yield None, "<span class='status-warn'>No matching highlights found by the LLM.</span>"
        return

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

    yield output_path, "<span class='status-ok'>Success! Custom highlight reel saved.</span>"

LOGO_PATH = "assets/logo_basket.jpg"
BANNER_PATH = "assets/NBA.Com-National-Basketball-Association-3252384836.png"


def _logo_data_url(path: str, mime_type: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


LOGO_DATA_URL = _logo_data_url(LOGO_PATH, "image/jpeg")
BANNER_DATA_URL = _logo_data_url(BANNER_PATH, "image/png")

CUSTOM_CSS = """
:root {
    --nba-blue: #1d428a;
    --nba-red: #c8102e;
    --nba-orange: #f97316;
    --nba-slate: #0f172a;
    --nba-ice: #f8fafc;
    --nba-text: #0f172a;
    --nba-muted: #475569;
    --nba-card: #ffffff;
    --nba-border: #e2e8f0;
}
body, .gradio-container {background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); color: var(--nba-text);}
.gradio-container {position: relative;}
.gradio-container::before {
    content: "";
    position: fixed;
    inset: 0;
    background: url('__BANNER_URL__') center/70% no-repeat;
    opacity: 0.08;
    pointer-events: none;
    z-index: 0;
}
.gradio-container > * {position: relative; z-index: 1;}
.app-header {display:flex;align-items:center;gap:16px;padding:8px 0;}
.app-title {font-size:28px;font-weight:800;color:var(--nba-blue);letter-spacing:0.2px;}
.app-subtitle {color:var(--nba-muted);margin-top:4px;}
.card {border:1px solid var(--nba-border);border-radius:12px;padding:12px;background:var(--nba-card);}
.status-row {display:flex;align-items:center;gap:10px;font-weight:600;color:var(--nba-text);}
.status-ok {color:#16a34a;font-weight:600;}
.status-warn {color:#f59e0b;font-weight:600;}
.status-error {color:#dc2626;font-weight:600;}
.ball-spinner {width:22px;height:22px;border-radius:50%;background:var(--nba-orange);position:relative;animation:spin 1s linear infinite;box-shadow:inset 0 0 0 3px var(--nba-slate);}
.ball-spinner:before,.ball-spinner:after {content:'';position:absolute;left:50%;top:0;bottom:0;width:2px;background:var(--nba-slate);transform:translateX(-50%);} 
.ball-spinner:after {left:0;right:0;top:50%;height:2px;width:100%;transform:translateY(-50%);} 
button.primary {background: var(--nba-blue) !important;border-color: var(--nba-blue) !important;color: white !important;}
button.secondary {background: white !important;border-color: var(--nba-red) !important;color: var(--nba-red) !important;}
button.primary:hover {background: #16356f !important;}
button.secondary:hover {background: #fff1f2 !important;}
.gr-textbox textarea, .gr-textbox input {border-radius:10px;border-color: var(--nba-border);background:#ffffff;color:var(--nba-text);}
.gr-form, .gr-panel, .gr-box, .gr-group, .gr-block {background: var(--nba-card);border-radius:14px;border:1px solid var(--nba-border);}
.gr-block {box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);}
.gr-markdown, label, .gr-textbox label {color: var(--nba-text) !important;}
@keyframes spin {to {transform:rotate(360deg);}}
"""
CUSTOM_CSS = CUSTOM_CSS.replace("__BANNER_URL__", BANNER_DATA_URL or "")

with gr.Blocks(title="AI Video Highlight Editor") as app:
    logo_src = LOGO_DATA_URL or ""
    logo_html = (
        f"<img src='{logo_src}' width='56' height='56'/>" if logo_src else ""
    )
    gr.HTML(
        f"<div class='app-header'>"
        f"{logo_html}"
        f"<div><div class='app-title'>AI Video Highlight Editor</div>"
        f"<div class='app-subtitle'>Upload a video, provide match info, and extract highlights from commentary.</div>"
        f"</div></div>"
    )

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
            status_output = gr.HTML(label="Status")
            highlight_image_src = _logo_data_url("assets/wp1916190-4025962750.jpg", "image/jpeg") or ""
            if highlight_image_src:
                gr.HTML(
                    f"<div style='margin-top:16px;'>"
                    f"<img src='{highlight_image_src}' style='width:100%;max-width:680px;border-radius:12px;'/>"
                    f"</div>"
                )
            
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
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
