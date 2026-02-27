# airflow/tasks/live_tasks.py

from sqlalchemy import select, func
from app.db import AsyncSessionLocal
from app.db.models import Fixture
from datetime import date
import asyncio
from app.live_tracker import main as run_live_tracker
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

async def _has_matches_today() -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).where(
                func.date(Fixture.date) == date.today(),
                Fixture.status.in_(["notstarted", "inprogress"])
            )
        )
        return result.scalar() > 0

def task_run_live_tracker(**context):
    async def _run():
        if not await _has_matches_today():
            print("Aucun match aujourd'hui, tracker non lancé")
            return
        await run_live_tracker()

    asyncio.run(_run())