-- One row per team per match.
--
-- Definitions
--   goals             shots with outcome Goal (periods 1-4) plus own goals
--                     scored for the team; shootout kicks (period 5) excluded
--   pass_share_pct    the team's share of all passes in the match, used as a
--                     simple possession proxy
--   possessions       distinct possession sequences controlled by the team
--   pressures         Pressure events by the team

CREATE OR REPLACE TABLE gold.team_match_stats AS
WITH team_matches AS (
    SELECT DISTINCT match_id, team_id, team
    FROM silver.events
    WHERE team_id IS NOT NULL
),

shots AS (
    SELECT
        e.match_id,
        e.team_id,
        COUNT(*) AS shots,
        COUNT(*) FILTER (
            WHERE s.outcome IN ('Goal', 'Saved', 'Saved To Post')
        ) AS shots_on_target,
        COUNT(*) FILTER (WHERE s.outcome = 'Goal') AS shot_goals,
        COALESCE(SUM(s.xg), 0) AS xg
    FROM silver.events e
    JOIN silver.shot_events s USING (event_id)
    WHERE e.period <= 4
    GROUP BY e.match_id, e.team_id
),

own_goals AS (
    SELECT match_id, team_id, COUNT(*) AS own_goals_for
    FROM silver.events
    WHERE event_type = 'Own Goal For'
    GROUP BY match_id, team_id
),

passes AS (
    SELECT
        e.match_id,
        e.team_id,
        COUNT(*) AS passes,
        COUNT(*) FILTER (WHERE p.is_completed) AS passes_completed
    FROM silver.events e
    JOIN silver.pass_events p USING (event_id)
    GROUP BY e.match_id, e.team_id
),

other AS (
    SELECT
        match_id,
        team_id,
        COUNT(*) FILTER (WHERE event_type = 'Pressure') AS pressures,
        COUNT(*) FILTER (WHERE event_type = 'Foul Committed')
            AS fouls_committed
    FROM silver.events
    GROUP BY match_id, team_id
),

possessions AS (
    SELECT
        match_id,
        possession_team_id AS team_id,
        COUNT(DISTINCT possession) AS possessions
    FROM silver.events
    GROUP BY match_id, possession_team_id
)

SELECT
    t.match_id,
    t.team_id,
    t.team,
    COALESCE(s.shot_goals, 0) + COALESCE(o.own_goals_for, 0) AS goals,
    COALESCE(s.shots, 0) AS shots,
    COALESCE(s.shots_on_target, 0) AS shots_on_target,
    ROUND(COALESCE(s.xg, 0), 3) AS xg,
    COALESCE(p.passes, 0) AS passes,
    COALESCE(p.passes_completed, 0) AS passes_completed,
    ROUND(
        100.0 * p.passes_completed / NULLIF(p.passes, 0), 1
    ) AS pass_accuracy_pct,
    ROUND(
        100.0 * p.passes / NULLIF(SUM(p.passes) OVER (PARTITION BY t.match_id), 0),
        1
    ) AS pass_share_pct,
    COALESCE(po.possessions, 0) AS possessions,
    COALESCE(x.pressures, 0) AS pressures,
    COALESCE(x.fouls_committed, 0) AS fouls_committed
FROM team_matches t
LEFT JOIN shots s USING (match_id, team_id)
LEFT JOIN own_goals o USING (match_id, team_id)
LEFT JOIN passes p USING (match_id, team_id)
LEFT JOIN other x USING (match_id, team_id)
LEFT JOIN possessions po USING (match_id, team_id);
