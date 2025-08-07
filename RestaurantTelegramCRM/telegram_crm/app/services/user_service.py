from core.db_helper import db_helper
from app.repository.user_repository import UserRepository
from core.models import User
from core.models.base_model import UserRole, SectorStatus


class UserService:
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int):
        async with db_helper.session_factory() as session:
            user_repository = UserRepository(session)
            return await user_repository.get_user(telegram_id)

    @staticmethod
    async def create_new_user(telegram_id: int, full_name: str, role: UserRole, position: str, sector: SectorStatus) -> dict:
        async with db_helper.session_factory() as session:
            user_repository = UserRepository(session)
            user = await user_repository.get_user(telegram_id)
            if user is None:
                await user_repository.create_user(telegram_id, full_name, role, position, sector)
                return {"success": True, "message": "Пользователь успешно создан"}
            return {"success": False, "message": "Пользователь уже существует"}

    @staticmethod
    async def get_all_users() -> list[User]:
        async with db_helper.session_factory() as session:
            user_repository = UserRepository(session)
            return await user_repository.get_all_users()

    @staticmethod
    async def delete_user(telegram_id: int):
        async with db_helper.session_factory() as session:
            user_repository = UserRepository(session)
            try:
                deleted_count = await user_repository.delete_user(telegram_id)
                if deleted_count > 0:
                    return {"success": True, "message": "Сотрудник успешно удален"}
                else:
                    return {"success": False, "message": "Сотрудник не найден"}
            except Exception as e:
                print(e)
                return {"success": False, "message": f"Ошибка при удалении: {str(e)}"}

    @staticmethod
    async def get_users_by_sector(sector: SectorStatus):
        async with db_helper.session_factory() as session:
            user_repository = UserRepository(session)
            return await user_repository.get_users_by_sector(sector)