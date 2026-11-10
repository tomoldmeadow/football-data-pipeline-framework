import pandas as pd


def clock_to_seconds(clock):
    """Convert a StatsBomb "mm:ss" match clock to seconds.

    The clock runs continuously across periods (the second half starts
    at 45:00), so values can be subtracted to get time on the pitch.
    Returns None for missing or malformed values.
    """

    if not isinstance(clock, str):
        return None

    parts = clock.split(":")

    try:
        minutes, seconds = int(parts[0]), int(parts[1])

    except (ValueError, IndexError):
        return None

    return minutes * 60 + seconds


def transform_lineups(lineups_data, match_id):
    """Turn one match's lineup JSON into two DataFrames.

    Returns (lineups, positions):
    - lineups: one row per squad player (including unused substitutes).
    - positions: one row per spell a player spent in a position. These
      are the reliable source for minutes played. Spells that end before
      they start are flagged with is_valid = False.
    """

    lineup_rows = []
    position_rows = []

    for team in lineups_data:

        team_id = team.get("team_id")
        team_name = team.get("team_name")

        for player in team.get("lineup", []):

            player_id = player.get("player_id")

            lineup_rows.append({
                "match_id": match_id,
                "team_id": team_id,
                "team": team_name,
                "player_id": player_id,
                "player_name": player.get("player_name"),
                "player_nickname": player.get("player_nickname"),
                "jersey_number": player.get("jersey_number"),
                "country": (player.get("country") or {}).get("name"),
            })

            for position in player.get("positions", []):

                from_seconds = clock_to_seconds(position.get("from"))
                to_seconds = clock_to_seconds(position.get("to"))

                # Some source spells end before they start (a spurious
                # "Tactical Shift" row on substitutes). Keep the row but
                # flag it so Gold can exclude it from minutes played.
                is_valid = (
                    from_seconds is not None
                    and (to_seconds is None or to_seconds >= from_seconds)
                )

                position_rows.append({
                    "match_id": match_id,
                    "team_id": team_id,
                    "player_id": player_id,
                    "position_id": position.get("position_id"),
                    "position": position.get("position"),
                    "from_seconds": from_seconds,
                    "to_seconds": to_seconds,
                    "is_valid": is_valid,
                    "from_period": position.get("from_period"),
                    "to_period": position.get("to_period"),
                    "start_reason": position.get("start_reason"),
                    "end_reason": position.get("end_reason"),
                })

    return pd.DataFrame(lineup_rows), pd.DataFrame(position_rows)
