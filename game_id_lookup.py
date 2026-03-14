import argparse
import json
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
SCOREBOARD_URL = "https://stats.nba.com/stats/scoreboardv2"

TEAM_TRICODES = {
    "atl": "ATL",
    "hawks": "ATL",
    "boston": "BOS",
    "celtics": "BOS",
    "brooklyn": "BKN",
    "nets": "BKN",
    "charlotte": "CHA",
    "hornets": "CHA",
    "chicago": "CHI",
    "bulls": "CHI",
    "cleveland": "CLE",
    "cavaliers": "CLE",
    "cleveland cavaliers": "CLE",
    "dallas": "DAL",
    "mavericks": "DAL",
    "dallas mavericks": "DAL",
    "denver": "DEN",
    "nuggets": "DEN",
    "detroit": "DET",
    "pistons": "DET",
    "golden state": "GSW",
    "warriors": "GSW",
    "houston": "HOU",
    "rockets": "HOU",
    "indiana": "IND",
    "pacers": "IND",
    "la clippers": "LAC",
    "clippers": "LAC",
    "la lakers": "LAL",
    "lakers": "LAL",
    "memphis": "MEM",
    "grizzlies": "MEM",
    "miami": "MIA",
    "heat": "MIA",
    "milwaukee": "MIL",
    "bucks": "MIL",
    "minnesota": "MIN",
    "timberwolves": "MIN",
    "new orleans": "NOP",
    "pelicans": "NOP",
    "new york": "NYK",
    "knicks": "NYK",
    "oklahoma city": "OKC",
    "thunder": "OKC",
    "orlando": "ORL",
    "magic": "ORL",
    "philadelphia": "PHI",
    "sixers": "PHI",
    "76ers": "PHI",
    "phoenix": "PHX",
    "suns": "PHX",
    "portland": "POR",
    "trail blazers": "POR",
    "sacramento": "SAC",
    "kings": "SAC",
    "san antonio": "SAS",
    "spurs": "SAS",
    "toronto": "TOR",
    "raptors": "TOR",
    "utah": "UTA",
    "jazz": "UTA",
    "washington": "WAS",
    "wizards": "WAS",
}


def normalize_team_input(team: str) -> str:
    if not team:
        raise ValueError("Team name is required.")
    cleaned = team.strip().lower()
    if cleaned.upper() in TEAM_TRICODES.values():
        return cleaned.upper()
    if cleaned in TEAM_TRICODES:
        return TEAM_TRICODES[cleaned]
    raise ValueError(f"Unknown team input: {team}")


