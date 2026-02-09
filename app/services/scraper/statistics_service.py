from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import MatchStatistics, PlayerStatistics, TeamStatistics, Team, Player
from app.utils import get_or_create, get_team_by_sofascore_id


# ==================== MATCH STATISTICS ====================

STATS_MAPPING = {
    'ballPossession': 'ball_possession',
    'totalShotsOnGoal': 'total_shots',
    'shotsOnGoal': 'shots_on_goal',
    'shotsOffGoal': 'shots_off_goal',
    'blockedScoringAttempt': 'blocked_shots',
    'totalShotsInsideBox': 'shots_inside_box',
    'totalShotsOutsideBox': 'shots_outside_box',
    'fouls': 'fouls',
    'cornerKicks': 'corners',
    'offsides': 'offsides',
    'passes': 'passes',
    'accuratePasses': 'pass_accuracy',
    'totalTackle': 'tackles',
    'goalkeeperSaves': 'saves',
    'yellowCards': 'yellow_cards',
    'redCards': 'red_cards',
    'accurateCross': 'crosses',
    'throwIns': 'throw_ins',
    'totalClearance': 'clearances',
    'interceptionWon': 'interceptions',
}


async def ingest_match_statistics(session, fixture_id, home_team_sofascore_id, 
                                  away_team_sofascore_id, stats_data):
    
    if not stats_data or 'statistics' not in stats_data:
        return
    
    home_team_db_id, _ = await get_team_by_sofascore_id(session, Team, home_team_sofascore_id)
    away_team_db_id, _ = await get_team_by_sofascore_id(session, Team, away_team_sofascore_id)
    
    if not home_team_db_id or not away_team_db_id:
        print(f"Équipes introuvables pour le match {fixture_id}")
        return
    
    all_period_stats = next(
        (s for s in stats_data['statistics'] if s['period'] == 'ALL'), None
    )
    
    if not all_period_stats:
        print(f"Pas de stats 'ALL' pour le match {fixture_id}")
        return
    
    home_stats, away_stats = _extract_statistics(all_period_stats)
    
    await _save_team_statistics(session, fixture_id, home_team_db_id, home_stats)
    await _save_team_statistics(session, fixture_id, away_team_db_id, away_stats)


def _extract_statistics(all_period_stats):
    
    home_stats = {}
    away_stats = {}
    
    for group in all_period_stats.get('groups', []):
        for stat_item in group.get('statisticsItems', []):
            key = stat_item.get('key')
            
            if key in STATS_MAPPING:
                db_field = STATS_MAPPING[key]
                home_value = stat_item.get('homeValue')
                away_value = stat_item.get('awayValue')
                
                if key == 'accuratePasses' and 'passes' in home_stats:
                    home_stats['pass_accuracy'] = round(
                        (home_value / home_stats['passes']) * 100, 2
                    ) if home_stats['passes'] > 0 else 0
                    away_stats['pass_accuracy'] = round(
                        (away_value / away_stats['passes']) * 100, 2
                    ) if away_stats['passes'] > 0 else 0
                else:
                    home_stats[db_field] = home_value
                    away_stats[db_field] = away_value
            
            _process_percentage_stats(key, stat_item, home_stats, away_stats)
    
    return home_stats, away_stats


