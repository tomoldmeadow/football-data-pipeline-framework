# Football Data Pipeline Framework

A reusable data engineering framework for football data. It extracts
[StatsBomb open data](https://github.com/statsbomb/open-data), processes it
through a Bronze / Silver / Gold style flow and loads it into DuckDB.

The longer-term goal is a football intelligence platform: analytical Gold
tables, an API and dashboard, and news-driven RAG features.

## Architecture

```text
StatsBomb Open Data
        |
   Extraction        src/extraction     -> data/bronze (raw JSON)
        |
 Transformation      src/transformation -> pandas DataFrames
        |
   Validation        src/validation     -> errors / warnings
        |
 Loading (Silver)    src/loading        -> DuckDB schema `silver`
        |
  Gold (SQL)         src/gold/sql       -> DuckDB schema `gold`
```

`src/pipeline/football_pipeline.py` orchestrates the stages and
`scripts/run_pipeline.py` is the entry point.

### Silver tables (`silver.*`)

| Table | Contents |
|---|---|
| `matches` | One row per match (teams, date, score) |
| `events` | One row per event with the common StatsBomb fields |
| `pass_events`, `shot_events`, `carry_events`, `dribble_events`, `duel_events`, `foul_events` | Type-specific attributes, keyed on `event_id` |
| `lineups` | Squad players per match (including unused substitutes) |
| `lineup_positions` | Time spells per player and position, the source of minutes played |

### Gold tables (`gold.*`)

Built by the numbered SQL files in `src/gold/sql`, which are rebuilt from
Silver on every run.

| Table | Grain |
|---|---|
| `dim_players`, `dim_teams` | One row per player / team |
| `player_match_stats` | Player per match: minutes, goals, assists, shots, xG, passing, progressive passes, tackles, interceptions |
| `player_tournament_stats` | Player across all loaded matches |
| `team_match_stats` | Team per match: goals, shots, xG, pass accuracy, pass share, possessions, pressures |
| `possessions` | One row per possession sequence |
| `match_summary` | One row per match, both teams side by side |

Metric definitions are documented at the top of each SQL file. Notable
choices: minutes come from lineup positions, not event counts. Penalty
shootout kicks (period 5) are excluded from goals, shots and xG. Possession
is approximated by share of passes.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run

Run as a module from the repo root:

```bash
python -m scripts.run_pipeline
```

Configuration lives in `src/config/settings.py` (competition, season,
`MAX_MATCHES`, skip/refresh behaviour, validation strictness) and paths in
`src/config/paths.py`.

- Existing Bronze files are skipped unless `FORCE_REFRESH = True`.
- A failed match download is logged and skipped; the rest of the run continues.
- Tables are fully refreshed on each load, so re-running never duplicates rows.
- Set `MAX_MATCHES = None` to ingest every match in the competition.

## API

A read-only FastAPI service exposes the Gold tables. After running the
pipeline:

```bash
uvicorn src.api.main:app
```

Interactive docs are at http://127.0.0.1:8000/docs. Set `FOOTBALL_DB_PATH`
to point at a different database file.

| Endpoint | Description |
|---|---|
| `GET /health` | Status and match count |
| `GET /matches` | Match summaries (`team`, `limit`, `offset`) |
| `GET /matches/{match_id}` | One match with both teams' statistics |
| `GET /matches/{match_id}/events` | Events (`event_type`, `team_id`, `player_id`, `period`, paging) |
| `GET /players` | Tournament stats (`q`, `team`, `min_minutes`, `sort_by`, `order`, paging) |
| `GET /players/{player_id}` | Player profile and totals |
| `GET /players/{player_id}/statistics` | Per-match statistics |
| `GET /players/compare?ids=1&ids=2` | Side-by-side totals with per-90 rates (2 to 5 players) |
| `GET /teams` | All teams |
| `GET /teams/{team_id}/statistics` | Totals and match-by-match results with opponent figures |

## Dashboard

A Streamlit dashboard (matches, player leaderboard, player comparison and
team statistics) reads from the API. Start the API, then:

```bash
streamlit run src/dashboard/app.py
```

Set `FOOTBALL_API_URL` if the API is not on `http://127.0.0.1:8000`.

## Validation

Events validation returns `(errors, warnings)`. Errors (duplicate or null IDs,
invalid periods, malformed timestamps and so on) stop the run when
`FAIL_ON_VALIDATION_ERROR` is set. Warnings (such as out-of-pitch
coordinates) are logged only. Optional fields like player or location are
legitimately null for some event types and are not flagged.

## Development

```bash
pytest
ruff check .
```

CI runs both on every pull request.

## Roadmap

1. Football news ingestion.
2. RAG over news plus SQL over DuckDB, then an agent layer.
3. Further Silver detail tables (goalkeeper events and others).
