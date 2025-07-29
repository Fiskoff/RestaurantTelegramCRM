from os import getenv

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class EnvLoader:
    load_dotenv()


class DatabaseENV(EnvLoader):
    DATABASE_URL: str = getenv("DATABASE_URL")
    TOKEN: str = getenv("TOKEN")


class DataBaseConfig(BaseModel):
    url: str = DatabaseENV.DATABASE_URL
    echo: bool = True
    pool_size: int = 10
    max_overflow: int = 15


class TelegramConfig(BaseModel):
    token: str = DatabaseENV.TOKEN


class Settings(BaseSettings):
    db: DataBaseConfig = DataBaseConfig()
    tg: TelegramConfig = TelegramConfig()


settings = Settings()
