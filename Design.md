# App Design and Feature Documentation

This document maintains descriptions of all features implemented in the **NBA Custom Highlights Generator**.

## Architecture Overview
The system is designed as a modular pipeline:
1. **Data Ingestion & Perception**: Parsing full match videos and extracting text/timestamps.
2. **Reasoning**: LLM-based filtering based on user prompts.
3. **Execution**: Video slicing and rendering.

---

## 1. Centralized Configuration (`config.py`)
- **Description**: Contains all configurable parameters for the NBA Highlights Generator, including API keys, file paths, and model settings.
- **Key Features**:
  - Centralized management of API keys for YouTube and Mistral.
  - Configurable file paths for input videos and output transcripts.
  - Settings for model parameters, including temperature and max tokens for the LLM.
- **Usage**: Imported as a module in other scripts to access configuration settings.

## 2. Voxtral / Mistral API Transcription (`transcribe_voxtral.py`)
- **Description**: Handles remote transcription of local full-match NBA videos via the Mistral API, yielding timestamped subtitle segments.
- **Use Cases**:
  - Transcribe arbitrary standard video files (e.g., downloaded NBA matches) to create a searchable text index of the game.
  - Rely on Mistral's language models for high-quality sports commentary recognition.
- **Testing Strategy**: Uses a `dry_run` flag to bypass the API call, returning a static mock transcript to ensure downstream timeline/editing data pipelines can be tested without spending API credits.

---

## Future Modules (To Be Implemented)

### 3. Prompt Analysis Engine
- **Description**: Uses an LLM to read the generated transcript and the user's prompt to output target timestamps (e.g., `[{"start": 120, "end": 135}, ...]`).

### 4. Video Sub-clipper
- **Description**: Takes the list of timestamps from the Analysis Engine and uses `ffmpeg` to extract and concatenate the corresponding video chunks into the final highlight reel.