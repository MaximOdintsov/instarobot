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

async def insert_new_account(async_session: sessionmaker, data: dict):
    async with async_session() as session:
        account_link = data['account_link']
        # Проверяем, существует ли запись с таким link
        result = await session.execute(
            select(Account).where(Account.link == account_link)
        )
        existing_account = result.scalar_one_or_none()

        if not existing_account:  # Если аккаунта не существует, создаём новый объект
            new_account = Account(
                link=account_link,
                all_description=data.get('all_description', None),
                links=data.get('links', []),
                posts=data.get('posts', 0),
                subscribers=data.get('subscribers', 0),
                subscriptions=data.get('subscriptions', 0),
                account_type=AccountType.Other,
                hashtag=data.get('hashtag', None)
            )
            session.add(new_account)
            await session.commit()  # После добавления всех новых объектов — коммитим
        
async def get_all_accounts(async_session: sessionmaker):
    async with async_session() as session: 
        # Получение всех объектов Account
        all_accounts = await session.execute(select(Account))
        all_accounts = all_accounts.scalars().all()

        # Проход по всем объектам
        for acc in all_accounts:
            print(f"ID: {acc.id}, Link: {acc.link}, Type: {acc.account_type}")
            
      
      
# Создание асинхронного движка
async_engine = create_async_engine(config.DATABASE_URL, echo=True)

# Создание асинхронной фабрики сессий
async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# await create_tables(async_engine=async_engine)
# await insert_new_account(async_session=async_session, data=account_info)
# await get_all_accounts(async_session=async_session)
    