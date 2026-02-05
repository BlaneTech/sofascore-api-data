import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.search import Search
from sofascore_wrapper.league import League
from sofascore_wrapper.team import Team as TeamWrapper
from sofascore_wrapper.match import Match

from new_models import (
    League as LeagueModel, Season, Team,
    Fixture, TournamentType, MatchStatus, Player, Lineup, MatchStatistics
)

DATABASE_URL = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_or_create(session, model, unique_field, value, defaults):
    # Get or create an object by unique field
    result = await session.execute(
        model.__table__.select().where(getattr(model, unique_field) == value)
    )
    row = result.first()
    if row:
        return await session.get(model, row[0])
    obj = model(**defaults)
    session.add(obj)
    await session.flush()
    return obj

async def map_json_to_db(json_data, api, session):
    for event in json_data["events"]:
        # League
        league_defaults = {
            "sofascore_id": event["tournament"]["uniqueTournament"]["id"],
            "name": event["tournament"]["uniqueTournament"]["name"],
            "slug": event["tournament"]["uniqueTournament"]["slug"],
            "type": TournamentType.AFCON,
            "country": event["tournament"]["uniqueTournament"]["category"]["name"],
            "logo_url": None,
        }
        league = await get_or_create(session, LeagueModel, "sofascore_id",
                                     league_defaults["sofascore_id"], league_defaults)

        # Season
        season_defaults = {
            "sofascore_id": event["season"]["id"],
            "league_id": league.id,
            "year": event["season"]["year"],
            "name": event["season"]["name"],
            "current": True,
        }
        season = await get_or_create(session, Season, "sofascore_id",
                                     season_defaults["sofascore_id"], season_defaults)

        # Teams
        for side in ["homeTeam", "awayTeam"]:
            t = event[side]
            
            # Récupérer le drapeau de l'équipe
            team_flag_url = None
            team_id = t["id"]
            try:
                team_wrapper = TeamWrapper(api, team_id)
                team_flag_url = await team_wrapper.image()
                # print(f"✓ Drapeau récupéré pour {t['name']} (ID: {team_id}): {team_flag_url}")
            except Exception as e:
                print(f"Erreur lors de la récupération du drapeau pour {t['name']} (ID: {team_id}): {str(e)}")
            
            team_defaults = {
                "sofascore_id": t["id"],
                "name": t["name"],
                "slug": t["slug"],
                "short_name": t.get("shortName"),
                "code": t.get("nameCode"),
                "country": t["country"]["name"],
                "national": t.get("national", True),
                "logo_url": team_flag_url,
                "primary_color": t["teamColors"]["primary"],
                "secondary_color": t["teamColors"]["secondary"],
                # "raw_data": t,
            }
            team = await get_or_create(session, Team, "sofascore_id",
                                       team_defaults["sofascore_id"], team_defaults)
            if side == "homeTeam":
                home_team = team
            else:
                away_team = team

            # player
            try:
                team_wrapper = TeamWrapper(api, team_id)
                squad_data = await team_wrapper.squad()
                
                # Vérification que squad_data contient bien 'players'
                if not squad_data or 'players' not in squad_data:
                    print(f"Pas de données squad pour {t['name']}")
                    continue
                
                for player_item in squad_data.get('players', []):
                    player_data = player_item.get('player', {})
                    
                    if not player_data or 'id' not in player_data:
                        continue
                    
                    sofascore_id = player_data.get('id')
                    
                    # Extraction des données du joueur
                    player_defauls = {
                        'sofascore_id': sofascore_id,
                        'team_id': team.id,
                        'name': player_data.get('name'),  # ✅ Déjà corrigé
                        'first_name': player_data.get('firstName'),
                        'last_name': player_data.get('lastName'),
                        'slug': player_data.get('slug'),
                        'short_name': player_data.get('shortName'),
                        'position': player_data.get('position'),
                        # 'jersey_number': player_data.get('jerseyNumber') or player_data.get('shirtNumber'),
                        'jersey_number': int(player_data.get('jerseyNumber') or player_data.get('shirtNumber') or 0) if (player_data.get('jerseyNumber') or player_data.get('shirtNumber')) else None,
                        'height': player_data.get('height'),
                        'date_of_birth': None,
                        'preferred_foot': player_data.get('preferredFoot'), 
                        'photo_url': None,
                    }
                    
                    # Conversion de la date de naissance
                    dob_str = player_data.get('dateOfBirth')
                    if dob_str:
                        try:
                            player_defauls['date_of_birth'] = datetime.fromisoformat(dob_str.replace('Z', '+00:00')).date()
                        except:
                            pass

                    await get_or_create(session, Player, "sofascore_id",
                                        player_defauls["sofascore_id"], player_defauls)

            except Exception as e:
                print(f"⚠ Erreur ing   estion joueurs pour {t['name']}: {str(e)}")
                # import traceback
                # traceback.print_exc()
                


        # Fixture
        fixture_defaults = {
            "sofascore_id": event["id"],
            "league_id": league.id,
            "season_id": season.id,
            "home_team_id": home_team.id,
            "away_team_id": away_team.id,
            "date": datetime.fromtimestamp(event["startTimestamp"]),
            "timestamp": event["startTimestamp"],
            "round": event["roundInfo"]["round"],
            "round_name": f"Round {event['roundInfo']['round']}",
            "group_name": event["tournament"].get("groupName"),
            "group_sign": event["tournament"].get("groupSign"),
            "status": MatchStatus(event["status"]["type"]),
            "home_score": event["homeScore"]["current"],
            "away_score": event["awayScore"]["current"],
            "home_score_period1": event["homeScore"]["period1"],
            "home_score_period2": event["homeScore"]["period2"],
            "home_score_normaltime": event["homeScore"]["normaltime"],
            "away_score_period1": event["awayScore"]["period1"],
            "away_score_period2": event["awayScore"]["period2"],
            "away_score_normaltime": event["awayScore"]["normaltime"],
            # "raw_data": event,
        }
        await get_or_create(session, Fixture, "sofascore_id",
                            fixture_defaults["sofascore_id"], fixture_defaults)
        
