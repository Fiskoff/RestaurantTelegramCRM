from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Task, TaskStatus


class TaskRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session

    async def create_task(self, manager_id: int, executor_id: int, title: str, description: str, deadline: datetime):
        new_user = Task(
            manager_id=manager_id,
            executor_id=executor_id,
            title=title,
            description=description,
            deadline=deadline
        )
        self.session.add(new_user)
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
            .where(Task.status == TaskStatus.ACTIVE,Task.deadline < current_time)
            .values(status=TaskStatus.OVERDUE)
        )
        result = await self.session.execute(stmt)
        return result.rowcount