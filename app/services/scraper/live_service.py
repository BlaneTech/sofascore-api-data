import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import asyncio

import redis.asyncio as redis
from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.match import Match

from app.db.database import AsyncSessionLocal
from app.services.scraper.match_event_service import ingest_match_events
from app.services.scraper.statistics_service import ingest_match_statistics
from app.db.models import Fixture
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


class LiveMatchService:

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.api = SofascoreAPI()
        self.active_matches = set()

    async def close(self):
        await self.redis.close()
        await self.api.close()

    # DÉTECTION DES MATCHS LIVE
    async def get_live_fixtures(self, db: AsyncSession = None) -> List[int]:
        now = datetime.utcnow()
        one_hour_before = now - timedelta(hours=1)
        three_hours_after = now + timedelta(hours=3)

        fixture_ids = set()
        if db:
            # Utilise la session FastAPI existante
            result = await db.execute(
                select(Fixture).options(
                    selectinload(Fixture.home_team),
                    selectinload(Fixture.away_team),
                    selectinload(Fixture.league),
                ).where(Fixture.date.between(one_hour_before, three_hours_after))
            )
            fixture_ids.update([row[0] for row in result.all()])

        # Sofascore live_games
        try:
            match_obj = Match(self.api, 0)
            live_games = await match_obj.live_games()
            if live_games and 'events' in live_games:
                fixture_ids.update({event['id'] for event in live_games['events']})
        except Exception:
            pass

        return list(fixture_ids)

    # PARSING DES DONNÉES SOFASCORE
    def _parse_match_info(self, match_details: Dict) -> Dict:
       
        event = match_details.get("event", {})

        # Scores
        home_score = event.get("homeScore", {})
        away_score = event.get("awayScore", {})

        minute = None
        time_info = event.get("time", {})
        period_start = time_info.get("currentPeriodStartTimestamp")
        initial = time_info.get("initial", 0)

        if period_start:
            elapsed = int((datetime.utcnow().timestamp() - period_start))
            minute = int((initial + elapsed) / 60)

        return {
            "home_team": {
                "id": event.get("homeTeam", {}).get("id"),
                "name": event.get("homeTeam", {}).get("name"),
                "short_name": event.get("homeTeam", {}).get("shortName"),
            },
            "away_team": {
                "id": event.get("awayTeam", {}).get("id"),
                "name": event.get("awayTeam", {}).get("name"),
                "short_name": event.get("awayTeam", {}).get("shortName"),
            },
            "score": {
                "home": home_score.get("current", 0),
                "away": away_score.get("current", 0),
                "home_period1": home_score.get("period1"),
                "away_period1": away_score.get("period1"),
                "home_period2": home_score.get("period2"),
                "away_period2": away_score.get("period2"),
            },
            "minute": minute,
            "status_description": event.get("status", {}).get("description"),
            "tournament": event.get("tournament", {}).get("name"),
            "start_timestamp": event.get("startTimestamp"),
        }

    def _parse_incidents(self, raw_incidents: Dict) -> Dict:
        
        if not raw_incidents:
            return {"events": [], "periods": []}

        incidents_list = raw_incidents.get("incidents", [])

        events = [] 
        periods = []

        for inc in incidents_list:
            inc_type = inc.get("incidentType")

            if inc_type == "period":
                periods.append({
                    "text": inc.get("text"),
                    "time": inc.get("time"),
                    "home_score": inc.get("homeScore"),
                    "away_score": inc.get("awayScore"),
                    "is_live": inc.get("isLive", False),
                })

            elif inc_type == "goal":
                events.append({
                    "type": "goal",
                    "time": inc.get("time"),
                    "added_time": inc.get("addedTime"),
                    "team": "home" if inc.get("isHome") else "away",
                    "player": inc.get("player", {}).get("name"),
                    "assist": inc.get("assist1", {}).get("name") if inc.get("assist1") else None,
                    "goal_type": inc.get("incidentClass"),
                    "home_score": inc.get("homeScore"),
                    "away_score": inc.get("awayScore"),
                    "description": inc.get("description"),
                })

            elif inc_type == "card":
                events.append({
                    "type": "card",
                    "time": inc.get("time"),
                    "added_time": inc.get("addedTime"),
                    "team": "home" if inc.get("isHome") else "away",
                    "player": inc.get("player", {}).get("name"),
                    "card_type": inc.get("incidentClass"),
                    "reason": inc.get("reason"),
                })

            elif inc_type == "substitution":
                events.append({
                    "type": "substitution",
                    "time": inc.get("time"),
                    "team": "home" if inc.get("isHome") else "away",
                    "player_in": inc.get("playerIn", {}).get("name"),
                    "player_out": inc.get("playerOut", {}).get("name"),
                })

            elif inc_type == "injuryTime":
                events.append({
                    "type": "injury_time",
                    "time": inc.get("time"),
                    "added_time": inc.get("length"),
                })

            elif inc_type == "varDecision":
                events.append({
                    "type": "var",
                    "time": inc.get("time"),
                    "team": "home" if inc.get("isHome") else "away",
                    "decision": inc.get("incidentClass"),
                    "reason": inc.get("reason"),
                })

        return {
            "events": events,
            "periods": periods,
        }

    def _parse_stats(self, raw_stats: Dict) -> Dict:

        if not raw_stats:
            return {}

        statistics = raw_stats.get("statistics", [])
        parsed = {}

        for period_data in statistics:
            period = period_data.get("period", "ALL").lower()
            parsed[period] = {}

            for group in period_data.get("groups", []):
                group_name = group.get("groupName", "").lower().replace(" ", "_")
                parsed[period][group_name] = {}

                for item in group.get("statisticsItems", []):
                    key = item.get("key")
                    if not key:
                        continue
                    parsed[period][group_name][key] = {
                        "name": item.get("name"),
                        "home": item.get("homeValue"),
                        "away": item.get("awayValue"),
                        "home_display": item.get("home"),
                        "away_display": item.get("away"),
                    }

        return parsed

    # FETCH DONNÉES LIVE
    async def fetch_live_data(self, fixture_id: int) -> Optional[Dict]:

        match = Match(self.api, fixture_id)

        try:
            match_details = await match.get_match()
            status = match_details.get("event", {}).get("status", {}).get("type", "notstarted")

            live_data = {
                "fixture_id": fixture_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "match_info": self._parse_match_info(match_details),
                "incidents": None,
                "stats": None,
                "lineups": None,
            }

            # Incidents disponibles
            if status in ["inprogress", "finished"]:
                try:
                    raw_incidents = await match.incidents()
                    live_data["incidents"] = self._parse_incidents(raw_incidents)
                except Exception:
                    live_data["incidents"] = None

                try:
                    raw_stats = await match.stats()
                    live_data["stats"] = self._parse_stats(raw_stats)
                except Exception:
                    live_data["stats"] = None

            # Lineups disponibles 1h avant
            try:
                home_lineups = await match.lineups_home()
                away_lineups = await match.lineups_away()
                if home_lineups or away_lineups:
                    live_data["lineups"] = {
                        "home": home_lineups or {},
                        "away": away_lineups or {},
                    }
            except Exception:
                live_data["lineups"] = None

            return live_data

        except Exception:
            return None

    # CACHE REDIS
    async def cache_live_data(self, fixture_id: int, data: Dict):
        key = f"live:fixture:{fixture_id}"
        await self.redis.setex(key, 120, json.dumps(data))

    async def get_cached_live_data(self, fixture_id: int) -> Optional[Dict]:
        key = f"live:fixture:{fixture_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    # UPDATE & PERSISTANCE
    async def update_live_match(self, fixture_id: int) -> Optional[Dict]:
        try:
            live_data = await self.fetch_live_data(fixture_id)
            if not live_data:
                return None
            await self.cache_live_data(fixture_id, live_data)
            await self.update_fixture_status(fixture_id, live_data["status"])
            return live_data
        except Exception:
            return None

    async def update_fixture_status(self, sofascore_id: int, status: str):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                query = select(Fixture).where(Fixture.sofascore_id == sofascore_id)
                result = await session.execute(query)
                fixture = result.scalar_one_or_none()

                if fixture and fixture.status != status:
                    fixture.status = status
                    if status == "finished":
                        await self.persist_match_data(sofascore_id)
            await session.commit()

    async def persist_match_data(self, fixture_id: int):
        cached_data = await self.get_cached_live_data(fixture_id)
        if not cached_data:
            return

        async with AsyncSessionLocal() as session:
            async with session.begin():
                fixture_query = select(Fixture).where(Fixture.sofascore_id == fixture_id)
                result = await session.execute(fixture_query)
                fixture = result.scalar_one_or_none()

                if not fixture:
                    return

                if cached_data.get("incidents"):
                    await ingest_match_events(
                        session,
                        cached_data["incidents"],
                        fixture.id,
                        fixture.home_team_id,
                        fixture.away_team_id
                    )

                if cached_data.get("stats"):
                    await ingest_match_statistics(
                        session,
                        fixture.id,
                        fixture.home_team.sofascore_id,
                        fixture.away_team.sofascore_id,
                        cached_data["stats"]
                    )

                fixture.has_events = True
                fixture.has_statistics = True
            await session.commit()

        await self.redis.delete(f"live:fixture:{fixture_id}")

    async def run_live_tracker(self):
        while True:
            try:
                live_fixtures = await self.get_live_fixtures()
                for fixture_id in live_fixtures:
                    await self.update_live_match(fixture_id)
                    await asyncio.sleep(1)
                await asyncio.sleep(30)
            except Exception:
                await asyncio.sleep(60)