def normalize_date(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()


def season_from_date(date_str: str) -> str:
    date_value = datetime.strptime(date_str, "%Y-%m-%d").date()
    season_start = date_value.year if date_value.month >= 10 else date_value.year - 1
    season_end = str(season_start + 1)[2:]
    return f"{season_start}-{season_end}"


def fetch_schedule() -> dict[str, Any]:
    request = Request(
        SCHEDULE_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def _fetch_scoreboard(game_date: str, timeout_seconds: int = 15) -> dict[str, Any]:
    params = {
        "GameDate": datetime.strptime(game_date, "%Y-%m-%d").strftime("%m/%d/%Y"),
        "LeagueID": "00",
        "DayOffset": "0",
    }
    url = f"{SCOREBOARD_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://www.nba.com",
            "Referer": "https://www.nba.com/",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def _lookup_from_schedule(game_date: str, team_a: str, team_b: str) -> str:
    normalized_date = normalize_date(game_date)
    team_a_tricode = normalize_team_input(team_a)
    team_b_tricode = normalize_team_input(team_b)

    schedule = fetch_schedule()
    game_dates = schedule.get("leagueSchedule", {}).get("gameDates", [])
    for date_entry in game_dates:
        date_value = date_entry.get("gameDate")
        if not date_value:
            continue
        if not date_value.startswith(normalized_date):
            continue
        for game in date_entry.get("games", []):
            home_team = game.get("homeTeam") or {}
            away_team = game.get("awayTeam") or {}
            home = home_team.get("teamTricode")
            away = away_team.get("teamTricode")
            home = home.upper() if isinstance(home, str) else None
            away = away.upper() if isinstance(away, str) else None
            teams = {home, away}
            if team_a_tricode in teams and team_b_tricode in teams:
                game_id = game.get("gameId")
                if game_id:
                    return str(game_id)
    raise ValueError(
        f"No game found for {normalized_date} with {team_a_tricode} vs {team_b_tricode}."
    )


def _lookup_from_nba_api(game_date: str, team_a: str, team_b: str) -> str | None:
    try:
        from nba_api.stats.endpoints import scoreboardv2
    except Exception:
        return None

    normalized_date = normalize_date(game_date)
    team_a_tricode = normalize_team_input(team_a)
    team_b_tricode = normalize_team_input(team_b)
    scoreboard = scoreboardv2.ScoreboardV2(game_date=normalized_date)
    games_df = scoreboard.get_data_frames()[0]
    for _, row in games_df.iterrows():
        game_code = row.get("GAMECODE") or ""
        if team_a_tricode in game_code and team_b_tricode in game_code:
            game_id = row.get("GAME_ID")
            if game_id:
                return str(game_id)
    return None


def _lookup_from_nba_api_season(
    game_date: str,
    team_a: str,
    team_b: str,
    season: str,
) -> str | None:
    try:
        from nba_api.stats.endpoints import leaguegamefinder
    except Exception:
        return None

    normalized_date = normalize_date(game_date)
    team_a_tricode = normalize_team_input(team_a)
    team_b_tricode = normalize_team_input(team_b)

    finder = leaguegamefinder.LeagueGameFinder(season_nullable=season)
    games_df = finder.get_data_frames()[0]
    date_matches = games_df[games_df["GAME_DATE"] == normalized_date]
    if date_matches.empty:
        return None

    matchup_mask = (
        date_matches["MATCHUP"].str.contains(team_a_tricode)
        & date_matches["MATCHUP"].str.contains(team_b_tricode)
    )
    matchup_rows = date_matches[matchup_mask]
    if matchup_rows.empty:
        return None

    game_id = matchup_rows["GAME_ID"].iloc[0]
    return str(game_id) if game_id else None


def _lookup_from_scoreboard(game_date: str, team_a: str, team_b: str) -> str | None:
    team_a_tricode = normalize_team_input(team_a)
    team_b_tricode = normalize_team_input(team_b)
    payload = None
    for attempt in (1, 2):
        try:
            payload = _fetch_scoreboard(game_date, timeout_seconds=15)
            break
        except TimeoutError:
            if attempt == 2:
                return None
    result_sets = payload.get("resultSets", [])
    header = None
    rows = []
    for result in result_sets:
        if result.get("name") == "GameHeader":
            header = result.get("headers", [])
            rows = result.get("rowSet", [])
            break
    if not header:
        return None
    idx = {name: i for i, name in enumerate(header)}
    for row in rows:
        home = row[idx.get("HOME_TEAM_ABBREVIATION")]
        away = row[idx.get("VISITOR_TEAM_ABBREVIATION")]
        teams = {home, away}
        if team_a_tricode in teams and team_b_tricode in teams:
            game_id = row[idx.get("GAME_ID")]
            if game_id:
                return str(game_id)
    return None


def lookup_game_id(game_date: str, team_a: str, team_b: str, season: str | None = None) -> str:
    season_value = season or season_from_date(game_date)
    game_id = _lookup_from_nba_api_season(game_date, team_a, team_b, season_value)
    if game_id:
        return game_id

    game_id = _lookup_from_nba_api(game_date, team_a, team_b)
    if game_id:
        return game_id
    game_id = _lookup_from_scoreboard(game_date, team_a, team_b)
    if game_id:
        return game_id
    return _lookup_from_schedule(game_date, team_a, team_b)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lookup NBA gameId by date and teams.")
    parser.add_argument("--date", required=True, help="Game date YYYY-MM-DD")
    parser.add_argument("--team-a", required=True, help="Team A name or tricode")
    parser.add_argument("--team-b", required=True, help="Team B name or tricode")
    parser.add_argument(
        "--season",
        default=None,
        help="Season string like 2024-25 (optional).",
    )
    args = parser.parse_args()

    game_id = lookup_game_id(args.date, args.team_a, args.team_b, season=args.season)
    print(game_id)


if __name__ == "__main__":
    main()
