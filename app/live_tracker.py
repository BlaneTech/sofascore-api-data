import asyncio
from app.services.scraper.live_service import LiveMatchService


async def main():
    service = LiveMatchService()
    
    try:
        print("Live Tracker démarré...")
        await service.run_live_tracker()
    except KeyboardInterrupt:
        print("Arrêt du tracker...")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())