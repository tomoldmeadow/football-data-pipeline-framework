-- One row per possession sequence.
--
-- Definitions
--   duration_seconds   last event time minus first event time in the sequence
--   ended_in_shot/goal whether any shot / goal (periods 1-4) occurred in it
--   start_play_pattern the play pattern of the sequence's first event
--   final_event_type   the last event of the sequence

CREATE OR REPLACE TABLE gold.possessions AS
WITH events AS (
    SELECT
        e.*,
        e.minute * 60 + e.second AS clock_seconds
    FROM silver.events e
    WHERE e.possession IS NOT NULL
),

pass_counts AS (
    SELECT
        e.match_id,
        e.possession,
        COUNT(*) AS passes
    FROM events e
    JOIN silver.pass_events p USING (event_id)
    GROUP BY e.match_id, e.possession
),

shot_counts AS (
    SELECT
        e.match_id,
        e.possession,
        COUNT(*) AS shots,
        COUNT(*) FILTER (WHERE s.outcome = 'Goal') AS goals,
        COALESCE(SUM(s.xg), 0) AS xg
    FROM events e
    JOIN silver.shot_events s USING (event_id)
    WHERE e.period <= 4
    GROUP BY e.match_id, e.possession
),

sequence AS (
    SELECT
        match_id,
        possession,
        ANY_VALUE(possession_team_id) AS team_id,
        ANY_VALUE(possession_team) AS team,
        MIN(period) AS period,
        MIN(clock_seconds) AS start_seconds,
        MAX(clock_seconds) AS end_seconds,
        ARG_MIN(play_pattern, index) AS start_play_pattern,
        ARG_MAX(event_type, index) AS final_event_type,
        COUNT(*) AS events
    FROM events
    GROUP BY match_id, possession
)

SELECT
    q.match_id,
    q.possession,
    q.team_id,
    q.team,
    q.period,
    q.start_seconds,
    q.end_seconds,
    q.end_seconds - q.start_seconds AS duration_seconds,
    q.start_play_pattern,
    q.final_event_type,
    q.events,
    COALESCE(p.passes, 0) AS passes,
    COALESCE(s.shots, 0) AS shots,
    ROUND(COALESCE(s.xg, 0), 3) AS xg,
    COALESCE(s.shots, 0) > 0 AS ended_in_shot,
    COALESCE(s.goals, 0) > 0 AS ended_in_goal
FROM sequence q
LEFT JOIN pass_counts p USING (match_id, possession)
LEFT JOIN shot_counts s USING (match_id, possession);
