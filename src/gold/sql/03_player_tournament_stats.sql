-- One row per player aggregated across all loaded matches.
-- Appearances count matches where the player was on the pitch.

CREATE OR REPLACE TABLE gold.player_tournament_stats AS
SELECT
    s.player_id,
    d.player_name,
    ANY_VALUE(t.team) AS team,
    COUNT(*) FILTER (WHERE s.minutes_played > 0) AS appearances,
    ROUND(SUM(s.minutes_played), 1) AS minutes_played,
    SUM(s.goals) AS goals,
    SUM(s.assists) AS assists,
    SUM(s.shots) AS shots,
    SUM(s.shots_on_target) AS shots_on_target,
    ROUND(SUM(s.xg), 3) AS xg,
    SUM(s.passes) AS passes,
    SUM(s.passes_completed) AS passes_completed,
    ROUND(
        100.0 * SUM(s.passes_completed) / NULLIF(SUM(s.passes), 0), 1
    ) AS pass_completion_pct,
    SUM(s.shot_assists) AS shot_assists,
    SUM(s.progressive_passes) AS progressive_passes,
    SUM(s.tackles) AS tackles,
    SUM(s.tackles_won) AS tackles_won,
    SUM(s.interceptions) AS interceptions
FROM gold.player_match_stats s
JOIN gold.dim_players d USING (player_id)
JOIN gold.dim_teams t ON t.team_id = s.team_id
GROUP BY s.player_id, d.player_name;
