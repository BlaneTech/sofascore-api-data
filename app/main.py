from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.settings import settings
from app.services.sofa_client import sofa_client
from app.db.init_db import init_db
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redis
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    # DB init (simple create_all)
    await init_db()

    # SofaScore client (Playwright/Chromium behind)
    await sofa_client.start()

    yield

    # Shutdown
    await sofa_client.stop()
    await app.state.redis.close()

app = FastAPI(
    title="Football SofaScore API",
    version="1.0.0",
    description="REST API based on sofascore-wrapper (async)",
)

app.include_router(api_router, prefix="/api", tags=["api"])

try:
    from app.api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api")
except Exception:
    pass
