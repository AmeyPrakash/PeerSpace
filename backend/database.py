import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from backend.config import DATABASE_URL

# Psycopg 3 in async mode on Windows requires a SelectorEventLoop
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Configure engine parameters optimized for Neon Serverless & Psycopg 3
is_neon = "neon.tech" in DATABASE_URL
is_pooled = "-pooler" in DATABASE_URL

engine_kwargs = {"echo": False}
if is_pooled or is_neon:
    # Delegate connection pooling to Neon PgBouncer and avoid connection limits
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    DATABASE_URL,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    """Reusable FastAPI dependency providing an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initializes tables on startup if they don't already exist."""
    # Neon best practice: DDL operations bypass PgBouncer pooler to avoid transaction locks
    ddl_url = DATABASE_URL.replace("-pooler", "") if is_neon else DATABASE_URL
    
    ddl_engine = create_async_engine(
        ddl_url,
        echo=False,
        poolclass=NullPool
    )
    async with ddl_engine.begin() as conn:
        from backend.models.models import Base as ModelsBase
        await conn.run_sync(ModelsBase.metadata.create_all)
    await ddl_engine.dispose()
