import pandas as pd


def split_location(location):
    """Return (x, y) from a StatsBomb location, or (None, None).

    Handles missing, null or malformed values rather than assuming a
    two-element list.
    """

    if (
        isinstance(location, (list, tuple))
        and len(location) >= 2
    ):
        return location[0], location[1]

    return None, None


def transform_events(events_data, match_id):

    rows = []

    for event in events_data:

        location_x, location_y = split_location(event.get("location"))

        rows.append({
            "event_id": event.get("id"),
            "match_id": match_id,
            "index": event.get("index"),
            "period": event.get("period"),
            "timestamp": event.get("timestamp"),
            "minute": event.get("minute"),
            "second": event.get("second"),
            "duration": event.get("duration"),
            "possession": event.get("possession"),

            "possession_team_id": (
                event.get("possession_team", {})
                    .get("id")
            ),

            "possession_team": (
                event.get("possession_team", {})
                    .get("name")
            ),

            "play_pattern": (
                event.get("play_pattern", {})
                    .get("name")
            ),

            "team_id": (
                event.get("team", {})
                    .get("id")
            ),

            "team": (
                event.get("team", {})
                    .get("name")
            ),

            "player_id": (
                event.get("player", {})
                    .get("id")
            ),

            "player": (
                event.get("player", {})
                    .get("name")
            ),

            "position": (
                event.get("position", {})
                    .get("name")
            ),

            "event_type": (
                event.get("type", {})
                    .get("name")
            ),

            "under_pressure": bool(event.get("under_pressure", False)),

            "location_x": location_x,
            "location_y": location_y
        })

    return pd.DataFrame(rows)
