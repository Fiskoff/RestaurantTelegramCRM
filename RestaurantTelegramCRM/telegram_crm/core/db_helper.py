from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from core.config import settings


class DatabaseHelper:
    def __init__(
            self,
            url: str,
            echo: bool = False,
            pool_size: int = 5,
            max_overflow: int = 10,

    ):
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow
        )

        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False
        )


db_helper = DatabaseHelper(
    settings.db.url,
    settings.db.echo,
    settings.db.pool_size,
    settings.db.max_overflow,
)