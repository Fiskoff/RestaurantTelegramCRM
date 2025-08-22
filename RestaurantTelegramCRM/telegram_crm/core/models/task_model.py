from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Integer, Text, DateTime, ForeignKey, BigInteger, String, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base_model import BaseModel, TaskStatus, SectorStatus
from core.models.user_model import User


class Task(BaseModel):
    __tablename__ = "tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.ACTIVE, nullable=False, index=True)
    sector_task: Mapped[SectorStatus | None] = mapped_column(Enum(SectorStatus), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Krasnoyarsk")), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notified_one_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_today: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_two_hours: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_overdue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    executor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    manager_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)


    executor: Mapped["User | None"] = relationship(
        back_populates="executed_tasks",
        foreign_keys=[executor_id],
        lazy="selectin"
    )
    manager: Mapped["User"] = relationship(
        back_populates="managed_tasks",
        foreign_keys=[manager_id],
        lazy="selectin"
    )