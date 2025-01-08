from typing import Type, TypeVar, Optional, List, Any, Dict

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession
)
from sqlalchemy.orm import sessionmaker

from robot import config
from robot.database.models import Base, Account, STATUS, AccountType

# Определяем универсальный тип T, привязанный к моделям (наследникам Base).
T = TypeVar('T', bound=Base)

# Создаём асинхронный движок (engine).
async_engine: AsyncEngine = create_async_engine(
    config.DATABASE_URL,  # sqlite+aiosqlite:///<path_to_db>
    echo=True  # установить в False в продакшене
)

# Создаём фабрику асинхронных сессий.
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
    filters: Optional[Dict[str, Any]] = None,
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
    filters: Optional[Dict[str, Any]] = None,
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
    filters: Optional[Dict[str, Any]] = None,
    defaults: Optional[Dict[str, Any]] = None,
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
    defaults = defaults or {}
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

# --- Примеры использования для модели Account ---

# async def create_or_update_account(
#     async_session_factory: sessionmaker[AsyncSession],
#     account_link: str,
#     **kwargs: Any
# ) -> Optional[Account]:
#     """
#     Создать или обновить аккаунт (Account).
#     Если аккаунт с указанной ссылкой уже существует, он будет обновлён,
#     иначе будет создан новый.
#
#     :param async_session_factory: Фабрика асинхронных сессий.
#     :param account_link: Ссылка на аккаунт (уникальное поле).
#     :param kwargs: Дополнительные поля (status, account_type, data и т.д.).
#     :return: Созданный или обновлённый объект Account, либо None при ошибке.
#     """
#     return await create_or_update_object(
#         async_session_factory,
#         Account,
#         defaults=kwargs,
#         link=account_link
#     )
#
#
# async def get_accounts_by_status(
#     async_session_factory: sessionmaker[AsyncSession],
#     status: STATUS
# ) -> List[Account]:
#     """
#     Получить список аккаунтов с заданным статусом.
#
#     :param async_session_factory: Фабрика асинхронных сессий.
#     :param status: Значение статуса, по которому будет осуществлён поиск.
#     :return: Список объектов Account (может быть пустым).
#     """
#     return await get_objects_by_filter(
#         async_session_factory,
#         Account,
#         status=status
#     )

