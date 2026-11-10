from typing import Annotated, Literal

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from src.api.database import fetch_all, fetch_one, get_db
from src.api.schemas import (
    Event,
    MatchDetail,
    MatchSummary,
    PlayerComparisonEntry,
    PlayerDetail,
    PlayerMatchStats,
    PlayerSummary,
    Team,
    TeamStatistics,
)

app = FastAPI(
    title="Football Data Pipeline API",
    description="Read-only access to the Gold analytics tables.",
    version="0.1.0",
)

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]

Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]

# Columns the players endpoint may be sorted by (whitelist: never
# interpolate user input into SQL)
PLAYER_SORT_COLUMNS = {
    "minutes_played", "appearances", "goals", "assists", "shots",
    "shots_on_target", "xg", "passes", "pass_completion_pct",
    "shot_assists", "progressive_passes", "tackles", "tackles_won",
    "interceptions", "player_name",
}

PER_90_METRICS = [
    "goals", "assists", "shots", "xg", "progressive_passes",
    "tackles", "interceptions",
]


@app.exception_handler(duckdb.CatalogException)
async def missing_table_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Gold tables not found. Run the pipeline first."},
    )


@app.get("/health")
def health(conn: DB):
    matches = fetch_one(conn, "SELECT COUNT(*) AS n FROM silver.matches")

    return {"status": "ok", "matches": matches["n"]}


# ----------------------------------------------------------------------
# Matches
# ----------------------------------------------------------------------

@app.get("/matches", response_model=list[MatchSummary])
def list_matches(
    conn: DB,
    team: str | None = Query(None, description="Home or away team name"),
    limit: Limit = 50,
    offset: Offset = 0,
):
    return fetch_all(
        conn,
        """
        SELECT * FROM gold.match_summary
        WHERE ? IS NULL
           OR home_team ILIKE '%' || ? || '%'
           OR away_team ILIKE '%' || ? || '%'
        ORDER BY match_date, match_id
        LIMIT ? OFFSET ?
        """,
        [team, team, team, limit, offset],
    )


@app.get("/matches/{match_id}", response_model=MatchDetail)
def get_match(match_id: int, conn: DB):
    match = fetch_one(
        conn,
        "SELECT * FROM gold.match_summary WHERE match_id = ?",
        [match_id],
    )

    if match is None:
        raise HTTPException(404, f"Match {match_id} not found")

    match["teams"] = fetch_all(
        conn,
        "SELECT * FROM gold.team_match_stats WHERE match_id = ? ORDER BY team",
        [match_id],
    )

    return match


