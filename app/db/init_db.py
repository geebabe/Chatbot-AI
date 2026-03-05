from app.db.session import engine


async def init_db() -> None:
    """Verify we can connect (tables are managed by Alembic)."""
    async with engine.begin():
        pass  # connection check only


async def close_db() -> None:
    """Dispose the engine connection pool."""
    await engine.dispose()
