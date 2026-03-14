import gradio as gr
import os
from dotenv import load_dotenv
from transcribe_voxtral import transcribe_video
from analyze_prompt import get_highlight_timestamps
from video_editor import create_highlight_reel

def generate_highlights(prompt, video_path, voice_prompt):
    load_dotenv()
    
    video_path = video_path or os.getenv("DEFAULT_TEST_VIDEO_PATH", "sample_video.mp4")

    if not os.path.exists(video_path):
        return None, f"Error: Could not find video file at {video_path}"

    print("=== Step 1: Transcribing Video ===")
    match_transcript = transcribe_video(video_path)
    
    if not match_transcript:
        return None, "No audio detected or transcription failed."

    # If a voice prompt is provided, save it to assets and transcribe
    if voice_prompt:
        import shutil
        os.makedirs("assets", exist_ok=True)
        # voice_prompt is a filepath string because type="filepath" in gr.File
        voice_prompt_path = os.path.join("assets", os.path.basename(voice_prompt))
        shutil.copy2(voice_prompt, voice_prompt_path)
        
        prompt_transcript = transcribe_video(voice_prompt_path)
        
        # Combine the transcribed voice segments into a single prompt string
        user_prompt = " ".join([seg['text'] for seg in prompt_transcript]).strip()
        print(f"🗣️ Detected Voice Prompt: '{user_prompt}'")
        
        highlights = get_highlight_timestamps(match_transcript, user_prompt, dry_run=False)
    else:
        print(f"\n=== Step 2: Analyzing LLM Prompt ===\nUser Prompt: '{prompt}'")
        
        highlights = get_highlight_timestamps(match_transcript, prompt, dry_run=False)
    
    if not highlights:
        return None, "No matching highlights found by the LLM."
        
    print("\n=== Step 3: Rendering Highlight Reel ===")
    base_name = os.path.basename(video_path)
    # Ensure assets directory exists
    os.makedirs("assets", exist_ok=True)
    output_path = os.path.join("assets", f"gradio_highlights_{base_name}")
    
    create_highlight_reel(
        input_video=video_path,
        timestamps=highlights,
        output_video=output_path,
        dry_run=False
    )
    
    return output_path, f"Success! Custom highlight reel saved."

with gr.Blocks(title="AI Video Highlight Editor") as app:
    gr.Markdown("# AI Video Highlight Editor")
    gr.Markdown("Enter a prompt to automatically extract and stitch the most relevant segments from the default video.")
    
    with gr.Row():
        with gr.Column():
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
        inputs=[prompt_input, video_path_input, voice_prompt_input],
        outputs=[video_output, status_output]
    )

if __name__ == "__main__":
    app.launch(server_name="localhost", server_port=7860, share=True)