def _process_percentage_stats(key, stat_item, home_stats, away_stats):
    
    if key == 'accurateCross':
        home_total = stat_item.get('homeTotal', 0)
        away_total = stat_item.get('awayTotal', 0)
        home_stats['crosses'] = stat_item.get('homeValue', 0)
        away_stats['crosses'] = stat_item.get('awayValue', 0)
        home_stats['crosses_accuracy'] = round(
            (home_stats['crosses'] / home_total) * 100, 2
        ) if home_total > 0 else 0
        away_stats['crosses_accuracy'] = round(
            (away_stats['crosses'] / away_total) * 100, 2
        ) if away_total > 0 else 0
    
    elif key == 'dribblesPercentage':
        home_stats['dribbles'] = stat_item.get('homeValue', 0)
        away_stats['dribbles'] = stat_item.get('awayValue', 0)
        home_total = stat_item.get('homeTotal', 0)
        away_total = stat_item.get('awayTotal', 0)
        home_stats['dribble_success'] = round(
            (home_stats['dribbles'] / home_total) * 100, 2
        ) if home_total > 0 else 0
        away_stats['dribble_success'] = round(
            (away_stats['dribbles'] / away_total) * 100, 2
        ) if away_total > 0 else 0
    
    elif key == 'wonTacklePercent':
        home_won = stat_item.get('homeValue', 0)
        away_won = stat_item.get('awayValue', 0)
        home_total = stat_item.get('homeTotal', 0)
        away_total = stat_item.get('awayTotal', 0)
        home_stats['tackles_won'] = round(
            (home_won / home_total) * 100, 2
        ) if home_total > 0 else 0
        away_stats['tackles_won'] = round(
            (away_won / away_total) * 100, 2
        ) if away_total > 0 else 0
        home_stats['tackles_lost'] = round(
            ((home_total - home_won) / home_total) * 100, 2
        ) if home_total > 0 else 0
        away_stats['tackles_lost'] = round(
            ((away_total - away_won) / away_total) * 100, 2
        ) if away_total > 0 else 0
    
    elif key == 'aerialDuelsPercentage':
        home_stats['aerials_won'] = stat_item.get('homeValue', 0)
        away_stats['aerials_won'] = stat_item.get('awayValue', 0)
        home_total = stat_item.get('homeTotal', 0)
        away_total = stat_item.get('awayTotal', 0)
        home_stats['aerials_lost'] = home_total - home_stats['aerials_won']
        away_stats['aerials_lost'] = away_total - away_stats['aerials_won']


async def _save_team_statistics(session, fixture_id, team_db_id, stats):
    
    existing = await session.execute(
        MatchStatistics.__table__.select().where(
            MatchStatistics.fixture_id == fixture_id,
            MatchStatistics.team_id == team_db_id
        )
    )
    
    if not existing.first():
        stats_obj = MatchStatistics(
            fixture_id=fixture_id,
            team_id=team_db_id,
            **stats
        )
        session.add(stats_obj)
        await session.flush()


# ==================== PLAYER STATISTICS ====================

