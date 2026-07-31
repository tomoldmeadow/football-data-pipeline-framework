import pandas as pd


def transform_events(events_data, match_id):

    rows = []

    for event in events_data:

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

            "possession_team": (
                event.get("possession_team", {})
                    .get("name")
            ),

            "play_pattern": (
                event.get("play_pattern", {})
                    .get("name")
            ),

            "team": (
                event.get("team", {})
                    .get("name")
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

            "location_x": (
                event.get("location", [None, None])[0]
            ),

            "location_y": (
                event.get("location", [None, None])[1]
            )
        })

    return pd.DataFrame(rows)
