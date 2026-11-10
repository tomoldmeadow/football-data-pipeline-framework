from src.transformation.event_details_transformer import (
    transform_carry_events,
    transform_duel_events,
    transform_foul_events,
    transform_pass_events,
    transform_shot_events,
)


def event(event_type, **details):
    return {"id": f"id-{event_type}", "type": {"name": event_type}, **details}


def test_only_matching_event_types_are_returned():
    events = [event("Pass", **{"pass": {}}), event("Carry", carry={})]

    assert len(transform_pass_events(events)) == 1
    assert len(transform_carry_events(events)) == 1


def test_completed_pass_has_no_outcome():
    events = [event("Pass", **{"pass": {"length": 10.0}})]

    row = transform_pass_events(events).iloc[0]

    assert bool(row["is_completed"]) is True
    assert row["outcome"] is None


def test_incomplete_pass_and_flags():
    events = [event("Pass", **{"pass": {
        "outcome": {"name": "Incomplete"},
        "goal_assist": True,
        "end_location": [100.0, 40.0],
    }})]

    row = transform_pass_events(events).iloc[0]

    assert bool(row["is_completed"]) is False
    assert bool(row["goal_assist"]) is True
    assert bool(row["cross"]) is False
    assert row["end_x"] == 100.0


def test_shot_extracts_xg_and_outcome():
    events = [event("Shot", shot={
        "statsbomb_xg": 0.25,
        "outcome": {"name": "Goal"},
        "end_location": [120.0, 34.6, 1.2],
    })]

    row = transform_shot_events(events).iloc[0]

    assert row["xg"] == 0.25
    assert row["outcome"] == "Goal"
    assert row["end_x"] == 120.0


def test_missing_detail_block_does_not_crash():
    events = [event("Duel"), event("Foul Committed")]

    duel = transform_duel_events(events).iloc[0]
    foul = transform_foul_events(events).iloc[0]

    assert duel["duel_type"] is None
    assert bool(foul["penalty"]) is False


def test_no_matching_events_gives_empty_frame():
    assert transform_pass_events([event("Carry", carry={})]).empty