async def ingest_player_season_statistics(
    session: AsyncSession,
    player_id: int,
    league_id: int,
    season_id: int,
    stats_data: dict
) -> PlayerStatistics:
    
    stats = stats_data.get('statistics', {})
    
    stats_dict = {
        'player_id': player_id,
        'season_id': season_id,
        'league_id': league_id,
        'rating': stats.get('rating'),
        'appearances': stats.get('appearances') or stats.get('matchesStarted'),
        'minutes_played': stats.get('minutesPlayed'),
        'goals': stats.get('goals'),
        'assists': stats.get('assists'),
        'big_chances_created': stats.get('bigChancesCreated'),
        'big_chances_missed': stats.get('bigChancesMissed'),
        'total_shots': stats.get('totalShots'),
        'shots_on_target': stats.get('shotsOnTarget'),
        'shots_off_target': stats.get('shotsOffTarget'),
        'shots_from_inside_box': stats.get('shotsFromInsideTheBox'),
        'shots_from_outside_box': stats.get('shotsFromOutsideTheBox'),
        'goal_conversion_percentage': stats.get('goalConversionPercentage'),
        'total_passes': stats.get('totalPasses'),
        'accurate_passes': stats.get('accuratePasses'),
        'accurate_passes_percentage': stats.get('accuratePassesPercentage'),
        'key_passes': stats.get('keyPasses'),
        'accurate_crosses': stats.get('accurateCrosses'),
        'accurate_crosses_percentage': stats.get('accurateCrossesPercentage'),
        'accurate_long_balls': stats.get('accurateLongBalls'),
        'accurate_long_balls_percentage': stats.get('accurateLongBallsPercentage'),
        'total_duels_won': stats.get('totalDuelsWon'),
        'total_duels_won_percentage': stats.get('totalDuelsWonPercentage'),
        'ground_duels_won': stats.get('groundDuelsWon'),
        'ground_duels_won_percentage': stats.get('groundDuelsWonPercentage'),
        'aerial_duels_won': stats.get('aerialDuelsWon'),
        'aerial_duels_won_percentage': stats.get('aerialDuelsWonPercentage'),
        'tackles': stats.get('tackles'),
        'tackles_won': stats.get('tacklesWon'),
        'tackles_won_percentage': stats.get('tacklesWonPercentage'),
        'interceptions': stats.get('interceptions'),
        'clearances': stats.get('clearances'),
        'successful_dribbles': stats.get('successfulDribbles'),
        'successful_dribbles_percentage': stats.get('successfulDribblesPercentage'),
        'dribbled_past': stats.get('dribbledPast'),
        'yellow_cards': stats.get('yellowCards'),
        'red_cards': stats.get('redCards') or stats.get('directRedCards', 0),
        'fouls': stats.get('fouls'),
        'was_fouled': stats.get('wasFouled'),
        'saves': stats.get('saves'),
        'clean_sheet': stats.get('cleanSheet'),
        'goals_conceded': stats.get('goalsConceded'),
        'penalty_save': stats.get('penaltySave'),
        'penalty_goals': stats.get('penaltyGoals'),
        'penalties_taken': stats.get('penaltiesTaken'),
        'penalty_conversion': stats.get('penaltyConversion'),
        'touches': stats.get('touches'),
        'possession_lost': stats.get('possessionLost'),
        'offsides': stats.get('offsides'),
        'hit_woodwork': stats.get('hitWoodwork'),
        'own_goals': stats.get('ownGoals'),
    }
    
    query = select(PlayerStatistics).where(
        PlayerStatistics.player_id == player_id,
        PlayerStatistics.season_id == season_id,
        PlayerStatistics.league_id == league_id
    )
    result = await session.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        for key, value in stats_dict.items():
            if value is not None:
                setattr(existing, key, value)
        player_stats = existing
    else:
        player_stats = PlayerStatistics(**stats_dict)
        session.add(player_stats)
    
    return player_stats


async def ingest_all_players_statistics(
    session: AsyncSession,
    api,
    league_sofascore_id: int,
    season_sofascore_id: int,
    league_id: int,
    season_id: int
):
    from sofascore_wrapper.player import Player as PlayerAPI
    
    players_query = select(Player).where(Player.sofascore_id.isnot(None))
    result = await session.execute(players_query)
    players = result.scalars().all()
    
    print(f"\nIngestion stats pour {len(players)} joueurs...")
    
    count_success = 0
    count_skipped = 0
    
    for player in players:
        try:
            player_api = PlayerAPI(api, player.sofascore_id)
            stats_data = await player_api.league_stats(league_sofascore_id, season_sofascore_id)
            
            if stats_data and stats_data.get('statistics'):
                await ingest_player_season_statistics(
                    session, player.id, league_id, season_id, stats_data
                )
                count_success += 1
                if count_success % 100 == 0:
                    print(f"  {count_success} joueurs traités...")
            else:
                count_skipped += 1
                
        except Exception as e:
            count_skipped += 1
            continue
    
    print(f"Stats joueurs: {count_success} réussis, {count_skipped} ignorés")


# ==================== TEAM STATISTICS ====================