@app.get("/matches/{match_id}/events", response_model=list[Event])
def get_match_events(
    match_id: int,
    conn: DB,
    event_type: str | None = None,
    team_id: int | None = None,
    player_id: int | None = None,
    period: Annotated[int | None, Query(ge=1, le=5)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    offset: Offset = 0,
):
    exists = fetch_one(
        conn,
        "SELECT 1 AS found FROM silver.matches WHERE match_id = ?",
        [match_id],
    )

    if exists is None:
        raise HTTPException(404, f"Match {match_id} not found")

    return fetch_all(
        conn,
        """
        SELECT event_id, index, period, timestamp, minute, second,
               event_type, team_id, team, player_id, player, position,
               possession, play_pattern, under_pressure,
               location_x, location_y
        FROM silver.events
        WHERE match_id = ?
          AND (? IS NULL OR event_type = ?)
          AND (? IS NULL OR team_id = ?)
          AND (? IS NULL OR player_id = ?)
          AND (? IS NULL OR period = ?)
        ORDER BY index
        LIMIT ? OFFSET ?
        """,
        [match_id, event_type, event_type, team_id, team_id,
         player_id, player_id, period, period, limit, offset],
    )


# ----------------------------------------------------------------------
# Players
# ----------------------------------------------------------------------

@app.get("/players", response_model=list[PlayerSummary])
def list_players(
    conn: DB,
    q: Annotated[str | None, Query(description="Name contains")] = None,
    team: str | None = None,
    min_minutes: Annotated[float, Query(ge=0)] = 0,
    sort_by: str = "minutes_played",
    order: Literal["asc", "desc"] = "desc",
    limit: Limit = 50,
    offset: Offset = 0,
):
    if sort_by not in PLAYER_SORT_COLUMNS:
        raise HTTPException(
            400,
            f"sort_by must be one of {sorted(PLAYER_SORT_COLUMNS)}",
        )

    # sort_by and order are validated above, so safe to interpolate
    return fetch_all(
        conn,
        f"""
        SELECT * FROM gold.player_tournament_stats
        WHERE (? IS NULL OR player_name ILIKE '%' || ? || '%')
          AND (? IS NULL OR team ILIKE '%' || ? || '%')
          AND minutes_played >= ?
        ORDER BY {sort_by} {order} NULLS LAST, player_id
        LIMIT ? OFFSET ?
        """,
        [q, q, team, team, min_minutes, limit, offset],
    )


# Declared before /players/{player_id} so "compare" is not parsed as an ID
@app.get("/players/compare", response_model=list[PlayerComparisonEntry])
def compare_players(
    conn: DB,
    ids: Annotated[list[int], Query(min_length=2, max_length=5)],
):
    placeholders = ", ".join("?" for _ in ids)

    players = fetch_all(
        conn,
        f"""
        SELECT * FROM gold.player_tournament_stats
        WHERE player_id IN ({placeholders})
        """,
        ids,
    )

    found = {p["player_id"] for p in players}
    missing = [i for i in ids if i not in found]

    if missing:
        raise HTTPException(404, f"Players not found: {missing}")

    for player in players:
        minutes = player["minutes_played"]

        player["per_90"] = {
            f"{metric}_per_90": (
                round(player[metric] * 90 / minutes, 3)
                if minutes and minutes > 0 else None
            )
            for metric in PER_90_METRICS
        }

    # Preserve the order the caller asked for
    order = {player_id: i for i, player_id in enumerate(ids)}

    return sorted(players, key=lambda p: order[p["player_id"]])


@app.get("/players/{player_id}", response_model=PlayerDetail)
def get_player(player_id: int, conn: DB):
    player = fetch_one(
        conn,
        """
        SELECT s.*, d.player_nickname, d.country
        FROM gold.player_tournament_stats s
        JOIN gold.dim_players d USING (player_id)
        WHERE s.player_id = ?
        """,
        [player_id],
    )

    if player is None:
        raise HTTPException(404, f"Player {player_id} not found")

    return player


@app.get(
    "/players/{player_id}/statistics",
    response_model=list[PlayerMatchStats],
)
def get_player_statistics(player_id: int, conn: DB):
    rows = fetch_all(
        conn,
        """
        SELECT s.match_id, m.match_date, m.home_team, m.away_team,
               s.team_id, s.minutes_played, s.goals, s.assists, s.shots,
               s.shots_on_target, s.xg, s.passes, s.passes_completed,
               s.shot_assists, s.progressive_passes, s.tackles,
               s.tackles_won, s.interceptions
        FROM gold.player_match_stats s
        JOIN silver.matches m USING (match_id)
        WHERE s.player_id = ?
        ORDER BY m.match_date, s.match_id
        """,
        [player_id],
    )

    if not rows:
        raise HTTPException(404, f"No statistics for player {player_id}")

    return rows


# ----------------------------------------------------------------------
# Teams
# ----------------------------------------------------------------------

@app.get("/teams", response_model=list[Team])
def list_teams(conn: DB):
    return fetch_all(
        conn, "SELECT team_id, team FROM gold.dim_teams ORDER BY team"
    )


@app.get("/teams/{team_id}/statistics", response_model=TeamStatistics)
def get_team_statistics(team_id: int, conn: DB):
    matches = fetch_all(
        conn,
        """
        SELECT t.match_id, m.match_date, o.team AS opponent,
               t.goals, o.goals AS goals_against, t.shots, t.xg,
               o.xg AS xg_against, t.passes, t.pass_accuracy_pct,
               t.pass_share_pct, t.possessions, t.pressures
        FROM gold.team_match_stats t
        JOIN silver.matches m USING (match_id)
        LEFT JOIN gold.team_match_stats o
            ON o.match_id = t.match_id AND o.team_id <> t.team_id
        WHERE t.team_id = ?
        ORDER BY m.match_date, t.match_id
        """,
        [team_id],
    )

    if not matches:
        raise HTTPException(404, f"Team {team_id} not found")

    team = fetch_one(
        conn,
        "SELECT team_id, team FROM gold.dim_teams WHERE team_id = ?",
        [team_id],
    )

    def total(key):
        values = [m[key] for m in matches if m[key] is not None]
        return sum(values) if values else None

    def average(key):
        values = [m[key] for m in matches if m[key] is not None]
        return round(sum(values) / len(values), 1) if values else None

    totals = {
        "matches": len(matches),
        "goals": total("goals"),
        "goals_against": total("goals_against"),
        "shots": total("shots"),
        "xg": round(total("xg"), 3),
        "xg_against": (
            round(total("xg_against"), 3)
            if total("xg_against") is not None else None
        ),
        "avg_pass_accuracy_pct": average("pass_accuracy_pct"),
        "avg_pass_share_pct": average("pass_share_pct"),
        "pressures": total("pressures"),
    }

    return {**team, "totals": totals, "matches": matches}
