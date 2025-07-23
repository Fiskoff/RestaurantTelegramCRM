from sqlalchemy import String, BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base_model import BaseModel, UserRole


class User(BaseModel):
    __tablename__ = 'users'

    telegram_id: Mapped[BigInteger] = mapped_column(BigInteger, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STAFF, index=True, nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=True)


    managed_tasks = relationship(
        "Task",
        back_populates="manager",
        foreign_keys="Task.manager_id"
    )
    executed_tasks = relationship(
        "Task",
        back_populates="executor",
        foreign_keys="Task.executor_id"
    )