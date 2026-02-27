





    # ======================PLAYER INGESTION ========================
    
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.search import Search
from sofascore_wrapper.league import League
from sofascore_wrapper.team import Team as TeamWrapper
from sofascore_wrapper.match import Match
from pipeline._backups.copy_new_models import (
    League as LeagueModel, Season, Team, Fixture, Player, Lineup,
    TournamentType, MatchStatus
)


# Configuration de la base de données
DATABASE_URL = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_or_create(session: AsyncSession, model, unique_field: str, **kwargs):
    
    stmt = select(model).where(getattr(model, unique_field) == kwargs[unique_field])
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if instance is None:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
    
    return instance


async def ingest_players_from_squad(session: AsyncSession, api: SofascoreAPI, team_id: int, db_team_id: int):
    
    # print(f"Ingestion des joueurs pour l'équipe ID: {team_id}")
    
    team_wrapper = TeamWrapper(api, team_id)
    squad_data = await team_wrapper.squad()
    
    # if not squad_data or 'players' not in squad_data:
    #     print(f"Aucun joueur trouvé pour l'équipe {team_id}")
    #     return
    
    players_created = 0
    players_updated = 0
    
    for player_item in squad_data['players']:
        player_data = player_item.get('player', {})
        
        # if not player_data:
        #     continue
        
        sofascore_id = player_data.get('id')
        # if not sofascore_id:
        #     continue
        
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
        
        # Vérifier si le joueur existe déjà
        stmt = select(Player).where(Player.sofascore_id == sofascore_id)
        result = await session.execute(stmt)
        existing_player = result.scalar_one_or_none()
        
        if existing_player:
            # Mise à jour des informations
            for key, value in player_info.items():
                if value is not None:
                    setattr(existing_player, key, value)
            players_updated += 1
        else:
            # Création d'un nouveau joueur
            new_player = Player(**player_info)
            session.add(new_player)
            players_created += 1
    
    await session.flush()
    print(f"Joueurs créés: {players_created}, mis à jour: {players_updated}")


