from typing import Type, TypeVar, Optional, List, Any, Dict

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession
)
from sqlalchemy.orm import sessionmaker

from robot.conf import settings
from robot.database.models import Base


# Универсальный тип T, привязанный к моделям (наследникам Base).
T = TypeVar('T', bound=Base)


# Асинхронный движок (engine).
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,  # sqlite+aiosqlite:///<path_to_db>
    # echo=True  # установить в False в продакшене
)

# Фабрика асинхронных сессий.
async_session: sessionmaker[AsyncSession] = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_tables(async_engine: AsyncEngine) -> None:
    """
    Создаёт все таблицы, определённые в Base.metadata.
    Работает только если таблиц не существует.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_object_by_filter(
    async_session_factory: sessionmaker[AsyncSession],
    model: Type[T],
    filters: Optional[Dict[str, Any]] = {},
) -> Optional[T]:
    """
    Получить единственный объект по заданным фильтрам.

    :param async_session_factory: Фабрика асинхронных сессий.
    :param model: Модель (класс), унаследованная от Base.
    :param filters: Словарь фильтров для метода filter_by.
    :return: Найденный объект или None.
    """
    async with async_session_factory() as session:
        try:
            result = await session.execute(select(model).filter_by(**filters))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await session.rollback()
            # Логируйте или обрабатывайте ошибку по необходимости
            print(f"[get_object_by_filter] DB Error: {e}")
            return None


async def get_objects_by_filter(
    async_session_factory: sessionmaker[AsyncSession],
    model: Type[T],
    filters: Optional[Dict[str, Any]] = {},
) -> List[T]:
    """
    Получить список объектов по заданным фильтрам.

    :param async_session_factory: Фабрика асинхронных сессий.
    :param model: Модель (класс), унаследованная от Base.
    :param filters: Словарь фильтров для метода filter_by.
    :return: Список объектов (может быть пустым).
    """
    async with async_session_factory() as session:
        try:
            result = await session.execute(select(model).filter_by(**filters))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await session.rollback()
            # Логируйте или обрабатывайте ошибку по необходимости
            print(f"[get_objects_by_filter] DB Error: {e}")
            return []


async def create_or_update_object(
    async_session_factory: sessionmaker[AsyncSession],
    model: Type[T],
    filters: Optional[Dict[str, Any]] = {},
    defaults: Optional[Dict[str, Any]] = {},
) -> Optional[T]:
    """
    Создать или обновить объект в базе данных.
    Если объект с указанными фильтрами существует – обновить,
    иначе создать.

    :param async_session_factory: Фабрика асинхронных сессий.
    :param model: Модель (класс), унаследованная от Base.
    :param defaults: Словарь значений для установки или обновления.
    :param filters: Словарь фильтров для идентификации объекта.
    :return: Созданный или обновлённый объект, либо None при ошибке.
    """
    async with async_session_factory() as session:
        try:
            result = await session.execute(select(model).filter_by(**filters))
            obj = result.scalar_one_or_none()

            if obj:
                for key, value in defaults.items():
                    setattr(obj, key, value)
            else:
                # Объект не найден, создаём новый
                obj = model(**{**filters, **defaults})
                session.add(obj)

            await session.commit()
            await session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await session.rollback()
            # Логируйте или обрабатывайте ошибку по необходимости
            print(f"[create_or_update_object] DB Error: {e}")
            return None


async def get_objects_by_where(
    async_session_factory: sessionmaker,
    model: Type[T],
    *where_conditions
) -> List[T]:
    async with async_session_factory() as session:
        try:
            stmt = select(model).where(*where_conditions)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            await session.rollback()
            print(f"[get_objects_by_where] DB Error: {e}")
            return []