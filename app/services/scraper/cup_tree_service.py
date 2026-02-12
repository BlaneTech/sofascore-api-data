
from sofascore_wrapper.league import League
from sofascore_wrapper.match import Match
from app.db.models import Team
from app.services.scraper.team_service import ingest_team
from app.services.scraper.fixture_service import ingest_fixture_from_cup_tree
from app.services.scraper.lineup_service import ingest_lineups;
from app.services.scraper.statistics_service import ingest_match_statistics
from app.services.scraper.match_event_service import ingest_match_events
from app.utils import get_or_create


async def ingest_cup_tree_matches(session, api, season_id, league, season):
    
    try:
        can_league = League(api, league.sofascore_id)
        cup_tree_data = await can_league.cup_tree(season_id)
        
        if not cup_tree_data or 'cupTrees' not in cup_tree_data:
            print(" Pas de cup_tree disponible")
            return
        
        cup_tree = cup_tree_data['cupTrees'][0]
        
        for round_data in cup_tree.get('rounds', []):
            round_desc = round_data['description']
            
            for block in round_data.get('blocks', []):
                event_ids = block.get('events', [])
                
                if not event_ids:
                    continue
                
                event_id = event_ids[0]
                
                try:
                    await _process_cup_tree_match(
                        session, api, event_id, block, round_data, 
                        league, season
                    )
                except Exception as e:
                    print(f" Erreur match {event_id}: {str(e)}")
                    continue
        
        print(f" Phases finales insérées")
        
    except Exception as e:
        print(f"Erreur cup_tree: {str(e)}")
        import traceback
        traceback.print_exc()


async def _process_cup_tree_match(session, api, event_id, block, round_data, league, season):
    
    participants = block.get('participants', [])
    if len(participants) < 2:
        return
    
    # Récupérer ou créer les équipes
    home_team = await _get_or_create_team_from_participant(
        session, api, participants[0]
    )
    away_team = await _get_or_create_team_from_participant(
        session, api, participants[1]
    )
    
    # Créer le fixture
    fixture = await ingest_fixture_from_cup_tree(
        session, event_id, block, round_data,
        league.id, season.id, home_team.id, away_team.id
    )
    
    # Récupérer les lineups
    match_obj = Match(api, event_id)
    home_lineups = await match_obj.lineups_home()
    away_lineups = await match_obj.lineups_away()
    
    if home_lineups:
        await ingest_lineups(session, fixture.id, home_lineups, participants[0]['team']['id'])
    if away_lineups:
        await ingest_lineups(session, fixture.id, away_lineups, participants[1]['team']['id'])

    # Récupérer les statistiques
    match_stats = await match_obj.stats()
    if match_stats:
        await ingest_match_statistics(
            session, fixture.id,
            participants[0]['team']['id'],
            participants[1]['team']['id'],
            match_stats
        )

    # Récupérer les événements du match
    match_incidents = await match_obj.incidents()
    if match_incidents:
        await ingest_match_events(
            session, match_incidents, fixture.id,
            home_team.id, away_team.id
        )

async def _get_or_create_team_from_participant(session, api, participant):
    
    team_data = participant['team']
    
    team_defaults = {
        "sofascore_id": team_data['id'],
        "name": team_data['name'],
        "slug": team_data['slug'],
        "short_name": team_data.get('shortName'),
        "code": team_data.get('nameCode'),
        "country": team_data['name'],
        "national": True,
        "primary_color": team_data['teamColors']['primary'],
        "secondary_color": team_data['teamColors']['secondary'],
    }
    
    return await get_or_create(
        session, Team, "sofascore_id",
        team_defaults["sofascore_id"], team_defaults
    )
