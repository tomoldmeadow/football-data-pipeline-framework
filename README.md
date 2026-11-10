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
    Loading          src/loading        -> DuckDB (football.db)
```

`src/pipeline/football_pipeline.py` orchestrates the stages and
`scripts/run_pipeline.py` is the entry point.

### Tables

- `matches`: one row per match (teams, date, score).
- `events`: one row per event with the common StatsBomb fields (period,
  timestamp, possession, team, player, position, event type, location).

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

1. Silver/Gold layers: typed event tables, lineups, player/team/possession analytics.
2. FastAPI service and Streamlit dashboard.
3. Football news ingestion.
4. RAG over news plus SQL over DuckDB, then an agent layer.
