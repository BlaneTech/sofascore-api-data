import asyncio
import sys
from pathlib import Path

# sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.ingest_afcon import main as run_ingestion


def task_run_competitions(**context):
    asyncio.run(run_ingestion())