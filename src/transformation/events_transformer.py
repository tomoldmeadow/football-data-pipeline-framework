import pandas as pd


def transform_events(events_data):

    rows = []

    for event in events_data:

        rows.append({
            "event_id": event.get("id"),
            "match_id": event.get("match_id"),
            "minute": event.get("minute"),
            "second": event.get("second"),

            "event_type": (
                event.get("type", {})
                .get("name")
            ),

            "player": (
                event.get("player", {})
                .get("name")
            ),

            "team": (
                event.get("team", {})
                .get("name")
            ),

            "possession": event.get("possession")
        })

    return pd.DataFrame(rows)
