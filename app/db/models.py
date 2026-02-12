
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Date, Float, Text, Enum,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine
import enum
import asyncio

from app.core.config import settings

Base = declarative_base()


# ================= ENUMS =================
class TournamentType(str, enum.Enum):
    WORLD_CUP = "world_cup"
    AFCON = "afcon"
    AFCON_QUALIFIERS = "afcon_qualifiers"
    WC_QUALIFIERS = "wc_qualifiers"
    FRIENDLY = "friendly"
    OTHER = "other"


class MatchStatus(str, enum.Enum):
    NOT_STARTED = "notstarted"
    IN_PROGRESS = "inprogress"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"


# class EventType(str, enum.Enum):
#     GOAL = "goal"
#     YELLOW_CARD = "yellowCard"
#     RED_CARD = "redCard"
#     SUBSTITUTION = "substitution"
#     VAR = "var"
#     PENALTY_MISSED = "penaltyMissed"

class EventType(str, enum.Enum):
    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    PENALTY_MISSED = "penalty_missed"
    VAR = "var"

# ================= LEAGUES / SEASONS =================
class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255))
    type = Column(Enum(TournamentType), nullable=False)
    country = Column(String(100))
    logo_url = Column(String(500))

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    seasons = relationship("Season", back_populates="league")
    fixtures = relationship("Fixture", back_populates="league")


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    year = Column(String(20), nullable=False)
    name = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)
    current = Column(Boolean, default=False)

    league = relationship("League", back_populates="seasons")
    fixtures = relationship("Fixture", back_populates="season")
    standings = relationship("Standing", back_populates="season")


# ================= TEAMS =================
class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255))
    short_name = Column(String(100))
    code = Column(String(10))
    country = Column(String(100))
    national = Column(Boolean, default=False)
    logo_url = Column(String(500))
    founded = Column(Integer)

    primary_color = Column(String(7))
    secondary_color = Column(String(7))

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    home_fixtures = relationship("Fixture", foreign_keys="Fixture.home_team_id", back_populates="home_team")
    away_fixtures = relationship("Fixture", foreign_keys="Fixture.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")
    match_statistics = relationship("MatchStatistics", back_populates="team")
    team_statistics = relationship("TeamStatistics", back_populates="team")
    team_managers = relationship("TeamManager", back_populates="team")


# ================= MANAGERS =================
class Manager(Base):
    __tablename__ = "managers"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    slug = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    date_of_birth = Column(Date)
    nationality = Column(String(100))
    photo_url = Column(String(500))
    
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")
    
    team_managers = relationship("TeamManager", back_populates="manager")


class TeamManager(Base):
    __tablename__ = "team_managers"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False, index=True)
    
    start_date = Column(Date)
    end_date = Column(Date, nullable=True) 
    is_current = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default="now()")
    
    __table_args__ = (
        UniqueConstraint('team_id', 'manager_id', 'start_date', name='uq_team_manager_period'),
    )
    
    team = relationship("Team", back_populates="team_managers")
    manager = relationship("Manager", back_populates="team_managers")


# ================= PLAYERS =================
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255))
    short_name = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))

    position = Column(String(2))
    jersey_number = Column(Integer)

    date_of_birth = Column(Date)
    height = Column(Integer)
    preferred_foot = Column(String(20))

    photo_url = Column(String(500))

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    team = relationship("Team", back_populates="players")
    statistics = relationship("PlayerStatistics", back_populates="player")
    events = relationship("MatchEvent", foreign_keys="MatchEvent.player_id", back_populates="player")
    assists = relationship("MatchEvent", foreign_keys="MatchEvent.assist_player_id", back_populates="assist_player")


# ================= FIXTURES =================
class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)

    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False, index=True)

    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)

    date = Column(DateTime, nullable=False, index=True)
    timestamp = Column(Integer)

    round = Column(Integer) 
    round_name = Column(String(100)) 
    group_name = Column(String(100)) 
    group_sign = Column(String(10))

    status = Column(Enum(MatchStatus), default=MatchStatus.NOT_STARTED, index=True)
    status_long = Column(String(50))
    elapsed = Column(Integer)

    home_score = Column(Integer)
    away_score = Column(Integer)
    home_score_period1 = Column(Integer)
    away_score_period1 = Column(Integer)
    home_score_period2 = Column(Integer)
    away_score_period2 = Column(Integer)
    home_score_normaltime = Column(Integer)
    away_score_normaltime = Column(Integer)

    is_live = Column(Boolean, default=False)
    has_lineups = Column(Boolean, default=False)
    has_statistics = Column(Boolean, default=False)
    has_events = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    league = relationship("League", back_populates="fixtures")
    season = relationship("Season", back_populates="fixtures")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_fixtures")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_fixtures")
    events = relationship("MatchEvent", back_populates="fixture")
    lineups = relationship("Lineup", back_populates="fixture")
    match_statistics = relationship("MatchStatistics", back_populates="fixture")