async def map_json_to_db(session: AsyncSession, api: SofascoreAPI, json_data: dict):
    
    for event in json_data["events"]:
        # Ingestion de la ligue
        # league_data = {
        #     'sofascore_id': json_data['id'],
        #     'name': json_data['name'],
        #     'slug': json_data['slug'],
        #     'tournament_type': TournamentType.CUP if 'cup' in json_data['name'].lower() else TournamentType.LEAGUE,
        # }
        
        # league = await get_or_create(session, LeagueModel, 'sofascore_id', **league_data)

        league_data = {
                "sofascore_id": event["tournament"]["uniqueTournament"]["id"],
                "name": event["tournament"]["uniqueTournament"]["name"],
                "slug": event["tournament"]["uniqueTournament"]["slug"],
                "type": TournamentType.AFCON,
                "country": event["tournament"]["uniqueTournament"]["category"]["name"],
                "logo_url": None,
            }
        league = await get_or_create(session, LeagueModel,
                                        league_data["sofascore_id"], **league_data)
        
        # Ingestion de la saison
        # season_info = json_data.get('season', {})
        # if season_info:
        #     season_data = {
        #         'league_id': league.id,
        #         'sofascore_id': season_info['id'],
        #         'name': season_info['name'],
        #         'year': season_info['year'],
        #         'start_date': None,
        #         'end_date': None,
        #     }
            
        #     season = await get_or_create(session, Season, 'sofascore_id', **season_data)

        season_data = {
            "sofascore_id": event["season"]["id"],
            "league_id": league.id,
            "year": event["season"]["year"],
            "name": event["season"]["name"],
            "current": True,
        }
        season = await get_or_create(session, Season,
                                     season_data["sofascore_id"], **season_data)
        
        # Ingestion des équipes
        # teams_data = json_data.get('teams', [])
        # for team_json in teams_data:
        #     team_data = {
        #         'sofascore_id': team_json['id'],
        #         'name': team_json['name'],
        #         'slug': team_json['slug'],
        #         'short_name': team_json.get('shortName'),
        #         'name_code': team_json.get('nameCode'),
        #         'country_code': team_json.get('country', {}).get('alpha2'),
        #         'flag_url': None,
        #     }
            
        for side in ["homeTeam", "awayTeam"]:
            t = event[side]
            
            # Récupérer le drapeau de l'équipe
            # team_flag_url = None
            # team_id = t["id"]
            # try:
            #     team_wrapper = TeamWrapper(api, team_id)
            #     team_flag_url = await team_wrapper.image()
            #     # print(f"✓ Drapeau récupéré pour {t['name']} (ID: {team_id}): {team_flag_url}")
            # except Exception as e:
            #     print(f"Erreur lors de la récupération du drapeau pour {t['name']} (ID: {team_id}): {str(e)}")
            
            team_data = {
                "sofascore_id": t["id"],
                "name": t["name"],
                "slug": t["slug"],
                "short_name": t.get("shortName"),
                "code": t.get("nameCode"),
                "country": t["country"]["name"],
                "national": t.get("national", True),
                "flag_url": None,
                "primary_color": t["teamColors"]["primary"],
                "secondary_color": t["teamColors"]["secondary"],
                # "raw_data": t,
            }

            # Récupération du drapeau de l'équipe
            try:
                team_wrapper = TeamWrapper(api, t['id'])
                flag_url = await team_wrapper.image()
                team_data['flag_url'] = flag_url
            except Exception as e:
                print(f"Erreur lors de la récupération du drapeau pour l'équipe {t['name']}: {e}")
            
            team = await get_or_create(session, Team, team_data['sofascore_id'], **team_data)
            
            # Ingestion des joueurs de cette équipe via squad()
            await ingest_players_from_squad(session, api, t['id'], team.id)
        
        # Ingestion des fixtures
        fixtures_data = json_data.get('events', [])
        for fixture_json in fixtures_data:
            home_team_id = fixture_json.get('homeTeam', {}).get('id')
            away_team_id = fixture_json.get('awayTeam', {}).get('id')
            
            # Récupération des IDs de base de données des équipes
            stmt_home = select(Team).where(Team.sofascore_id == home_team_id)
            result_home = await session.execute(stmt_home)
            home_team = result_home.scalar_one_or_none()
            
            stmt_away = select(Team).where(Team.sofascore_id == away_team_id)
            result_away = await session.execute(stmt_away)
            away_team = result_away.scalar_one_or_none()
            
            if not home_team or not away_team:
                continue
            
            # fixture_data = {
            #     'season_id': season.id,
            #     'sofascore_id': fixture_json['id'],
            #     'home_team_id': home_team.id,
            #     'away_team_id': away_team.id,
            #     'round_number': fixture_json.get('roundInfo', {}).get('round'),
            #     'match_date': datetime.fromtimestamp(fixture_json['startTimestamp']),
            #     'status': MatchStatus.FINISHED if fixture_json.get('status', {}).get('type') == 'finished' else MatchStatus.SCHEDULED,
            #     'home_score': fixture_json.get('homeScore', {}).get('current'),
            #     'away_score': fixture_json.get('awayScore', {}).get('current'),
            # }


            fixture_data = {
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
            
            await get_or_create(session, Fixture, fixtures_data['sofascore_id'], **fixture_data)
        
        await session.commit()


# async def ingest_lineups(session: AsyncSession, api: SofascoreAPI, fixture_id: int, db_fixture_id: int):
    
#     print(f"Ingestion des lineups pour le match ID: {fixture_id}")
    
#     match = Match(api, fixture_id)
#     lineups_data = await match.lineups()
    
#     if not lineups_data:
#         print(f"Aucune composition trouvée pour le match {fixture_id}")
#         return
    
#     # Traitement de l'équipe domicile
#     home_lineup = lineups_data.get('home', {})
#     if home_lineup:
#         formation = home_lineup.get('formation')
        
#         # Joueurs titulaires
#         for player_lineup in home_lineup.get('players', []):
#             player_data = player_lineup.get('player', {})
#             sofascore_player_id = player_data.get('id')
            
#             # Récupération du joueur depuis la base de données
#             stmt = select(Player).where(Player.sofascore_id == sofascore_player_id)
#             result = await session.execute(stmt)
#             db_player = result.scalar_one_or_none()
            
#             if not db_player:
#                 print(f"Joueur non trouvé en base: {player_data.get('name')} (ID: {sofascore_player_id})")
#                 continue
            
#             lineup_data = {
#                 'fixture_id': db_fixture_id,
#                 'player_id': db_player.id,
#                 'is_home_team': True,
#                 'is_starter': True,
#                 'formation': formation,
#                 'position': player_lineup.get('position'),
#                 'shirt_number': player_lineup.get('shirtNumber'),
#                 'rating': player_lineup.get('statistics', {}).get('rating'),
#                 'minutes_played': player_lineup.get('statistics', {}).get('minutesPlayed'),
#                 'is_captain': player_lineup.get('captain', False),
#             }
            
#             lineup = Lineup(**lineup_data)
#             session.add(lineup)
        
#         # Joueurs remplaçants
#         for player_lineup in home_lineup.get('substitutes', []):
#             player_data = player_lineup.get('player', {})
#             sofascore_player_id = player_data.get('id')
            
#             stmt = select(Player).where(Player.sofascore_id == sofascore_player_id)
#             result = await session.execute(stmt)
#             db_player = result.scalar_one_or_none()
            
#             if not db_player:
#                 print(f"Joueur remplaçant non trouvé en base: {player_data.get('name')} (ID: {sofascore_player_id})")
#                 continue
            
#             lineup_data = {
#                 'fixture_id': db_fixture_id,
#                 'player_id': db_player.id,
#                 'is_home_team': True,
#                 'is_starter': False,
#                 'formation': formation,
#                 'position': player_lineup.get('position'),
#                 'shirt_number': player_lineup.get('shirtNumber'),
#                 'rating': player_lineup.get('statistics', {}).get('rating'),
#                 'minutes_played': player_lineup.get('statistics', {}).get('minutesPlayed'),
#                 'is_captain': player_lineup.get('captain', False),
#             }
            
#             lineup = Lineup(**lineup_data)
#             session.add(lineup)
    
#     # Traitement de l'équipe extérieure
#     away_lineup = lineups_data.get('away', {})
#     if away_lineup:
#         formation = away_lineup.get('formation')
        
#         # Joueurs titulaires
#         for player_lineup in away_lineup.get('players', []):
#             player_data = player_lineup.get('player', {})
#             sofascore_player_id = player_data.get('id')
            
#             stmt = select(Player).where(Player.sofascore_id == sofascore_player_id)
#             result = await session.execute(stmt)
#             db_player = result.scalar_one_or_none()
            
#             if not db_player:
#                 print(f"Joueur non trouvé en base: {player_data.get('name')} (ID: {sofascore_player_id})")
#                 continue
            
#             lineup_data = {
#                 'fixture_id': db_fixture_id,
#                 'player_id': db_player.id,
#                 'is_home_team': False,
#                 'is_starter': True,
#                 'formation': formation,
#                 'position': player_lineup.get('position'),
#                 'shirt_number': player_lineup.get('shirtNumber'),
#                 'rating': player_lineup.get('statistics', {}).get('rating'),
#                 'minutes_played': player_lineup.get('statistics', {}).get('minutesPlayed'),
#                 'is_captain': player_lineup.get('captain', False),
#             }
            
#             lineup = Lineup(**lineup_data)
#             session.add(lineup)
        
#         # Joueurs remplaçants
#         for player_lineup in away_lineup.get('substitutes', []):
#             player_data = player_lineup.get('player', {})
#             sofascore_player_id = player_data.get('id')
            
#             stmt = select(Player).where(Player.sofascore_id == sofascore_player_id)
#             result = await session.execute(stmt)
#             db_player = result.scalar_one_or_none()
            
#             if not db_player:
#                 print(f"Joueur remplaçant non trouvé en base: {player_data.get('name')} (ID: {sofascore_player_id})")
#                 continue
            
#             lineup_data = {
#                 'fixture_id': db_fixture_id,
#                 'player_id': db_player.id,
#                 'is_home_team': False,
#                 'is_starter': False,
#                 'formation': formation,
#                 'position': player_lineup.get('position'),
#                 'shirt_number': player_lineup.get('shirtNumber'),
#                 'rating': player_lineup.get('statistics', {}).get('rating'),
#                 'minutes_played': player_lineup.get('statistics', {}).get('minutesPlayed'),
#                 'is_captain': player_lineup.get('captain', False),
#             }
            
#             lineup = Lineup(**lineup_data)
#             session.add(lineup)
    
#     await session.commit()


async def main():
    api = SofascoreAPI()

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

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Boucler sur tous les rounds
            for round_number in rounds_list:
                try:
                    match_can = await can_league.league_fixtures_per_round(
                        latest_can_season_id, round_number
                    )

                    # Insertion des fixtures
                    await map_json_to_db(session, api, match_can)
                    
                    # Récupérer toutes les équipes uniques du round
                    teams_in_round = set()
                    for event in match_can["events"]:
                        teams_in_round.add(event["homeTeam"]["id"])
                        teams_in_round.add(event["awayTeam"]["id"])
                    
                    # Pour chaque équipe, ingérer ses joueurs via squad()
                    for team_sofascore_id in teams_in_round:
                        # Récupérer l'ID DB de l'équipe
                        stmt = select(Team).where(Team.sofascore_id == team_sofascore_id)
                        result = await session.execute(stmt)
                        db_team = result.scalar_one_or_none()
                        
                        if db_team:
                            await ingest_players_from_squad(session, api, team_sofascore_id, db_team.id)
                    
                    # Pour chaque match du round, récupérer les lineups
                    for event in match_can["events"]:
                        stmt = select(Fixture).where(Fixture.sofascore_id == event["id"])
                        result = await session.execute(stmt)
                        db_fixture = result.scalar_one_or_none()
                        
                        # if db_fixture:
                        #     await ingest_lineups(session, api, event["id"], db_fixture.id)
                        #     print(f"✓ Lineups insérés pour match {event['id']}")

                except Exception as e:
                    print(f"✗ Erreur round {round_number}: {str(e)}")
                    continue

        await session.commit()

    await api.close()

if __name__ == "__main__":
    asyncio.run(main())