async def ingest_team_season_statistics(
    session: AsyncSession,
    team_id: int,
    league_id: int,
    season_id: int,
    stats_data: dict
) -> TeamStatistics:
    
    stats = stats_data.get('statistics', {})
    
    stats_dict = {
        'team_id': team_id,
        'season_id': season_id,
        'league_id': league_id,
        'matches': stats.get('matches'),
        'goals_scored': stats.get('goalsScored'),
        'goals_conceded': stats.get('goalsConceded'),
        'own_goals': stats.get('ownGoals'),
        'assists': stats.get('assists'),
        'shots': stats.get('shots'),
        'shots_on_target': stats.get('shotsOnTarget'),
        'shots_off_target': stats.get('shotsOffTarget'),
        'shots_from_inside_box': stats.get('shotsFromInsideTheBox'),
        'shots_from_outside_box': stats.get('shotsFromOutsideTheBox'),
        'blocked_scoring_attempt': stats.get('blockedScoringAttempt'),
        'big_chances': stats.get('bigChances'),
        'big_chances_created': stats.get('bigChancesCreated'),
        'big_chances_missed': stats.get('bigChancesMissed'),
        'hit_woodwork': stats.get('hitWoodwork'),
        'total_passes': stats.get('totalPasses'),
        'accurate_passes': stats.get('accuratePasses'),
        'accurate_passes_percentage': stats.get('accuratePassesPercentage'),
        'total_long_balls': stats.get('totalLongBalls'),
        'accurate_long_balls': stats.get('accurateLongBalls'),
        'accurate_long_balls_percentage': stats.get('accurateLongBallsPercentage'),
        'total_crosses': stats.get('totalCrosses'),
        'accurate_crosses': stats.get('accurateCrosses'),
        'accurate_crosses_percentage': stats.get('accurateCrossesPercentage'),
        'average_ball_possession': stats.get('averageBallPossession'),
        'tackles': stats.get('tackles'),
        'interceptions': stats.get('interceptions'),
        'clearances': stats.get('clearances'),
        'saves': stats.get('saves'),
        'clean_sheets': stats.get('cleanSheets'),
        'total_duels': stats.get('totalDuels'),
        'duels_won': stats.get('duelsWon'),
        'duels_won_percentage': stats.get('duelsWonPercentage'),
        'ground_duels_won': stats.get('groundDuelsWon'),
        'ground_duels_won_percentage': stats.get('groundDuelsWonPercentage'),
        'aerial_duels_won': stats.get('aerialDuelsWon'),
        'aerial_duels_won_percentage': stats.get('aerialDuelsWonPercentage'),
        'yellow_cards': stats.get('yellowCards'),
        'red_cards': stats.get('redCards'),
        'fouls': stats.get('fouls'),
        'corners': stats.get('corners'),
        'free_kicks': stats.get('freeKicks'),
        'successful_dribbles': stats.get('successfulDribbles'),
        'dribble_attempts': stats.get('dribbleAttempts'),
        'penalty_goals': stats.get('penaltyGoals'),
        'penalties_taken': stats.get('penaltiesTaken'),
        'penalties_commited': stats.get('penaltiesCommited'),
        'offsides': stats.get('offsides'),
        'possession_lost': stats.get('possessionLost'),
        'errors_leading_to_goal': stats.get('errorsLeadingToGoal'),
        'ball_recovery': stats.get('ballRecovery'),
        'avg_rating': stats.get('avgRating'),
    }
    
    query = select(TeamStatistics).where(
        TeamStatistics.team_id == team_id,
        TeamStatistics.season_id == season_id,
        TeamStatistics.league_id == league_id
    )
    result = await session.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        for key, value in stats_dict.items():
            if value is not None:
                setattr(existing, key, value)
        team_stats = existing
    else:
        team_stats = TeamStatistics(**stats_dict)
        session.add(team_stats)
    
    return team_stats


async def ingest_all_teams_statistics(
    session: AsyncSession,
    api,
    league_sofascore_id: int,
    season_sofascore_id: int,
    league_id: int,
    season_id: int
):
    from sofascore_wrapper.team import Team as TeamAPI
    
    teams_query = select(Team).where(Team.national == True)
    result = await session.execute(teams_query)
    teams = result.scalars().all()
    
    print(f"\nIngestion stats pour {len(teams)} équipes...")
    
    count_success = 0
    count_skipped = 0
    
    for team in teams:
        try:
            team_api = TeamAPI(api, team.sofascore_id)
            stats_data = await team_api.league_stats(league_sofascore_id, season_sofascore_id)
            
            if stats_data and stats_data.get('statistics'):
                await ingest_team_season_statistics(
                    session, team.id, league_id, season_id, stats_data
                )
                count_success += 1
                # print(f"  Stats {team.name}")
            else:
                count_skipped += 1
                
        except Exception as e:
            count_skipped += 1
            continue
    
    print(f"Stats équipes: {count_success} réussies, {count_skipped} ignorées")