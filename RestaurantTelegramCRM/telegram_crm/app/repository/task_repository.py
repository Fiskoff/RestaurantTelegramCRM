from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession


from core.models import Task, TaskStatus, User
from core.models.base_model import SectorStatus


class TaskRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session

    async def create_task(self, manager_id: int, executor_id: int, title: str, description: str, deadline: datetime,
                          sector_task: SectorStatus = None):
        new_task = Task(
            manager_id=manager_id,
            executor_id=executor_id,
            title=title,
            description=description,
            deadline=deadline,
            sector_task=sector_task
        )
        self.session.add(new_task)
        await self.session.commit()


    async def get_all_task_for_executor(self, executor_id: int):
        result = await self.session.execute(select(Task).where(Task.executor_id == executor_id))
        return result.scalars().all()


    async def get_task_by_id(self, task_id: int):
        result = await self.session.execute(select(Task).where(Task.task_id == task_id))
        return result.scalars().first()


    async def update_status_task(self, current_time):
        stmt = (
            update(Task)
            .where(Task.status == TaskStatus.ACTIVE, Task.deadline < current_time)
            .values(status=TaskStatus.OVERDUE)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


    async def get_all_overdue_tasks(self):
        stmt = (
            select(Task, User)
            .join(User, Task.executor_id == User.telegram_id)
            .where(Task.status == TaskStatus.OVERDUE, Task.executor_id.isnot(None))
        )
        result = await self.session.execute(stmt)
        overdue_tasks_with_users = result.all()
        return overdue_tasks_with_users

    async def complete_task(self, task_id: int, comment: str = None, photo_url: str = None, executor_id: int = None):
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        completed_at = datetime.now(kemerovo_tz)

        update_values = {
            'status': TaskStatus.COMPLETED,
            'completed_at': completed_at,
            'comment': comment,
            'photo_url': photo_url
        }

        if executor_id is not None:
            update_values['executor_id'] = executor_id

        stmt = (
            update(Task)
            .where(Task.task_id == task_id)
            .values(**update_values)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


    async def get_completed_tasks(self):
        result = await self.session.execute(select(Task).where(Task.status == TaskStatus.COMPLETED))
        return result.scalars().all()


    async def get_task_by_id_and_staff(self, task_id: int):
        stmt = (
            select(Task, User)
            .join(User, Task.executor_id == User.telegram_id)
            .where(Task.task_id == task_id, Task.executor_id.isnot(None))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()


    async def delete_task_for_task_id(self, task_id):
        await self.session.execute(delete(Task).where(Task.task_id == task_id))
        await self.session.commit()


    async  def get_activ_and_overdue_tasks(self):
        result = await self.session.execute(select(Task).where(Task.status != TaskStatus.COMPLETED))
        return result.scalars().all()

    async def update_task_field(self, task_id: int, field: str, new_value):
        field_mapping = {
            'title': Task.title,
            'description': Task.description,
            'executor_id': Task.executor_id,
            'deadline': Task.deadline,
            'sector_task': Task.sector_task
        }

        if field not in field_mapping:
            raise ValueError(f"Недопустимое поле для обновления: {field}")

        stmt = (
            update(Task)
            .where(Task.task_id == task_id)
            .values({field_mapping[field]: new_value})
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        if result.rowcount == 0:
            raise ValueError("Задача не найдена")

    async def get_staff_tasks(self):
        stmt = select(Task).where(
            or_(
                Task.executor_id.isnot(None),
                Task.sector_task.isnot(None)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_sector_tasks(self, sector: SectorStatus):
        result = await self.session.execute(
            select(Task).where(
                Task.sector_task == sector,
                Task.status != TaskStatus.COMPLETED
            )
        )
        return result.scalars().all()


    async def get_active_tasks_for_notification(self) -> list[Task]:
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        current_time = datetime.now(kemerovo_tz)
        future_time = current_time + timedelta(hours=48)
        stmt = (
            select(Task)
            .where(
                Task.status == TaskStatus.ACTIVE,
                Task.deadline >= current_time.replace(tzinfo=None),  # Сравниваем naive datetime
                Task.deadline <= future_time.replace(tzinfo=None)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()