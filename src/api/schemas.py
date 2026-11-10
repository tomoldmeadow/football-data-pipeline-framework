from pydantic import BaseModel


class MatchSummary(BaseModel):
    match_id: int
    match_date: str | None = None
    home_team: str
    away_team: str
    home_score: int | None = None
    away_score: int | None = None
    home_shots: int | None = None
    away_shots: int | None = None
    home_xg: float | None = None
    away_xg: float | None = None
    home_pass_share_pct: float | None = None
    away_pass_share_pct: float | None = None
    home_pass_accuracy_pct: float | None = None
    away_pass_accuracy_pct: float | None = None


class TeamMatchStats(BaseModel):
    match_id: int
    team_id: int
    team: str
    goals: int
    shots: int
    shots_on_target: int
    xg: float
    passes: int
    passes_completed: int
    pass_accuracy_pct: float | None = None
    pass_share_pct: float | None = None
    possessions: int
    pressures: int
    fouls_committed: int


class MatchDetail(MatchSummary):
    teams: list[TeamMatchStats]


class Event(BaseModel):
    event_id: str
    index: int
    period: int
    timestamp: str | None = None
    minute: int
    second: int
    event_type: str
    team_id: int | None = None
    team: str | None = None
    player_id: int | None = None
    player: str | None = None
    position: str | None = None
    possession: int | None = None
    play_pattern: str | None = None
    under_pressure: bool = False
    location_x: float | None = None
    location_y: float | None = None


class PlayerSummary(BaseModel):
    player_id: int
    player_name: str
    team: str | None = None
    appearances: int
    minutes_played: float
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    xg: float
    passes: int
    passes_completed: int
    pass_completion_pct: float | None = None
    shot_assists: int
    progressive_passes: int
    tackles: int
    tackles_won: int
    interceptions: int


class PlayerDetail(PlayerSummary):
    player_nickname: str | None = None
    country: str | None = None


class PlayerComparisonEntry(PlayerSummary):
    # Rate stats per 90 minutes; None when the player has no minutes
    per_90: dict[str, float | None]


class PlayerMatchStats(BaseModel):
    match_id: int
    match_date: str | None = None
    home_team: str
    away_team: str
    team_id: int
    minutes_played: float
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    xg: float
    passes: int
    passes_completed: int
    shot_assists: int
    progressive_passes: int
    tackles: int
    tackles_won: int
    interceptions: int


class Team(BaseModel):
    team_id: int
    team: str


class TeamStatsRow(BaseModel):
    match_id: int
    match_date: str | None = None
    opponent: str | None = None
    goals: int
    goals_against: int | None = None
    shots: int
    xg: float
    xg_against: float | None = None
    passes: int
    pass_accuracy_pct: float | None = None
    pass_share_pct: float | None = None
    possessions: int
    pressures: int


class TeamTotals(BaseModel):
    matches: int
    goals: int
    goals_against: int | None = None
    shots: int
    xg: float
    xg_against: float | None = None
    avg_pass_accuracy_pct: float | None = None
    avg_pass_share_pct: float | None = None
    pressures: int


class TeamStatistics(Team):
    totals: TeamTotals
    matches: list[TeamStatsRow]