# =====================CUP TREE INGESTION ========================
async def ingest_cup_tree_matches(session, api, season_id, league, season):

    try:
        can_league = League(api, league.sofascore_id)
        cup_tree_data = await can_league.cup_tree(season_id)
        
        if not cup_tree_data or 'cupTrees' not in cup_tree_data:
            print("⚠ Pas de cup_tree disponible")
            return
        
        cup_tree = cup_tree_data['cupTrees'][0]
        
        # Parcourir tous les rounds (1/8, 1/4, 1/2, finale)
        for round_data in cup_tree.get('rounds', []):
            round_desc = round_data['description']
            
            
            # Parcourir les blocks (matchs)
            for block in round_data.get('blocks', []):
                # Récupérer l'event_id
                event_ids = block.get('events', [])
                
                if not event_ids:
                    continue
                
                event_id = event_ids[0]
                
                # Récupérer les détails du match via l'API
                try:
                    match_obj = Match(api, event_id)
                    
                    # Récupérer les participants
                    participants = block.get('participants', [])
                    if len(participants) < 2:
                        continue
                    
                    home_team_sofascore_id = participants[0]['team']['id']
                    away_team_sofascore_id = participants[1]['team']['id']
                    
                    # Récupérer ou créer les équipes
                    home_team = await get_or_create(
                        session, Team, "sofascore_id", home_team_sofascore_id,
                        {
                            "sofascore_id": home_team_sofascore_id,
                            "name": participants[0]['team']['name'],
                            "slug": participants[0]['team']['slug'],
                            "short_name": participants[0]['team'].get('shortName'),
                            "code": participants[0]['team'].get('nameCode'),
                            "country": participants[0]['team']['name'],  # Adapter si nécessaire
                            "national": True,
                            "primary_color": participants[0]['team']['teamColors']['primary'],
                            "secondary_color": participants[0]['team']['teamColors']['secondary'],
                        }
                    )
                    
                    away_team = await get_or_create(
                        session, Team, "sofascore_id", away_team_sofascore_id,
                        {
                            "sofascore_id": away_team_sofascore_id,
                            "name": participants[1]['team']['name'],
                            "slug": participants[1]['team']['slug'],
                            "short_name": participants[1]['team'].get('shortName'),
                            "code": participants[1]['team'].get('nameCode'),
                            "country": participants[1]['team']['name'],
                            "national": True,
                            "primary_color": participants[1]['team']['teamColors']['primary'],
                            "secondary_color": participants[1]['team']['teamColors']['secondary'],
                        }
                    )
                    
                    # Créer le fixture
                    fixture_defaults = {
                        "sofascore_id": event_id,
                        "league_id": league.id,
                        "season_id": season.id,
                        "home_team_id": home_team.id,
                        "away_team_id": away_team.id,
                        "date": datetime.fromtimestamp(block['seriesStartDateTimestamp']),
                        "timestamp": block['seriesStartDateTimestamp'],
                        "round": round_data['order'],  # Ordre du round
                        "round_name": round_desc,  # "1/8", "Quarterfinals", etc.
                        "status": MatchStatus.FINISHED if block.get('finished') else MatchStatus.NOT_STARTED,
                        "home_score": int(block.get('homeTeamScore', 0).split()[0]) if block.get('homeTeamScore') else None,
                        "away_score": int(block.get('awayTeamScore', 0).split()[0]) if block.get('awayTeamScore') else None,
                    }
                    
                    fixture = await get_or_create(
                        session, Fixture, "sofascore_id",
                        event_id, fixture_defaults
                    )
                    
                    # Récupérer les lineups
                    home_lineups = await match_obj.lineups_home()
                    away_lineups = await match_obj.lineups_away()
                    
                    if home_lineups:
                        await ingest_lineups(session, fixture.id, home_lineups, home_team_sofascore_id)
                    if away_lineups:
                        await ingest_lineups(session, fixture.id, away_lineups, away_team_sofascore_id)
                    
                    # print(f"  ✓ Match {event_id} ({round_desc}) inséré")
                    
                except Exception as e:
                    print(f"  ✗ Erreur match {event_id}: {str(e)}")
                    continue
        
        print(f"Phases finales insérées")
        
    except Exception as e:
        print(f"✗ Erreur cup_tree: {str(e)}")
        import traceback
        traceback.print_exc()


