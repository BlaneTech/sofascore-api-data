import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.ingest_friendlies import main as run_friendlies

def task_run_friendlies(**context):
    asyncio.run(run_friendlies())