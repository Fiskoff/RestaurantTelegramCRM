from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Enum, func, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telegram_crm.core.models.base_model import BaseModel, TaskStatus


class Task(BaseModel):
    __tablename__ = "tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str] = mapped_column(String, nullable=True)

    executor_id = mapped_column(BigInteger, ForeignKey("users.id"))
    manager_id = mapped_column(BigInteger, ForeignKey("users.id"))

