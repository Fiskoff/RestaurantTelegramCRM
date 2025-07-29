from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Task


class TaskRepository:
    def __init__(self, async_session: AsyncSession):
        self.session = async_session

    async def create_task(self, manager_id: int, executor_id: int, title: str, description: str, deadline: datetime):
        new_user = Task(
            executor_id=executor_id,
            manager_id=manager_id,
            title=title,
            description=description,
            deadline=deadline
        )
        self.session.add(new_user)
        await self.session.commit()