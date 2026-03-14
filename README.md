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

## Download 2024 Finals Game 5 Play-by-Play
This downloads the play-by-play JSON for **Dallas Mavericks vs Boston Celtics, Game 5 (June 17, 2024)**.

```bash
python3 download_playbyplay.py --game-id 0042300405
```

Output file:
- `data_nba/playbyplay_0042300405.json`

## Convert Play-by-Play to Transcript Segments
Generate transcript-like segments from the play-by-play file (for prompt analysis).

```bash
python3 playbyplay_to_transcript.py \
	--input data_nba/playbyplay_0042300405.json \
	--output data_nba/playbyplay_0042300405_transcript.json
```

## Use Audio + Play-by-Play Together
The analysis step can combine the audio transcript with structured play-by-play segments.

Set the path to the play-by-play transcript (optional):

```bash
export PLAYBYPLAY_TRANSCRIPT_PATH="data_nba/playbyplay_0042300405_transcript.json"
```

Then run either pipeline:

```bash
python3 main.py
```

## Gradio App: Upload Video + Game Info
The app can now resolve the NBA `gameId` from a date + two teams, fetch play-by-play,
and reuse cached transcripts if they already exist.

1. Upload your video.
2. Provide the game date (YYYY-MM-DD).
3. Provide the two teams (full name or tricode).
4. Enter a highlight prompt.

Transcript caching:
- Audio transcripts are saved to `assets/transcripts/<video_name>_transcript.json`.
- Play-by-play transcripts are saved to `data_nba/playbyplay_<gameId>_transcript.json`.