# ================= EVENTS =================
class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)
    assist_player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)
    player_out_id = Column(Integer, ForeignKey("players.id"), nullable=True)

    type = Column(Enum(EventType), nullable=False)
    minute = Column(Integer, nullable=False)
    extra_minute = Column(Integer)
    is_home = Column(Boolean, nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    incident_class = Column(String(50))
    reason = Column(String(100))
    detail = Column(String(255))
    comments = Column(Text)
    
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    fixture = relationship("Fixture", back_populates="events")
    player = relationship("Player", foreign_keys=[player_id], back_populates="events")
    assist_player = relationship("Player", foreign_keys=[assist_player_id], back_populates="assists")
    player_out = relationship("Player", foreign_keys=[player_out_id])
    team = relationship("Team")


# ================= LINEUPS =================
class Lineup(Base):
    __tablename__ = "lineups"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)

    formation = Column(String(10))
    position = Column(String(50))
    starter = Column(Boolean, default=True)

    rating = Column(Float)
    minutes_played = Column(Integer)
    captain = Column(Boolean, default=False)
    substitute = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('fixture_id', 'team_id', 'player_id', name='uq_lineup_fixture_team_player'),
    )

    fixture = relationship("Fixture", back_populates="lineups")
    team = relationship("Team")
    player = relationship("Player")


# ================= STATISTICS =================
class MatchStatistics(Base):
    __tablename__ = "match_statistics"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)

    shots_on_goal = Column(Integer)
    shots_off_goal = Column(Integer)
    total_shots = Column(Integer)
    blocked_shots = Column(Integer)
    shots_inside_box = Column(Integer)
    shots_outside_box = Column(Integer)
    fouls = Column(Integer)
    corners = Column(Integer)
    offsides = Column(Integer)
    ball_possession = Column(Float)
    passes = Column(Integer)
    pass_accuracy = Column(Float)
    tackles = Column(Integer)
    saves = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    fouls_drawn = Column(Integer)
    penalties_committed = Column(Integer)
    penalties_saved = Column(Integer)
    penalties_missed = Column(Integer)
    crosses = Column(Integer)
    crosses_accuracy = Column(Float)
    throw_ins = Column(Integer)
    clearances = Column(Integer)
    interceptions = Column(Integer)
    aerials_won = Column(Integer)
    aerials_lost = Column(Integer)
    offsides_given = Column(Integer)
    offsides_won = Column(Integer)
    dribbles = Column(Integer)
    dribble_success = Column(Float)
    tackles_won = Column(Float)
    tackles_lost = Column(Float)
    
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    __table_args__ = (
        UniqueConstraint('fixture_id', 'team_id', name='uq_match_stats_fixture_team'),
    )

    fixture = relationship("Fixture", back_populates="match_statistics")
    team = relationship("Team", back_populates="match_statistics")

class PlayerStatistics(Base):
    __tablename__ = "player_statistics"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)

    # Stats de base
    rating = Column(Float)
    appearances = Column(Integer)
    minutes_played = Column(Integer)
    
    # Buts et passes
    goals = Column(Integer)
    assists = Column(Integer)
    big_chances_created = Column(Integer)
    big_chances_missed = Column(Integer)
    
    # Tirs
    total_shots = Column(Integer)
    shots_on_target = Column(Integer)
    shots_off_target = Column(Integer)
    shots_from_inside_box = Column(Integer)
    shots_from_outside_box = Column(Integer)
    goal_conversion_percentage = Column(Float)
    
    # Passes
    total_passes = Column(Integer)
    accurate_passes = Column(Integer)
    accurate_passes_percentage = Column(Float)
    key_passes = Column(Integer)
    accurate_crosses = Column(Integer)
    accurate_crosses_percentage = Column(Float)
    accurate_long_balls = Column(Integer)
    accurate_long_balls_percentage = Column(Float)
    
    # Duels et défense
    total_duels_won = Column(Integer)
    total_duels_won_percentage = Column(Float)
    ground_duels_won = Column(Integer)
    ground_duels_won_percentage = Column(Float)
    aerial_duels_won = Column(Integer)
    aerial_duels_won_percentage = Column(Float)
    tackles = Column(Integer)
    tackles_won = Column(Integer)
    tackles_won_percentage = Column(Float)
    interceptions = Column(Integer)
    clearances = Column(Integer)
    
    # Dribbles
    successful_dribbles = Column(Integer)
    successful_dribbles_percentage = Column(Float)
    dribbled_past = Column(Integer)
    
    # Discipline
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    fouls = Column(Integer)
    was_fouled = Column(Integer)
    
    # Gardien
    saves = Column(Integer)
    clean_sheet = Column(Integer)
    goals_conceded = Column(Integer)
    penalty_save = Column(Integer)
    
    # Penalties
    penalty_goals = Column(Integer)
    penalties_taken = Column(Integer)
    penalty_conversion = Column(Float)
    
    # Divers
    touches = Column(Integer)
    possession_lost = Column(Integer)
    offsides = Column(Integer)
    hit_woodwork = Column(Integer)
    own_goals = Column(Integer)
    
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    __table_args__ = (
        UniqueConstraint('player_id', 'season_id', 'league_id', name='uq_player_stats_season_league'),
    )

    player = relationship("Player", back_populates="statistics")
    season = relationship("Season")
    league = relationship("League")