# =====================PLAYER INGESTION ========================

async def ingest_players_from_squad(session: AsyncSession, api: SofascoreAPI, team_id: int, db_team_id: int):
    
    # print(f"Ingestion des joueurs pour l'équipe ID: {team_id}")
    team_wrapper = TeamWrapper(api, team_id)
    squad_data = await team_wrapper.squad()
    
    players_created = 0
    players_updated = 0
    
    for player_item in squad_data['players']:
        player_data = player_item.get('player', {})
        
        sofascore_id = player_data.get('id')

        # Extraction des données du joueur
        player_info = {
            'sofascore_id': sofascore_id,
            'team_id': db_team_id,
            'name': player_data.get('name'),
            'first_name': player_data.get('firstName'),
            'last_name': player_data.get('lastName'),
            'slug': player_data.get('slug'),
            'short_name': player_data.get('shortName'),
            'position': player_data.get('position'),
            'jersey_number': player_data.get('jerseyNumber') or player_data.get('shirtNumber'),
            'height': player_data.get('height'),
            'date_of_birth': None,
            'preferred_foot': player_data.get('preferredFoot'),
            'country_code': player_data.get('country', {}).get('alpha2') if player_data.get('country') else None,
            'nationality': player_data.get('country', {}).get('name') if player_data.get('country') else None,
        }
        
        # Conversion de la date de naissance
        dob_str = player_data.get('dateOfBirth')
        if dob_str:
            try:
                player_info['date_of_birth'] = datetime.fromisoformat(dob_str.replace('Z', '+00:00')).date()
            except:
                pass

