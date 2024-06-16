import contextlib
import logging
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import (AsyncConnection, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from config import config


class DatabaseSessionManager:
    def __init__(self, url: str):
        self._engine = create_async_engine(url, echo=config.echo_sql)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)


    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None


    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception as e:
                await connection.rollback()
                logging.error(f"DatabaseSessionManager: Connection error")
                logging.exception(e)


    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logging.error(f"DatabaseSessionManager: Session error")
            logging.exception(e)
        finally:
            await session.close()
