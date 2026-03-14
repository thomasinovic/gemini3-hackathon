# NBA Custom Highlights Generator

## Overview
This project takes a full NBA match video and a natural language user prompt (e.g., "Show me all of Steph Curry's three-pointers" or "Give me the best defensive plays of the 4th quarter") and automatically generates a customized highlight reel.

## Core Workflow
1. **Transcription**: Extract audio from the full match and generate timestamped transcripts using the Mistral API (Voxtral).
2. **Analysis**: Feed the user's prompt and the timestamped transcript into an LLM to identify relevant events and their exact timestamps.
3. **Video Processing**: Use standard video editing libraries (e.g., `ffmpeg` or `moviepy`) to trim and stitch the identified segments into a single cohesive highlight video.

## Project Structure
- `config.py`: Centralized configuration (API keys, default paths, model names).
- `Design.md`: Detailed architectural design and feature documentation.
- `transcribe_voxtral.py`: Module for extracting audio and fetching transcripts via Mistral.
- `analyze_prompt.py`: Module for cross-referencing user prompts with transcripts using an LLM.
- `video_editor.py`: Module for cutting and stitching video segments.

## Setup
1. Install dependencies: `pip install -r requirements.txt` (ffmpeg must also be installed on your system).
2. Add your API keys to `config.py`.
3. Run the scripts directly (most include a `dry_run` test mode).
