"""Typed Silver tables for individual StatsBomb event types.

Each function takes one match's raw events and returns a DataFrame with
one row per event of that type, keyed on event_id so it joins back to the
central events table. Only a core set of attributes is extracted for each
type. Missing nested values become nulls.
"""

import pandas as pd

from src.transformation.events_transformer import split_location


def _name(obj):
    """Return obj["name"] for a nested StatsBomb object, else None."""

    if isinstance(obj, dict):
        return obj.get("name")

    return None


def _rows_for(events_data, event_type, build_row):

    rows = []

    for event in events_data:

        if _name(event.get("type")) != event_type:
            continue

        row = {"event_id": event.get("id")}
        row.update(build_row(event))
        rows.append(row)

    return rows


def transform_pass_events(events_data):

    def build(event):
        details = event.get("pass") or {}
        end_x, end_y = split_location(details.get("end_location"))
        recipient = details.get("recipient") or {}

        return {
            "recipient_id": recipient.get("id"),
            "recipient": recipient.get("name"),
            "length": details.get("length"),
            "angle": details.get("angle"),
            "height": _name(details.get("height")),
            "end_x": end_x,
            "end_y": end_y,
            "body_part": _name(details.get("body_part")),
            "pass_type": _name(details.get("type")),
            # StatsBomb leaves outcome empty for a completed pass
            "outcome": _name(details.get("outcome")),
            "is_completed": details.get("outcome") is None,
            "cross": bool(details.get("cross", False)),
            "switch": bool(details.get("switch", False)),
            "through_ball": bool(details.get("through_ball", False)),
            "cut_back": bool(details.get("cut_back", False)),
            "shot_assist": bool(details.get("shot_assist", False)),
            "goal_assist": bool(details.get("goal_assist", False)),
        }

    return pd.DataFrame(_rows_for(events_data, "Pass", build))


def transform_shot_events(events_data):

    def build(event):
        details = event.get("shot") or {}
        end_location = details.get("end_location")
        end_x, end_y = split_location(end_location)

        return {
            "xg": details.get("statsbomb_xg"),
            "end_x": end_x,
            "end_y": end_y,
            "outcome": _name(details.get("outcome")),
            "body_part": _name(details.get("body_part")),
            "technique": _name(details.get("technique")),
            "shot_type": _name(details.get("type")),
            "first_time": bool(details.get("first_time", False)),
        }

    return pd.DataFrame(_rows_for(events_data, "Shot", build))


def transform_carry_events(events_data):

    def build(event):
        details = event.get("carry") or {}
        end_x, end_y = split_location(details.get("end_location"))

        return {"end_x": end_x, "end_y": end_y}

    return pd.DataFrame(_rows_for(events_data, "Carry", build))


def transform_dribble_events(events_data):

    def build(event):
        details = event.get("dribble") or {}

        return {
            "outcome": _name(details.get("outcome")),
            "nutmeg": bool(details.get("nutmeg", False)),
            "overrun": bool(details.get("overrun", False)),
        }

    return pd.DataFrame(_rows_for(events_data, "Dribble", build))


def transform_duel_events(events_data):

    def build(event):
        details = event.get("duel") or {}

        return {
            "duel_type": _name(details.get("type")),
            "outcome": _name(details.get("outcome")),
        }

    return pd.DataFrame(_rows_for(events_data, "Duel", build))


def transform_foul_events(events_data):

    def build(event):
        details = event.get("foul_committed") or {}

        return {
            "foul_type": _name(details.get("type")),
            "card": _name(details.get("card")),
            "offensive": bool(details.get("offensive", False)),
            "advantage": bool(details.get("advantage", False)),
            "penalty": bool(details.get("penalty", False)),
        }

    return pd.DataFrame(_rows_for(events_data, "Foul Committed", build))


# Silver table name -> transformer
EVENT_DETAIL_TRANSFORMERS = {
    "pass_events": transform_pass_events,
    "shot_events": transform_shot_events,
    "carry_events": transform_carry_events,
    "dribble_events": transform_dribble_events,
    "duel_events": transform_duel_events,
    "foul_events": transform_foul_events,
}
