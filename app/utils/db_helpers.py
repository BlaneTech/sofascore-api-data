from typing import Type, TypeVar, Any, Dict, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


async def get_or_create(
    session: AsyncSession,
    model: Type[T],
    unique_field: str,
    value: Any,
    defaults: Dict[str, Any]
) -> T:
   
    result = await session.execute(
        model.__table__.select().where(getattr(model, unique_field) == value)
    )
    row = result.first()
    
    if row:
        return await session.get(model, row[0])
    
    obj = model(**defaults)
    session.add(obj)
    await session.flush()
    return obj


async def get_team_by_sofascore_id(
    session: AsyncSession,
    team_model: Type[T],
    sofascore_id: int
) -> Tuple[Optional[int], Optional[T]]:
    
    result = await session.execute(
        team_model.__table__.select().where(team_model.sofascore_id == sofascore_id)
    )
    team_row = result.first()
    
    if not team_row:
        return None, None
    
    return team_row[0], await session.get(team_model, team_row[0])
