-- Dimension tables derived from the Silver layer.

CREATE OR REPLACE TABLE gold.dim_teams AS
SELECT DISTINCT team_id, team
FROM silver.events
WHERE team_id IS NOT NULL;

CREATE OR REPLACE TABLE gold.dim_players AS
SELECT
    player_id,
    -- A player's name is constant; take the first seen to stay deterministic
    MIN(player_name) AS player_name,
    MIN(player_nickname) AS player_nickname,
    MIN(country) AS country
FROM silver.lineups
WHERE player_id IS NOT NULL
GROUP BY player_id;
