from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.api import (leagues, teams, fixtures, players, standings,
                     events, statistics, lineups, managers, seasons
)
from app.api import api_keys_routes
from app.auth import verify_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    print(" Starting gogainde-data API...")
    yield
    print("Shutting down gogainde-data API...")

app = FastAPI(
    title=settings.APP_NAME,
    # dependencies=[Depends(verify_api_key)],
    version=settings.APP_VERSION,
    description="GOGAINDE-DATA API - API pour les données de football",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "errors": [str(exc)],
            "data": None
        }
    )


# Routes de base
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to GOGAinde-Data API",
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "endpoints": {
            "leagues": "/leagues",
            "teams": "/teams",
            "fixtures": "/fixtures",
            "players": "/players",
            "standings": "/standings",
            "season": "/season",
            "manager": "/manager",
            "events": "/events",
            "lineups": "/lineups",
            "statistics": "/statistics"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
   
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }

# Inclure les routers
app.include_router(api_keys_routes.router)
app.include_router(leagues.router, dependencies=[Depends(verify_api_key)])
app.include_router(seasons.router, dependencies=[Depends(verify_api_key)])
app.include_router(teams.router, dependencies=[Depends(verify_api_key)])
app.include_router(players.router, dependencies=[Depends(verify_api_key)])
app.include_router(managers.router, dependencies=[Depends(verify_api_key)])
app.include_router(fixtures.router, dependencies=[Depends(verify_api_key)])
app.include_router(lineups.router, dependencies=[Depends(verify_api_key)])
app.include_router(standings.router, dependencies=[Depends(verify_api_key)])
app.include_router(events.router, dependencies=[Depends(verify_api_key)])
app.include_router(statistics.router, dependencies=[Depends(verify_api_key)])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
