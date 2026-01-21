from contextlib import asynccontextmanager
from sofascore_wrapper.api import SofascoreAPI

# One shared client for the whole app (expensive browser setup)
class SofaClient:
    def __init__(self):
        self.api: SofascoreAPI | None = None

    async def start(self):
        if self.api is None:
            self.api = SofascoreAPI()

    async def stop(self):
        if self.api is not None:
            await self.api.close()
            self.api = None

sofa_client = SofaClient()
