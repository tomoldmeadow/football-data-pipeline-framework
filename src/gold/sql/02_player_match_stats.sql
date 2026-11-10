-- One row per player per match they appeared in.
--
-- Definitions
--   minutes_played        time on the pitch from lineup position spells
--                         (a null end time means "until the final whistle";
--                         spells flagged is_valid = false are ignored and
--                         overlapping spells are merged)
--   goals / shots / xg    open-play and extra-time shots only; period 5
--                         (penalty shootout) is excluded
--   assists               completed passes flagged goal_assist by StatsBomb
--   progressive_passes    completed passes (excluding kick-offs) that move the
--                         ball at least 25% closer to the opponent goal
--                         centre (120, 40)
--   tackles               duels of type Tackle (tackles_won = Won or
--                         Success In/Out)

CREATE OR REPLACE TABLE gold.player_match_stats AS
WITH match_end AS (
    SELECT match_id, MAX(minute * 60 + second) AS end_seconds
    FROM silver.events
    GROUP BY match_id
),

spells AS (
    SELECT
        p.match_id,
        p.player_id,
        p.team_id,
        p.from_seconds AS start_seconds,
        COALESCE(p.to_seconds, m.end_seconds) AS end_seconds
    FROM silver.lineup_positions p
    JOIN match_end m USING (match_id)
    WHERE p.is_valid
),

-- Some source rows overlap (e.g. a starter who also has a later "Player On"
-- spell). Merge overlapping spells so time on the pitch is counted once;
-- real gaps (a player briefly off the pitch) stay uncounted.
spells_with_prior AS (
    SELECT
        *,
        MAX(end_seconds) OVER (
            PARTITION BY match_id, player_id
            ORDER BY start_seconds, end_seconds
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS prior_max_end
    FROM spells
),

spell_groups AS (
    SELECT
        *,
        SUM(
            CASE
                WHEN prior_max_end IS NULL OR start_seconds > prior_max_end
                THEN 1 ELSE 0
            END
        ) OVER (
            PARTITION BY match_id, player_id
            ORDER BY start_seconds, end_seconds
        ) AS spell_group
    FROM spells_with_prior
),

merged_spells AS (
    SELECT
        match_id,
        player_id,
        MIN(team_id) AS team_id,
        MAX(end_seconds) - MIN(start_seconds) AS seconds_on_pitch
    FROM spell_groups
    GROUP BY match_id, player_id, spell_group
),

minutes AS (
    SELECT
        match_id,
        player_id,
        MIN(team_id) AS team_id,
        SUM(seconds_on_pitch) / 60.0 AS minutes_played
    FROM merged_spells
    GROUP BY match_id, player_id
),

shots AS (
    SELECT
        e.match_id,
        e.player_id,
        COUNT(*) AS shots,
        COUNT(*) FILTER (WHERE s.outcome = 'Goal') AS goals,
        COUNT(*) FILTER (
            WHERE s.outcome IN ('Goal', 'Saved', 'Saved To Post')
        ) AS shots_on_target,
        COALESCE(SUM(s.xg), 0) AS xg
    FROM silver.events e
    JOIN silver.shot_events s USING (event_id)
    WHERE e.period <= 4
    GROUP BY e.match_id, e.player_id
),

passes AS (
    SELECT
        e.match_id,
        e.player_id,
        COUNT(*) AS passes,
        COUNT(*) FILTER (WHERE p.is_completed) AS passes_completed,
        COUNT(*) FILTER (WHERE p.goal_assist) AS assists,
        COUNT(*) FILTER (WHERE p.shot_assist) AS shot_assists,
        COUNT(*) FILTER (
            WHERE p.is_completed
              AND p.pass_type IS DISTINCT FROM 'Kick Off'
              AND p.end_x IS NOT NULL
              AND e.location_x IS NOT NULL
              AND SQRT(POWER(120 - p.end_x, 2) + POWER(40 - p.end_y, 2))
                  <= 0.75 * SQRT(
                      POWER(120 - e.location_x, 2)
                      + POWER(40 - e.location_y, 2)
                  )
        ) AS progressive_passes
    FROM silver.events e
    JOIN silver.pass_events p USING (event_id)
    GROUP BY e.match_id, e.player_id
),

tackles AS (
    SELECT
        e.match_id,
        e.player_id,
        COUNT(*) AS tackles,
        COUNT(*) FILTER (
            WHERE d.outcome IN ('Won', 'Success In Play', 'Success Out')
        ) AS tackles_won
    FROM silver.events e
    JOIN silver.duel_events d USING (event_id)
    WHERE d.duel_type = 'Tackle'
    GROUP BY e.match_id, e.player_id
),

interceptions AS (
    SELECT match_id, player_id, COUNT(*) AS interceptions
    FROM silver.events
    WHERE event_type = 'Interception'
    GROUP BY match_id, player_id
)

SELECT
    m.match_id,
    m.player_id,
    m.team_id,
    ROUND(m.minutes_played, 1) AS minutes_played,
    COALESCE(s.goals, 0) AS goals,
    COALESCE(p.assists, 0) AS assists,
    COALESCE(s.shots, 0) AS shots,
    COALESCE(s.shots_on_target, 0) AS shots_on_target,
    ROUND(COALESCE(s.xg, 0), 3) AS xg,
    COALESCE(p.passes, 0) AS passes,
    COALESCE(p.passes_completed, 0) AS passes_completed,
    COALESCE(p.shot_assists, 0) AS shot_assists,
    COALESCE(p.progressive_passes, 0) AS progressive_passes,
    COALESCE(t.tackles, 0) AS tackles,
    COALESCE(t.tackles_won, 0) AS tackles_won,
    COALESCE(i.interceptions, 0) AS interceptions
FROM minutes m
LEFT JOIN shots s USING (match_id, player_id)
LEFT JOIN passes p USING (match_id, player_id)
LEFT JOIN tackles t USING (match_id, player_id)
LEFT JOIN interceptions i USING (match_id, player_id);
