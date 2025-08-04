from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


from core.models import Task, TaskStatus, User


class TaskRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session


    async def create_task(self, manager_id: int, executor_id: int, title: str, description: str, deadline: datetime):
        new_task = Task(
            manager_id=manager_id,
            executor_id=executor_id,
            title=title,
            description=description,
            deadline=deadline
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


    async def complete_task(self, task_id: int, comment: str = None, photo_url: str = None):
        kemerovo_tz = ZoneInfo("Asia/Krasnoyarsk")
        completed_at = datetime.now(kemerovo_tz)

        stmt = (
            update(Task)
            .where(Task.task_id == task_id)
            .values(
                status=TaskStatus.COMPLETED,
                completed_at=completed_at,
                comment=comment,
                photo_url=photo_url
            )
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