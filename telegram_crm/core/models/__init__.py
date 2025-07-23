from sqlalchemy.orm import configure_mappers

from .base_model import BaseModel, UserRole, TaskStatus
from .user_model import User
from .task_model import Task

configure_mappers()