from datetime import datetime

from core.db_helper import db_helper
from core.models import Task
from app.repository.task_repository import TaskRepository


class TaskService:
    @staticmethod
    async def create_new_task(manager_id: int, executor_id: int, title: str, description: str, deadline: datetime) -> dict:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            await task_repository.create_task(manager_id, executor_id, title, description, deadline)
            return {"success": True, "message": "Задача создана"}

    @staticmethod
    async def get_all_task(telegram_id: int) -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_all_task_for_executor(telegram_id)

    @staticmethod
    async def get_task_by_id(task_id: int) -> Task:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_task_by_id(task_id)

    @staticmethod
    async def get_all_overdue_tasks() -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_all_overdue_tasks()