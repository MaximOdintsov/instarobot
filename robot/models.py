import datetime
import enum

from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AccountType(enum.Enum):
    UNKNOWN = "UNKNOWN"
    ARTIST = "ARTIST"
    BEATMAKER = "BEATMAKER"
    LABEL = "LABEL"
    MARKET = "MARKET"
    COMMUNITY = "COMMUNITY"
    OTHER = "OTHER"


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_datetime = Column(DateTime, default=datetime.datetime.now)
    # modify_datetime =
    
    link = Column(String, unique=True, nullable=False)
    is_send = Column(Boolean, default=False)  # Записан ли экземпляр в таблицу
    is_processed = Column(Boolean, default=False)  # Обработан ли экземпляр
    data = Column(JSON, default=dict)
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.UNKNOWN)
    
    # is_checked - Проверен ли экземпляр верификатором
    # post - Связанный объект Post

    
    
