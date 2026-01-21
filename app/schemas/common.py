from pydantic import BaseModel

class StoreResult(BaseModel):
    stored: bool
    id: int | None = None
