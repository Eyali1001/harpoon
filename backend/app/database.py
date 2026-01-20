from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    import logging
    from sqlalchemy import text
    # Import models so they register with Base.metadata
    from app.models.trade import Trade, CacheMetadata

    logger = logging.getLogger(__name__)
    logger.info("Initializing database...")

    async with engine.begin() as conn:
        logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully")

        # Migrate column sizes if needed (safe to run multiple times)
        try:
            await conn.execute(text("ALTER TABLE trades ALTER COLUMN outcome TYPE VARCHAR(255)"))
            logger.info("Migrated outcome column")
        except Exception as e:
            logger.info(f"Outcome column migration skipped: {e}")

        try:
            await conn.execute(text("ALTER TABLE trades ALTER COLUMN side TYPE VARCHAR(10)"))
            logger.info("Migrated side column")
        except Exception as e:
            logger.info(f"Side column migration skipped: {e}")

    logger.info("Database initialization complete")
