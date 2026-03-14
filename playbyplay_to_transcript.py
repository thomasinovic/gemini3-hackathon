import argparse
import json
from pathlib import Path
from typing import Any


def _parse_clock(clock_value: str) -> float | None:
    if not clock_value:
        return None
    if clock_value.startswith("PT") and clock_value.endswith("S"):
        minutes = 0.0
        seconds = 0.0
        payload = clock_value[2:-1]
        if "M" in payload:
            minutes_part, seconds_part = payload.split("M", 1)
            minutes = float(minutes_part) if minutes_part else 0.0
            seconds = float(seconds_part) if seconds_part else 0.0
        else:
            seconds = float(payload)
        return minutes * 60 + seconds
    if ":" in clock_value:
        minutes_str, seconds_str = clock_value.split(":", 1)
        return float(minutes_str) * 60 + float(seconds_str)
    return None


def _period_length(period: int) -> int:
    return 720 if period <= 4 else 300


def _action_text(action: dict[str, Any]) -> str:
    for key in ("description", "actionType", "subType", "shotResult", "qualifiers"):
        value = action.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def playbyplay_to_transcript(payload: dict[str, Any], default_duration: float = 2.0) -> list[dict[str, Any]]:
    actions = payload.get("game", {}).get("actions", [])
    transcript = []
    for action in actions:
        period = action.get("period")
        clock_value = action.get("clock") or action.get("clockTime")
        remaining = _parse_clock(clock_value) if isinstance(clock_value, str) else None
        if period is None or remaining is None:
            continue
        length = _period_length(int(period))
        elapsed = (int(period) - 1) * length + (length - remaining)
        text = _action_text(action)
        if not text:
            continue
        transcript.append(
            {
                "text": text,
                "start": float(elapsed),
                "end": float(elapsed + default_duration),
            }
        )
    return transcript


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert NBA play-by-play JSON to transcript-style segments."
    )
    parser.add_argument(
        "--input",
        default="data_nba/playbyplay_0042300405.json",
        help="Input play-by-play JSON file.",
    )
    parser.add_argument(
        "--output",
        default="data_nba/playbyplay_0042300405_transcript.json",
        help="Output transcript JSON file.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=2.0,
        help="Default segment duration in seconds.",
    )
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    transcript = playbyplay_to_transcript(payload, default_duration=args.duration)
    Path(args.output).write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    print(f"Saved transcript to {args.output} with {len(transcript)} segments")


if __name__ == "__main__":
    main()
