from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Enum, func, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base_model import BaseModel, TaskStatus
from core.models.user_model import User


class Task(BaseModel):
    __tablename__ = "tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)

    executor_id: Mapped[BigInteger | None] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    manager_id: Mapped[BigInteger] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)

    executor: Mapped["User | None"] = relationship(
        "User",
        back_populates="executed_tasks",
        foreign_keys=[executor_id]
    )
    manager: Mapped["User"] = relationship(
        "User",
        back_populates="managed_tasks",
        foreign_keys=[manager_id]
    )