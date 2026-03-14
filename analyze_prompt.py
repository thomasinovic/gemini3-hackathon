"""
Feature: Prompt Analysis Engine

This module is responsible for analyzing the user's natural language request 
(e.g., "Show me Steph Curry's three-pointers") against the generated NBA match transcript.
It uses an LLM to identify the relevant events and returns their precise timestamps.

Use Cases:
1. Semantic Search: Find specific events in a 2-hour game based on spoken commentary.
2. Highlight Extraction: Convert text-based events into video timeline boundaries (start/end).
"""

import json
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
try:
    import config
except ImportError:
    class config:
        GEMINI_API_KEY = "demo"
        GEMINI_MODEL_NAME = "gemini-2.5-flash"


def _normalize_transcript(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for index, segment in enumerate(transcript):
        text = segment.get("text") or segment.get("sentence") or ""
        if text is None:
            text = ""
        start = segment.get("start")
        end = segment.get("end")
        duration = segment.get("duration")

        if start is None:
            continue
        if end is None and duration is not None:
            end = start + duration
        if end is None:
            next_segment = transcript[index + 1] if index + 1 < len(transcript) else None
            next_start = next_segment.get("start") if isinstance(next_segment, dict) else None
            if next_start is not None:
                end = next_start
        if end is None:
            continue

        normalized.append({
            "text": str(text),
            "start": float(start),
            "end": float(end)
        })

    return normalized


def _build_prompt(transcript: list[dict[str, Any]], user_prompt: str, stats_data: dict | None) -> str:
    payload = {
        "user_prompt": user_prompt,
        "stats_data": stats_data or {},
        "transcript_segments": transcript,
        "output_schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "reason": {"type": "string"}
                },
                "required": ["start", "end"]
            }
        }
    }

    return (
        "You are an NBA highlight extractor.\n"
        "Given a user request, match it to transcript segments.\n"
        "Return ONLY a valid JSON array that matches the output_schema.\n"
        "Use exact timestamps from transcript_segments; if you need a span, use the earliest matching start and latest matching end.\n"
        "Do not include any extra text outside JSON.\n\n"
        f"INPUT_JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def _parse_gemini_response(raw_text: str) -> list[dict[str, Any]]:
    data = json.loads(raw_text)
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        start = item.get("start")
        end = item.get("end")
        if start is None or end is None:
            continue
        results.append({"start": float(start), "end": float(end)})
    return results

def get_highlight_timestamps(
    transcript: list,
    user_prompt: str,
    stats_data: dict | None = None,
    dry_run: bool = False
) -> list:
    """
    Analyzes the transcript according to the user prompt to find matching highlight timestamps.
    
    Args:
        transcript (list): List of dictionaries containing 'text', 'start', and 'duration' or 'end'.
        user_prompt (str): The natural language request from the user.
        stats_data (dict | None): Optional structured stats to help disambiguate players/events.
        dry_run (bool): If True, returns mock timestamps without calling the LLM.
        
    Returns:
        list: A list of dictionaries containing 'start' and 'end' keys in seconds.
    """
    if dry_run:
        print(f"[TEST MODE] Simulating LLM analysis for prompt: '{user_prompt}'")
        return [
            {"start": 10.5, "end": 15.0},
            {"start": 45.0, "end": 52.5}
        ]
    
    if genai is None or types is None:
        raise ImportError(
            "Missing google-genai package. Install with: pip install google-genai"
        )

    if not getattr(config, "GEMINI_API_KEY", None):
        raise ValueError("GEMINI_API_KEY is not set in config.py")

    normalized_transcript = _normalize_transcript(transcript)
    if not normalized_transcript:
        return []

    prompt = _build_prompt(normalized_transcript, user_prompt, stats_data)
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=config.GEMINI_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )

    return _parse_gemini_response(response.text)

if __name__ == "__main__":
    print("Testing Prompt Analysis Engine...")
    with open("sample_video_2_transcript.json", "r", encoding="utf-8") as handle:
        transcript = json.load(handle)

    prompt = "Show me the blocks in this clip."
    results = get_highlight_timestamps(transcript, prompt, dry_run=False)
    print("LLM identified timestamps:")
    print(json.dumps(results, indent=2))
