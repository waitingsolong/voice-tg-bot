from sqlalchemy import String, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    @classmethod
    async def create(cls, db: AsyncSession, id, **kwargs):
        transaction = cls(id=id, **kwargs)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @classmethod
    async def get(cls, db: AsyncSession, id: str):
        try:
            transaction = await db.get(cls, id)
        except NoResultFound:
            return None
        return transaction

    @classmethod
    async def get_all(cls, db: AsyncSession):
        return (await db.execute(select(cls))).scalars().all()
    
class Users(BaseModel):
    __tablename__ = "users"
    uid: Mapped[str] = mapped_column(String, primary_key=True)
    tid: Mapped[str] = mapped_column(String)
    values: Mapped[str] = mapped_column(String)


class Assistants(BaseModel):
    __tablename__ = "assistants"
    aid: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, primary_key=True)
    prompt: Mapped[str] = mapped_column(String)