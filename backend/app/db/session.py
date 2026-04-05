from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# In production, this comes from environment variables
DATABASE_URL = "postgresql+asyncpg://postgres:moodwave_pass@db:5432/moodwave_db"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

Base = declarative_base()

async def get_db():
    """Dependency to inject DB sessions into API routes."""
    async with SessionLocal() as session:
        yield session