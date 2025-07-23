from sqlalchemy.ext.asyncio import AsyncSession

from core.models.user_model import User


class UserRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session


    async def create_user(self, user_id:int, username:str, role:str, position:str):
        self.session.add(User(telegram_id=user_id, full_name=username, role=role, position=position))
        await self.session.commit()
