import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


def fetch_cdn_playbyplay(game_id: str) -> dict:
    url = f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def save_json(payload: dict, output_path: Path | str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download NBA play-by-play JSON from the NBA CDN."
    )
    parser.add_argument(
        "--game-id",
        default="0042300405",
        help="NBA GameID (e.g. 0042300405 for 2024 Finals Game 5)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (default: data_nba/playbyplay_<GAME_ID>.json)",
    )
    args = parser.parse_args()

    output_path = (
        Path(args.output)
        if args.output
        else Path("data_nba") / f"playbyplay_{args.game_id}.json"
    )

    payload = fetch_cdn_playbyplay(args.game_id)
    actions = payload.get("game", {}).get("actions", [])
    if not isinstance(actions, list) or not actions:
        raise ValueError("Play-by-play payload is empty or missing actions.")
    last_action = actions[-1] if actions else {}
    print(f"Fetched {len(actions)} actions. Last period: {last_action.get('period')}, clock: {last_action.get('clock')}")
    save_json(payload, output_path)
    print(f"Saved play-by-play to {output_path}")


if __name__ == "__main__":
    main()
