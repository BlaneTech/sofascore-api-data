
from app.db.models import MatchStatistics, Team
from app.utils import get_or_create, get_team_by_sofascore_id


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
    
    # Récupérer les IDs DB des équipes
    home_team_db_id, _ = await get_team_by_sofascore_id(session, Team, home_team_sofascore_id)
    away_team_db_id, _ = await get_team_by_sofascore_id(session, Team, away_team_sofascore_id)
    
    if not home_team_db_id or not away_team_db_id:
        print(f"Équipes introuvables pour le match {fixture_id}")
        return
    
    # Chercher les stats
    all_period_stats = next(
        (s for s in stats_data['statistics'] if s['period'] == 'ALL'), None
    )
    
    if not all_period_stats:
        print(f"Pas de stats 'ALL' pour le match {fixture_id}")
        return
    
    # Extraire les stats pour home et away
    home_stats, away_stats = _extract_statistics(all_period_stats)
    
    # Créer les enregistrements
    await _save_team_statistics(session, fixture_id, home_team_db_id, home_stats)
    await _save_team_statistics(session, fixture_id, away_team_db_id, away_stats)


def _extract_statistics(all_period_stats):
    
    home_stats = {}
    away_stats = {}
    
    for group in all_period_stats.get('groups', []):
        for stat_item in group.get('statisticsItems', []):
            key = stat_item.get('key')
            
            # Stats simples
            if key in STATS_MAPPING:
                db_field = STATS_MAPPING[key]
                home_value = stat_item.get('homeValue')
                away_value = stat_item.get('awayValue')
                
                # Calcul spécial pour pass_accuracy
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
            
            # Stats avec pourcentages
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
    
    # Vérifier si existe déjà
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
