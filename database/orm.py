import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database.models import Base, Account, AccountType
import config


async def create_tables(async_engine: create_async_engine):
    # Создаём таблицы
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def insert_account(async_session: sessionmaker, account_link: str, account_type: AccountType = None, 
                         is_processed: bool = False, account_data: dict = {}):

    async with async_session() as session:
        # Проверяем, существует ли запись с таким account_link
        result = await session.execute(
            select(Account).where(Account.link == account_link)
        )
        account = result.scalar_one_or_none()

        # Если аккаунт существует и есть данные, то обновляем объект
        if account and account_data:
            account.data = account_data
            account.is_processed = is_processed
        # Если аккаунта не существует, создаём новый объект
        elif not account:
            account = Account(
                link=account_link,
                data=account_data,
                is_processed=is_processed
            )
        else:
            return
        if account_type:
            account.account_type = account_type
        
        session.add(account)
        await session.commit()  # После добавления всех новых объектов — коммитим


# change account


async def get_all_accounts(async_session: sessionmaker):
    async with async_session() as session:
        # Получение всех объектов Account
        all_accounts = await session.execute(select(Account))
        all_accounts = all_accounts.scalars().all()
        return all_accounts


async def get_accounts_not_send(async_session: sessionmaker):
    """
    Получить все аккаунты, у которых is_send = False.
    """
    async with async_session() as session:
        all_accounts = await session.execute(
            select(Account).where(Account.is_send == False, Account.is_processed == True)
        )
        return all_accounts.scalars().all()


async def get_accounts_not_processed(async_session: sessionmaker):
    """
    Получить все аккаунты, у которых is_send = False.
    """
    async with async_session() as session:
        all_accounts = await session.execute(
            select(Account).where(Account.is_processed == False)
        )
        return all_accounts.scalars().all()


async def mark_account_as_sent(async_session: sessionmaker, account: Account):
    """
    Обновить поле is_send для accounts
    """
    async with async_session() as session:
        account.is_send = True
        session.add(account)  # Добавление изменённого объекта в сессию

        # Фиксация изменений в базе данных
        await session.commit()


# Создание асинхронного движка
async_engine = create_async_engine(config.DATABASE_URL, echo=True)

# Создание асинхронной фабрики сессий
async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# asyncio.run(create_tables(async_engine=async_engine))
# await insert_new_account(async_session=async_session, data=account_info)
# await get_all_accounts(async_session=async_session)
# await create_tables(async_engine=async_engine)