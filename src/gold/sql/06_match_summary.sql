-- One row per match with both teams side by side.

CREATE OR REPLACE TABLE gold.match_summary AS
SELECT
    m.match_id,
    m.match_date,
    m.home_team,
    m.away_team,
    m.home_score,
    m.away_score,
    h.shots AS home_shots,
    a.shots AS away_shots,
    h.xg AS home_xg,
    a.xg AS away_xg,
    h.pass_share_pct AS home_pass_share_pct,
    a.pass_share_pct AS away_pass_share_pct,
    h.pass_accuracy_pct AS home_pass_accuracy_pct,
    a.pass_accuracy_pct AS away_pass_accuracy_pct
FROM silver.matches m
LEFT JOIN gold.team_match_stats h
    ON h.match_id = m.match_id AND h.team = m.home_team
LEFT JOIN gold.team_match_stats a
    ON a.match_id = m.match_id AND a.team = m.away_team;
