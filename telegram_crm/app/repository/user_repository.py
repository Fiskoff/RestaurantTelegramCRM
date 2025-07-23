from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.user_model import User


class UserRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session

    async def create_user(self, telegram_id:int, full_name:str, role:str, position:str):
        self.session.add(User(telegram_id=telegram_id, full_name=full_name, role=role, position=position))
        await self.session.commit()

    async def get_user(self, input_user_id) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == input_user_id))
        return result.scalars().first()