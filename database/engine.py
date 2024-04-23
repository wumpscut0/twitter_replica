import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models import Base

engine = create_async_engine(os.getenv("BASE"))
session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
