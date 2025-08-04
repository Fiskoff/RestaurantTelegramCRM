from aiogram import Router

from app.handlers.registration_handler import register_router
from app.handlers.manager_handlers import manager_router
from app.handlers.create_task_handlers import create_task_router
from app.handlers.my_tasks_handlers import my_task_router
from app.handlers.overdue_task_handlers import overdue_task
from app.handlers.completed_tasks_handlers import completed_tasks_router
from app.handlers.update_task_handlers import change_task_router


all_routers = Router()

all_routers.include_router(register_router)
all_routers.include_router(manager_router)
all_routers.include_router(create_task_router)
all_routers.include_router(my_task_router)
all_routers.include_router(overdue_task)
all_routers.include_router(completed_tasks_router)
all_routers.include_router(change_task_router)