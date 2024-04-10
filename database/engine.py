import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(os.getenv("BASE"))
session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)


# async def drop_all():
#     async with engine.connect() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#
#
# async def create_all():
#     async with engine.connect() as conn:
#         await conn.run_sync(Base.metadata.create_all)
