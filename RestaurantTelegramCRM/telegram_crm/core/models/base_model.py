from enum import Enum

from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    pass


class UserRole(str, Enum):
    MANAGER = "manager"
    STAFF = "staff"


class TaskStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    OVERDUE = "overdue"