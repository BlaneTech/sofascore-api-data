from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ================= ENUMS =================
class TournamentTypeEnum(str, Enum):
    WORLD_CUP = "world_cup"
    AFCON = "afcon"
    AFCON_QUALIFIERS = "afcon_qualifiers"
    WC_QUALIFIERS = "wc_qualifiers"
    FRIENDLY = "friendly"
    OTHER = "other"


class MatchStatusEnum(str, Enum):
    NOT_STARTED = "notstarted"
    IN_PROGRESS = "inprogress"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"


class EventTypeEnum(str, Enum):
    # GOAL = "goal"
    # YELLOW_CARD = "yellowCard"
    # RED_CARD = "redCard"
    # SUBSTITUTION = "substitution"
    # VAR = "var"
    # PENALTY_MISSED = "penaltyMissed"

    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    PENALTY_MISSED = "penalty_missed"
    VAR = "var"

# ================= TEAMS =================
class TeamBase(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TeamDetailed(TeamBase):
    sofascore_id: int
    slug: Optional[str] = None
    short_name: Optional[str] = None
    national: bool
    founded: Optional[int] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


# ================= LEAGUES & SEASONS =================
class LeagueBase(BaseModel):
    id: int
    name: str
    type: TournamentTypeEnum
    country: Optional[str] = None
    logo_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SeasonBase(BaseModel):
    id: int
    year: str
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current: bool
    
    model_config = ConfigDict(from_attributes=True)


# ================= PLAYERS =================
class PlayerBase(BaseModel):
    id: int
    name: str
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    photo_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PlayerDetailed(PlayerBase):
    sofascore_id: int
    slug: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[int] = None
    preferred_foot: Optional[str] = None


# ================= MANAGERS =================
class ManagerBase(BaseModel):
    id: int
    name: str
    nationality: Optional[str] = None
    photo_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ManagerDetailed(ManagerBase):
    sofascore_id: int
    slug: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None


class TeamManagerSchema(BaseModel):
    manager: ManagerBase
    team: TeamBase
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    
    model_config = ConfigDict(from_attributes=True)


# ================= FIXTURES =================
class FixtureBase(BaseModel):
    id: int
    date: datetime
    status: MatchStatusEnum
    round: Optional[int] = None
    round_name: Optional[str] = None
    
    home_team: TeamBase
    away_team: TeamBase
    
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class FixtureDetailed(FixtureBase):
    sofascore_id: int
    league: LeagueBase
    season: SeasonBase
    
    group_name: Optional[str] = None
    group_sign: Optional[str] = None
    
    home_score_period1: Optional[int] = None
    away_score_period1: Optional[int] = None
    home_score_period2: Optional[int] = None
    away_score_period2: Optional[int] = None
    home_score_normaltime: Optional[int] = None
    away_score_normaltime: Optional[int] = None
    
    is_live: bool = False
    has_lineups: bool = False
    has_statistics: bool = False
    has_events: bool = False


# ================= EVENTS =================
class MatchEventSchema(BaseModel):
    id: int
    type: EventTypeEnum
    minute: int
    extra_minute: Optional[int] = None
    detail: Optional[str] = None
    player: Optional[PlayerBase] = None
    assist_player: Optional[PlayerBase] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================= LINEUPS =================
class LineupPlayerSchema(BaseModel):
    player: PlayerBase
    position: Optional[str] = None
    formation: Optional[str] = None
    starter: bool
    substitute: bool
    captain: bool = False
    rating: Optional[float] = None
    minutes_played: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class LineupSchema(BaseModel):
    team: TeamBase
    formation: Optional[str] = None
    starters: List[LineupPlayerSchema]
    substitutes: List[LineupPlayerSchema]
    
    model_config = ConfigDict(from_attributes=True)


# ================= MATCH STATISTICS =================
class MatchStatisticsSchema(BaseModel):
    team: TeamBase
    
    shots_on_goal: Optional[int] = None
    shots_off_goal: Optional[int] = None
    total_shots: Optional[int] = None
    blocked_shots: Optional[int] = None
    shots_inside_box: Optional[int] = None
    shots_outside_box: Optional[int] = None
    
    fouls: Optional[int] = None
    corners: Optional[int] = None
    offsides: Optional[int] = None
    
    ball_possession: Optional[float] = None
    
    passes: Optional[int] = None
    pass_accuracy: Optional[float] = None
    
    tackles: Optional[int] = None
    saves: Optional[int] = None
    
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================= PLAYER STATISTICS =================
class PlayerStatisticsSchema(BaseModel):
    player: PlayerBase
    season: SeasonBase
    league: LeagueBase
    
    rating: Optional[float] = None
    appearances: Optional[int] = None
    minutes_played: Optional[int] = None
    
    goals: Optional[int] = None
    assists: Optional[int] = None
    big_chances_created: Optional[int] = None
    big_chances_missed: Optional[int] = None
    
    total_shots: Optional[int] = None
    shots_on_target: Optional[int] = None
    shots_off_target: Optional[int] = None
    goal_conversion_percentage: Optional[float] = None
    
    total_passes: Optional[int] = None
    accurate_passes: Optional[int] = None
    accurate_passes_percentage: Optional[float] = None
    key_passes: Optional[int] = None
    
    total_duels_won: Optional[int] = None
    total_duels_won_percentage: Optional[float] = None
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    
    successful_dribbles: Optional[int] = None
    successful_dribbles_percentage: Optional[float] = None
    
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    fouls: Optional[int] = None
    
    saves: Optional[int] = None
    clean_sheet: Optional[int] = None
    goals_conceded: Optional[int] = None
    
    penalty_goals: Optional[int] = None
    penalties_taken: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================= TEAM STATISTICS =================
class TeamStatisticsSchema(BaseModel):
    team: TeamBase
    season: SeasonBase
    league: LeagueBase
    
    matches: Optional[int] = None
    
    goals_scored: Optional[int] = None
    goals_conceded: Optional[int] = None
    assists: Optional[int] = None
    
    shots: Optional[int] = None
    shots_on_target: Optional[int] = None
    big_chances: Optional[int] = None
    big_chances_created: Optional[int] = None
    big_chances_missed: Optional[int] = None
    
    total_passes: Optional[int] = None
    accurate_passes: Optional[int] = None
    accurate_passes_percentage: Optional[float] = None
    
    average_ball_possession: Optional[float] = None
    
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    clearances: Optional[int] = None
    saves: Optional[int] = None
    clean_sheets: Optional[int] = None
    
    total_duels: Optional[int] = None
    duels_won: Optional[int] = None
    duels_won_percentage: Optional[float] = None
    
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    fouls: Optional[int] = None
    
    corners: Optional[int] = None
    offsides: Optional[int] = None
    
    avg_rating: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================= STANDINGS =================
class StandingSchema(BaseModel):
    rank: int
    team: TeamBase
    group: Optional[str] = None
    total_matches: Optional[int] = None
    wins: Optional[int] = None
    draws: Optional[int] = None
    losses: Optional[int] = None
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None
    goal_difference: Optional[int] = None
    points: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ================= RESPONSE SCHEMAS =================
class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class APIResponse(BaseModel):
    success: bool = True
    data: Optional[dict | list] = None
    errors: Optional[List[str]] = None
    meta: Optional[PaginationMeta] = None


# ================= REQUEST FILTERS =================
class FixtureFilters(BaseModel):
    league_id: Optional[int] = None
    season_id: Optional[int] = None
    team_id: Optional[int] = None
    date: Optional[datetime] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[MatchStatusEnum] = None
    round: Optional[int] = None
    live: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class TeamFilters(BaseModel):
    league_id: Optional[int] = None
    country: Optional[str] = None
    national: Optional[bool] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PlayerFilters(BaseModel):
    team_id: Optional[int] = None
    position: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class ManagerFilters(BaseModel):
    nationality: Optional[str] = None
    current_only: Optional[bool] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class EventFilters(BaseModel):
    fixture_id: Optional[int] = None
    team_id: Optional[int] = None
    player_id: Optional[int] = None
    event_type: Optional[EventTypeEnum] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class LineupFilters(BaseModel):
    fixture_id: Optional[int] = None
    team_id: Optional[int] = None
    player_id: Optional[int] = None
    starter: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)