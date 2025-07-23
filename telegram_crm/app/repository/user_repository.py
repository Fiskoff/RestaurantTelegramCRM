from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.user_model import User
from core.models.base_model import UserRole


class UserRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session

    async def create_user(self, telegram_id: int, full_name: str, role: UserRole, position: str):
        new_user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            role=role,
            position=position
        )
        self.session.add(new_user)
        await self.session.commit()

    async def get_user(self, telegram_id: int):
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()