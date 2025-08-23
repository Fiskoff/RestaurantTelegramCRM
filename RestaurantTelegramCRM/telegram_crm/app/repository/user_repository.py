from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.user_model import User
from core.models.base_model import UserRole, SectorStatus

class UserRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session

    async def create_user(self, telegram_id: int, full_name: str, role: UserRole, position: str, sector: SectorStatus):
        new_user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            role=role,
            position=position,
            sector=sector
        )
        self.session.add(new_user)
        await self.session.commit()

    async def get_user(self, telegram_id: int):
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_all_users(self):
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def delete_user(self, telegram_id: int):
        result = await self.session.execute(delete(User).where(User.telegram_id == telegram_id))
        await self.session.commit()
        return result.rowcount

    async def get_users_by_sector(self, sector: SectorStatus):
        result = await self.session.execute(select(User).where(User.sector == sector))
        return result.scalars().all()