from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False; PostgreSQL doesn't need it
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=not settings.is_production,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        from sqlalchemy import text
        # ADD missing columns (no-op if already present)
        for stmt in [
            "ALTER TABLE sources ADD COLUMN authors TEXT",
            "ALTER TABLE sources ADD COLUMN doi VARCHAR(255)",
        ]:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass

        # Widen VARCHAR columns to TEXT on PostgreSQL (no-op on SQLite)
        if not settings.is_sqlite:
            for stmt in [
                "ALTER TABLE sources ALTER COLUMN authors TYPE TEXT",
                "ALTER TABLE sources ALTER COLUMN title TYPE TEXT",
            ]:
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    pass
