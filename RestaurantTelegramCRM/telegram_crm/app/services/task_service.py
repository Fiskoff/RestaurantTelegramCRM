from datetime import datetime
from zoneinfo import ZoneInfo

from core.db_helper import db_helper
from core.models import Task, TaskStatus
from core.models.base_model import SectorStatus
from app.repository.task_repository import TaskRepository


class TaskService:
    @staticmethod
    async def create_new_task(manager_id: int, executor_id: int | None, title: str, description: str,
                              deadline: datetime, sector_task: SectorStatus | None = None) -> dict:
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        if deadline.tzinfo is None:
            aware_deadline = deadline.replace(tzinfo=kemerovo_tz)
        else:
            aware_deadline = deadline.astimezone(kemerovo_tz)

        async with db_helper.session_factory() as session:
            try:
                new_task = Task(
                    manager_id=manager_id,
                    executor_id=executor_id,
                    title=title,
                    description=description,
                    deadline=aware_deadline,
                    sector_task=sector_task
                )
                session.add(new_task)
                await session.commit()
                await session.refresh(new_task)

                try:
                    from app.services.notification_service import notify_new_task
                    await notify_new_task(new_task)
                except Exception as notify_error:
                    print(f"Предупреждение: Ошибка при отправке уведомления о новой задаче: {notify_error}")

                return {"success": True, "message": "Задача создана", "task": new_task}

            except Exception as e:
                await session.rollback()
                return {"success": False, "message": f"Ошибка при создании задачи: {str(e)}"}


    @staticmethod
    async def get_tasks_user(telegram_id: int) -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            tasks = await task_repository.get_all_task_for_executor(telegram_id)
            active_and_overdue_tasks = [task for task in tasks if task.status != TaskStatus.COMPLETED]
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
    async def complete_task(task_id: int, comment: str = None, photo_url: str = None, executor_id: int = None) -> dict:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            try:
                result = await task_repository.complete_task(task_id, comment, photo_url, executor_id)
                if result > 0:
                    return {"success": True, "message": "Задача успешно завершена"}
                else:
                    return {"success": False, "message": "Задача не найдена"}
            except Exception as e:
                return {"success": False, "message": f"Ошибка при завершении задачи: {str(e)}"}


    @staticmethod
    async def get_completed_tasks() -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_completed_tasks()


    @staticmethod
    async def get_task_by_id_and_staff(task_id: int) -> Task:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_task_by_id_and_staff(task_id)


    @staticmethod
    async def delete_task_for_task_id(task_id: int):
        async with db_helper.session_factory() as session:
            try:
                task_repository = TaskRepository(session)
                task_to_delete = await task_repository.get_task_by_id(task_id)

                if task_to_delete:
                    await task_repository.delete_task_for_task_id(task_id)

                    try:
                        from app.services.notification_service import notify_deleted_task
                        await notify_deleted_task(task_to_delete)
                    except Exception as notify_error:
                        print(f"Предупреждение: Ошибка при отправке уведомления об удалении задачи: {notify_error}")
                else:
                    print(f"Попытка удаления несуществующей задачи с ID {task_id}")

            except Exception as e:
                print(f"Ошибка при удалении задачи {task_id}: {e}")


    @staticmethod
    async def get_all_task() -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_activ_and_overdue_tasks()


    @staticmethod
    async def update_task_field(task_id: int, field: str, new_value) -> dict:
        async with db_helper.session_factory() as session:
            try:
                task_repository = TaskRepository(session)
                old_task = await task_repository.get_task_by_id(task_id)
                if not old_task:
                    return {"success": False, "message": "Задача не найдена"}

                if field == 'executor':
                    await task_repository.update_task_field(task_id, 'executor_id', new_value)
                    await task_repository.update_task_field(task_id, 'sector_task', None)
                elif field == 'sector_task':
                    await task_repository.update_task_field(task_id, 'sector_task', new_value)
                    await task_repository.update_task_field(task_id, 'executor_id', None)
                else:
                    await task_repository.update_task_field(task_id, field, new_value)

                updated_task = await task_repository.get_task_by_id(task_id)

                try:
                    from app.services.notification_service import notify_updated_task
                    await notify_updated_task(old_task, updated_task)
                except Exception as notify_error:
                    print(f"Предупреждение: Ошибка при отправке уведомления об изменении задачи: {notify_error}")

                return {"success": True, "message": "Задача успешно обновлена"}
            except Exception as e:
                return {"success": False, "message": f"Ошибка при обновлении задачи: {str(e)}"}


    @staticmethod
    async def get_staff_tasks():
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_staff_tasks()


    @staticmethod
    async def get_sector_tasks(sector: SectorStatus) -> list[Task]:
        async with db_helper.session_factory() as session:
            task_repository = TaskRepository(session)
            return await task_repository.get_sector_tasks(sector)