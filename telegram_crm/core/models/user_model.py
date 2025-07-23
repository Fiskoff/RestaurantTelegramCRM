from sqlalchemy import String, BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column

from telegram_crm.core.models.base_model import BaseModel, UserRole


class User(BaseModel):
    __tablename__ = 'users'

    telegram_id: Mapped[BigInteger] = mapped_column(BigInteger, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STAFF, index=True)
    position: Mapped[str] = mapped_column(String(100), nullable=False)