from sqlalchemy import select
from app.db.models import Standing, Team
from app.utils import get_or_create


async def ingest_standings(session, standings_data, season_id):

    for standing_table in standings_data.get("standings", []):
        group_name = standing_table["tournament"].get("groupName")
        
        for row in standing_table["rows"]:
            result = await session.execute(
                select(Team).where(Team.sofascore_id == row["team"]["id"])
            )
            team = result.scalar_one_or_none()
            
            if not team:
                print(f"Team {row['team']['name']} (ID: {row['team']['id']}) non trouvée")
                continue

             # Vérifier si standing existe déjà
            standing_query = select(Standing).where(
                Standing.season_id == season_id,
                Standing.team_id == team.id
            )
            standing_result = await session.execute(standing_query)
            existing = standing_result.scalar_one_or_none()
                
            if existing:
                continue

            standing_defaults = {
                "sofascore_id": row["id"],
                "season_id": season_id,
                "team_id": team.id,
                "group": group_name,
                "rank": row["position"],
                "total_matches": row["matches"],
                "wins": row["wins"],
                "draws": row["draws"],
                "losses": row["losses"],
                "goals_for": row["scoresFor"],
                "goals_against": row["scoresAgainst"],
                "goal_difference": row["scoresFor"] - row["scoresAgainst"],
                "points": row["points"],
            }
            
            await get_or_create(
                session, Standing, "sofascore_id",
                standing_defaults["sofascore_id"], standing_defaults
            )
            
            # print(f" {row['team']['name']} - {group_name} - Pos {row['position']}")