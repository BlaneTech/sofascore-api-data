from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Date, Float, Text, Enum,
    create_engine
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import enum
import asyncio

Base = declarative_base()

DATABASE_URL = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"

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

class EventType(str, enum.Enum):
    GOAL = "goal"
    YELLOW_CARD = "yellowCard"
    RED_CARD = "redCard"
    SUBSTITUTION = "substitution"
    VAR = "var"
    PENALTY_MISSED = "penaltyMissed"

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
    # is_female = Column(Boolean, default=False)

class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
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
    # is_female = Column(Boolean, default=False)
    # venue_name = Column(String(255))
    # venue_city = Column(String(100))
    # venue_capacity = Column(Integer)

    primary_color = Column(String(7))
    secondary_color = Column(String(7))

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    # raw_data = Column(JSON)

    home_fixtures = relationship("Fixture", foreign_keys="Fixture.home_team_id", back_populates="home_team")
    away_fixtures = relationship("Fixture", foreign_keys="Fixture.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")
    match_statistics = relationship("MatchStatistics", back_populates="team")
    team_statistics = relationship("TeamStatistics", back_populates="team")

# ================= PLAYERS =================
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255))
    short_name = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))

    position = Column(String(2))
    jersey_number = Column(Integer)

    date_of_birth = Column(Date)
    # nationality = Column(String(100))
    height = Column(Integer)
    # weight = Column(Integer)
    preferred_foot = Column(String(20))

    photo_url = Column(String(500))

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    # raw_data = Column(JSON)

    team = relationship("Team", back_populates="players")
    statistics = relationship("PlayerStatistics", back_populates="player")
    events = relationship("MatchEvent", foreign_keys="MatchEvent.player_id", back_populates="player")
    assists = relationship("MatchEvent", foreign_keys="MatchEvent.assist_player_id", back_populates="assist_player")

# ================= FIXTURES =================
class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)

    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)

    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

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

    # venue = Column(String(255))
    # city = Column(String(100))
    # referee = Column(String(255))

    is_live = Column(Boolean, default=False)
    has_lineups = Column(Boolean, default=False)
    has_statistics = Column(Boolean, default=False)
    has_events = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    # raw_data = Column(JSON)

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
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    assist_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)

    type = Column(Enum(EventType), nullable=False)
    minute = Column(Integer, nullable=False)
    extra_minute = Column(Integer)
    detail = Column(String(255))
    comments = Column(Text)

    fixture = relationship("Fixture", back_populates="events")
    player = relationship("Player", foreign_keys=[player_id], back_populates="events")
    # assist_player = relationship("Player", foreign_keys=[assist_player_id])
    team = relationship("Team")
    assist_player = relationship("Player", foreign_keys=[assist_player_id], back_populates="assists")

# ================= LINEUPS =================
class Lineup(Base):
    __tablename__ = "lineups"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    formation = Column(String(10))
    position = Column(String(50))
    # grid = Column(String(5))
    starter = Column(Boolean, default=True)

    rating = Column(Float)
    minutes_played = Column(Integer)
    captain = Column(Boolean, default=False)
    substitute = Column(Boolean, default=False)

    fixture = relationship("Fixture", back_populates="lineups")
    team = relationship("Team")
    player = relationship("Player")

# ================= STATISTICS =================
class MatchStatistics(Base):
    __tablename__ = "match_statistics"

    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    shots_on_goal = Column(Integer)
    shots_off_goal = Column(Integer)
    total_shots = Column(Integer)
    blocked_shots = Column(Integer)
    shots_inside_box = Column(Integer)
    shots_outside_box = Column(Integer) # last line
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

    fixture = relationship("Fixture", back_populates="match_statistics")
    team = relationship("Team", back_populates="match_statistics")

class PlayerStatistics(Base):
    __tablename__ = "player_statistics"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)

    rating = Column(Float)
    minutes_played = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    shots = Column(Integer)
    shots_on_target = Column(Integer)
    passes = Column(Integer)
    pass_accuracy = Column(Float)
    tackles = Column(Integer)
    interceptions = Column(Integer)
    fouls = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    dribbles = Column(Integer)
    dribble_attempts = Column(Integer)

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    player = relationship("Player", back_populates="statistics")

class TeamStatistics(Base):
    __tablename__ = "team_statistics"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    total_matches = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_difference = Column(Integer, default=0)
    points = Column(Integer, default=0)

    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, onupdate="now()")

    team = relationship("Team", back_populates="team_statistics")

class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True)
    sofascore_id = Column(Integer, unique=True, nullable=False, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

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

    season = relationship("Season", back_populates="standings")
    team = relationship("Team", foreign_keys=[team_id])


# ================= CREATE SCHEMA =================
async def create_schema():
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    
    await engine.dispose()
    print(" Database schema created successfully!")


if __name__ == "__main__":
    asyncio.run(create_schema())