# =====================LINEUPS INGESTION ========================
async def ingest_lineups(session, fixture_id, lineup_data, team_sofascore_id=None):
    # Récupérer l'équipe par son sofascore_id
    result = await session.execute(
        Team.__table__.select().where(Team.sofascore_id == team_sofascore_id)
    )
    team_row = result.first()
    if not team_row:
        print(f"⚠ Équipe {team_sofascore_id} introuvable")
        return
    
    team_db_id = team_row[0] 

    # Fonction interne pour insérer un joueur
    async def insert_player_lineup(player_block, is_substitute=False):
        p = player_block["player"]

        player_defaults = {
            "sofascore_id": p["id"],
            "name": p["name"],
            "slug": p.get("slug"),
            "short_name": p.get("shortName"),
            "first_name": p.get("firstName"),
            "last_name": p.get("lastName"),
            "position": p.get("position"),
            "jersey_number": int(p.get("jerseyNumber")) if p.get("jerseyNumber") else None,
            "height": p.get("height"),
        }
        player = await get_or_create(session, Player, "sofascore_id",
                                     player_defaults["sofascore_id"], player_defaults)

        lineup_defaults = {
            "fixture_id": fixture_id,
            "team_id": team_db_id,
            "player_id": player.id,
            "formation": lineup_data.get("formation"),
            "position": player_block.get("position"),
            "starter": not is_substitute,
            "rating": player_block.get("statistics", {}).get("rating"),
            "minutes_played": player_block.get("statistics", {}).get("minutesPlayed"),
            "captain": player_block.get("captain", False),
            "substitute": is_substitute,
        }
        await get_or_create(session, Lineup, 
                            "player_id", lineup_defaults["player_id"], lineup_defaults)

    # Starters
    for starter in lineup_data.get("starters", []):
        await insert_player_lineup(starter, is_substitute=False)

    # Substitutes
    for sub in lineup_data.get("substitutes", []):
        await insert_player_lineup(sub, is_substitute=True)

