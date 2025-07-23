from core.db_helper import db_helper
from app.repository.user_repository import UserRepository


class UserService:

    @staticmethod
    async def create_new_user(telegram_id:int, full_name:str, role:str, position:str) -> dict:
        async with db_helper.session_factory() as session:
            user_repository = UserRepository(session)
            user = await user_repository.get_user(telegram_id)
            if user is None:
                await user_repository.create_user(telegram_id, full_name, role, position)
                return {"success": True, "message": "User created successfully"}
            return {"success": False, "message": "Such a user already exists"}