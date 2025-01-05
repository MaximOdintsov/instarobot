import datetime
import enum

from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AccountType(enum.Enum):  # FIXME Заменить на 1, 2, 3, 4 и тд
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
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.OTHER)
    
    # post - связанный объект Post
    # 
    
    
    # links = Column(JSON, default=[])
    # all_description = Column(String, nullable=True)
    # posts = Column(Integer, default=0)
    # subscribers = Column(Integer, default=0)
    # subscriptions = Column(Integer, default=0)
    # last_post_datetime = Column(DateTime, nullable=True)
    # hashtag = Column(String, nullable=True)
    
    