# =====================MATCH STATISTICS INGESTION ========================
async def ingest_match_statistics(session, fixture_id, home_team_sofascore_id, away_team_sofascore_id, stats_data):
    
    if not stats_data or 'statistics' not in stats_data:
        return
    
    # Récupérer les IDs DB des équipes
    home_team_result = await session.execute(
        Team.__table__.select().where(Team.sofascore_id == home_team_sofascore_id)
    )
    home_team_row = home_team_result.first()
    if not home_team_row:
        print(f"⚠ Équipe home {home_team_sofascore_id} introuvable")
        return
    home_team_db_id = home_team_row[0]
    
    away_team_result = await session.execute(
        Team.__table__.select().where(Team.sofascore_id == away_team_sofascore_id)
    )
    away_team_row = away_team_result.first()
    if not away_team_row:
        print(f"⚠ Équipe away {away_team_sofascore_id} introuvable")
        return
    away_team_db_id = away_team_row[0]
    
    # Chercher les stats de la période
    all_period_stats = next((s for s in stats_data['statistics'] if s['period'] == 'ALL'), None)
    
    if not all_period_stats:
        print(f"⚠ Pas de stats 'ALL' pour le match {fixture_id}")
        return
    
    # Créer un dictionnaire pour mapper les clés API vers les champs DB
    stats_mapping = {
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
        'accuratePasses': 'pass_accuracy',  # Note: c'est le nombre, pas le %
        'totalTackle': 'tackles',
        'goalkeeperSaves': 'saves',
        'yellowCards': 'yellow_cards',
        'redCards': 'red_cards',
        'accurateCross': 'crosses',
        'throwIns': 'throw_ins',
        'totalClearance': 'clearances',
        'interceptionWon': 'interceptions',
    }
    
    # Initialiser les dictionnaires pour home et away
    home_stats = {}
    away_stats = {}
    
    # Parcourir tous les groupes de stats
    for group in all_period_stats.get('groups', []):
        for stat_item in group.get('statisticsItems', []):
            key = stat_item.get('key')
            
            if key in stats_mapping:
                db_field = stats_mapping[key]
                home_value = stat_item.get('homeValue')
                away_value = stat_item.get('awayValue')
                
                # Conversion spéciale pour le pass_accuracy (calculer le %)
                if key == 'accuratePasses' and 'passes' in home_stats:
                    home_stats['pass_accuracy'] = round((home_value / home_stats['passes']) * 100, 2) if home_stats['passes'] > 0 else 0
                    away_stats['pass_accuracy'] = round((away_value / away_stats['passes']) * 100, 2) if away_stats['passes'] > 0 else 0
                else:
                    home_stats[db_field] = home_value
                    away_stats[db_field] = away_value
            
            # Cas spéciaux avec des calculs
            if key == 'accurateCross':
                home_total = stat_item.get('homeTotal', 0)
                away_total = stat_item.get('awayTotal', 0)
                home_stats['crosses'] = stat_item.get('homeValue', 0)
                away_stats['crosses'] = stat_item.get('awayValue', 0)
                home_stats['crosses_accuracy'] = round((home_stats['crosses'] / home_total) * 100, 2) if home_total > 0 else 0
                away_stats['crosses_accuracy'] = round((away_stats['crosses'] / away_total) * 100, 2) if away_total > 0 else 0
            
            if key == 'dribblesPercentage':
                home_stats['dribbles'] = stat_item.get('homeValue', 0)
                away_stats['dribbles'] = stat_item.get('awayValue', 0)
                home_total = stat_item.get('homeTotal', 0)
                away_total = stat_item.get('awayTotal', 0)
                home_stats['dribble_success'] = round((home_stats['dribbles'] / home_total) * 100, 2) if home_total > 0 else 0
                away_stats['dribble_success'] = round((away_stats['dribbles'] / away_total) * 100, 2) if away_total > 0 else 0
            
            if key == 'wonTacklePercent':
                home_won = stat_item.get('homeValue', 0)
                away_won = stat_item.get('awayValue', 0)
                home_total = stat_item.get('homeTotal', 0)
                away_total = stat_item.get('awayTotal', 0)
                home_stats['tackles_won'] = round((home_won / home_total) * 100, 2) if home_total > 0 else 0
                away_stats['tackles_won'] = round((away_won / away_total) * 100, 2) if away_total > 0 else 0
                home_stats['tackles_lost'] = round(((home_total - home_won) / home_total) * 100, 2) if home_total > 0 else 0
                away_stats['tackles_lost'] = round(((away_total - away_won) / away_total) * 100, 2) if away_total > 0 else 0
            
            if key == 'aerialDuelsPercentage':
                home_stats['aerials_won'] = stat_item.get('homeValue', 0)
                away_stats['aerials_won'] = stat_item.get('awayValue', 0)
                home_total = stat_item.get('homeTotal', 0)
                away_total = stat_item.get('awayTotal', 0)
                home_stats['aerials_lost'] = home_total - home_stats['aerials_won']
                away_stats['aerials_lost'] = away_total - away_stats['aerials_won']
    
    # Créer les enregistrements pour home team
    home_match_stats = {
        'fixture_id': fixture_id,
        'team_id': home_team_db_id,
        **home_stats
    }
    
    await get_or_create(
        session, MatchStatistics, 
        'fixture_id', fixture_id,
        home_match_stats,
    )
    
    # Créer les enregistrements pour away team
    away_match_stats = {
        'fixture_id': fixture_id,
        'team_id': away_team_db_id,
        **away_stats
    }
    
    # Utiliser un identifiant unique composite
    # Vérifier si existe déjà
    existing_away = await session.execute(
        MatchStatistics.__table__.select().where(
            MatchStatistics.fixture_id == fixture_id,
            MatchStatistics.team_id == away_team_db_id
        )
    )
    
    if not existing_away.first():
        away_obj = MatchStatistics(**away_match_stats)
        session.add(away_obj)
        await session.flush()