class TeamStatistics(Base):
    __tablename__ = "team_statistics"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False, index=True)

    # Matchs
    matches = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    
    # Buts
    goals_scored = Column(Integer)
    goals_conceded = Column(Integer)
    own_goals = Column(Integer)
    assists = Column(Integer)
    
    # Tirs
    shots = Column(Integer)
    shots_on_target = Column(Integer)
    shots_off_target = Column(Integer)
    shots_from_inside_box = Column(Integer)
    shots_from_outside_box = Column(Integer)
    blocked_scoring_attempt = Column(Integer)
    big_chances = Column(Integer)
    big_chances_created = Column(Integer)
    big_chances_missed = Column(Integer)
    hit_woodwork = Column(Integer)
    
    # Passes
    total_passes = Column(Integer)
    accurate_passes = Column(Integer)
    accurate_passes_percentage = Column(Float)
    total_long_balls = Column(Integer)
    accurate_long_balls = Column(Integer)
    accurate_long_balls_percentage = Column(Float)
    total_crosses = Column(Integer)
    accurate_crosses = Column(Integer)
    accurate_crosses_percentage = Column(Float)
    
    # Possession
    average_ball_possession = Column(Float)
    
    # Défense
    tackles = Column(Integer)
    interceptions = Column(Integer)
    clearances = Column(Integer)
    saves = Column(Integer)
    clean_sheets = Column(Integer)
    
    # Duels
    total_duels = Column(Integer)
    duels_won = Column(Integer)
    duels_won_percentage = Column(Float)
    ground_duels_won = Column(Integer)
    ground_duels_won_percentage = Column(Float)
    aerial_duels_won = Column(Integer)
    aerial_duels_won_percentage = Column(Float)
    
    # Discipline
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    fouls = Column(Integer)
    
    # Corners et coups de pied arrêtés
    corners = Column(Integer)
    free_kicks = Column(Integer)
    
    # Dribbles
    successful_dribbles = Column(Integer)
    dribble_attempts = Column(Integer)
    
    # Penalties
    penalty_goals = Column(Integer)
    penalties_taken = Column(Integer)
    penalties_commited = Column(Integer)
    
    # Autres
    offsides = Column(Integer)
    possession_lost = Column(Integer)
    errors_leading_to_goal = Column(Integer)
    ball_recovery = Column(Integer)
    
    # Rating moyen
    avg_rating = Column(Float)
    
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    __table_args__ = (
        UniqueConstraint('team_id', 'season_id', 'league_id', name='uq_team_stats_season_league'),
    )

    team = relationship("Team", back_populates="team_statistics")
    season = relationship("Season")
    league = relationship("League")

# ================= STANDINGS =================
class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)

    group = Column(String(100))
    rank = Column(Integer)
    total_matches = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    goals_for = Column(Integer)
    goals_against = Column(Integer)
    goal_difference = Column(Integer)
    points = Column(Integer)

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    __table_args__ = (
        UniqueConstraint('season_id', 'team_id', 'group', name='uq_standing_season_team_group'),
    )

    season = relationship("Season", back_populates="standings")
    team = relationship("Team", foreign_keys=[team_id])


# ================= API KEY =================
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default="now()")
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    request_count = Column(Integer, default=0)
    rate_limit = Column(Integer, default=1000)
    
    owner_email = Column(String(255))

# ================= CREATE SCHEMA =================
async def create_schema():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database schema created successfully!")


if __name__ == "__main__":
    asyncio.run(create_schema())