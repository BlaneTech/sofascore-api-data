from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    pass

# We store raw payload as JSONB for flexibility
class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)  # player|team|match|search
    external_id: Mapped[str] = mapped_column(String(50), index=True)  # sofascore id or query
    payload: Mapped[dict] = mapped_column(JSONB)