# =====================MAIN INGESTION PIPELINE ========================
async def main():
    api = SofascoreAPI()

    try:
        # Chercher la compétition CAN
        search = Search(api, search_string="Africa Cup of Nations")
        competition = await search.search_all()
        can_id = competition['results'][0]['entity']['id']

        # Récupérer saisons
        can_league = League(api, can_id)
        can_seasons = await can_league.get_seasons()
        latest_can_season_id = can_seasons[0].get('id') if can_seasons else None

        # Récupérer tous les rounds
        can_rounds = await can_league.rounds(latest_can_season_id)
        rounds_list = [r['round'] for r in can_rounds['rounds']]

        async with async_session() as session:
            async with session.begin():
                #PHASE DE GROUPES
                league_obj = None
                season_obj = None
                
                for round_number in rounds_list:
                    try:
                        match_can = await can_league.league_fixtures_per_round(
                            latest_can_season_id, round_number
                        )

                        # Insertion des fixtures
                        await map_json_to_db(match_can, api, session)

                        # Sauvegarder league et season pour plus tard
                        if not league_obj and match_can["events"]:
                            event = match_can["events"][0]
                            league_obj = await get_or_create(
                                session, LeagueModel, "sofascore_id",
                                event["tournament"]["uniqueTournament"]["id"],
                                {"sofascore_id": event["tournament"]["uniqueTournament"]["id"]}
                            )
                            season_obj = await get_or_create(
                                session, Season, "sofascore_id",
                                event["season"]["id"],
                                {"sofascore_id": event["season"]["id"]}
                            )

                        # Pour chaque match du round, récupérer les lineups
                        for event in match_can["events"]:
                            try:
                                fixture = await get_or_create(
                                    session, Fixture, "sofascore_id", event["id"],
                                    {"sofascore_id": event["id"]}
                                )

                                match_obj = Match(api, event["id"])
                                home_lineups = await match_obj.lineups_home()
                                away_lineups = await match_obj.lineups_away()

                                if home_lineups:
                                    await ingest_lineups(session, fixture.id, home_lineups, event["homeTeam"]["id"])
                                if away_lineups:
                                    await ingest_lineups(session, fixture.id, away_lineups, event["awayTeam"]["id"])

                                print(f"✓ Lineups insérés pour match {event['id']}")
                            except Exception as e:
                                print(f"✗ Erreur lineups match {event['id']}: {str(e)}")
                                continue

                            # Récupérer et insérer les statistiques du match
                            try:
                                match_stats = await match_obj.stats()
                                
                                if match_stats:
                                    await ingest_match_statistics(
                                        session, 
                                        fixture.id, 
                                        event["homeTeam"]["id"],
                                        event["awayTeam"]["id"],
                                        match_stats
                                    )
                                    print(f"✓ Statistiques insérées pour match {event['id']}")
                            except Exception as e:
                                print(f"✗ Erreur stats match {event['id']}: {str(e)}")

                    except Exception as e:
                        print(f"✗ Erreur round {round_number}: {str(e)}")
                        continue

                # PHASES FINALES (CUP TREE)
                if league_obj and season_obj:
                    await ingest_cup_tree_matches(
                        session, api, latest_can_season_id, 
                        league_obj, season_obj
                    )
                else:
                    print("⚠ Impossible de récupérer league/season pour cup_tree")

            await session.commit()
            print("\n✅ Ingestion terminée avec succès!")

    except Exception as e:
        print(f"❌ Erreur fatale: {str(e)}")
        # import traceback
        # traceback.print_exc()
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())