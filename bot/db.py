import os
from sqlalchemy import Column, BigInteger, Date, String, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "lifery")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    chat_id = Column(BigInteger, primary_key=True, index=True)
    birth_date = Column(Date, nullable=False)
    language_code = Column(String, default="en")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def delete_user(chat_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        user = result.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False


async def get_user(chat_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        return result.scalar_one_or_none()
