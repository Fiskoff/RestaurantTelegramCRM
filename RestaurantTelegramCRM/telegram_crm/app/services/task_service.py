from datetime import datetime

from core.db_helper import db_helper
from core.models import Task, TaskStatus
from app.repository.task_repository import TaskRepository


class TaskService:
    @staticmethod
    async def create_new_task(manager_id: int, executor_id: int, title: str, description: str, deadline: datetime) -> dict:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            await task_repository.create_task(manager_id, executor_id, title, description, deadline)
            return {"success": True, "message": "Задача создана"}

    @staticmethod
    async def get_tasks_user(telegram_id: int) -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            tasks =  await task_repository.get_all_task_for_executor(telegram_id)
            active_and_overdue_tasks = []
            for task in tasks:
                if task.status == TaskStatus.COMPLETED:
                    continue
                active_and_overdue_tasks.append(task)
            return active_and_overdue_tasks
            
    @staticmethod
    async def get_task_by_id(task_id: int) -> Task:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_task_by_id(task_id)

    @staticmethod
    async def get_all_overdue_tasks():
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_all_overdue_tasks()

    @staticmethod
    async def complete_task(task_id: int, comment: str = None, photo_url: str = None) -> dict:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            try:
                result = await task_repository.complete_task(task_id, comment, photo_url)
                if result > 0:
                    return {"success": True, "message": "Задача успешно завершена"}
                else:
                    return {"success": False, "message": "Задача не найдена"}
            except Exception as e:
                return {"success": False, "message": f"Ошибка при завершении задачи: {str(e)}"}

    @staticmethod
    async def get_completed_tasks() -> list[Task]:
        async with db_helper.session_factory() as session:
            completed_tasks = TaskRepository(session)
            return await completed_tasks.get_completed_tasks()

    @staticmethod
    async def get_task_by_id_and_staff(task_id: int) -> Task:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_task_by_id(task_id)

    @staticmethod
    async def delete_task_for_task_id(task_id: int):
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            await task_repository.delete_task_for_task_id(task_id)

    @staticmethod
    async def get_all_task() -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_activ_and_overdue_tasks()

