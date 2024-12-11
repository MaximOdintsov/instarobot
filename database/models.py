import datetime
import enum

from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AccountType(enum.Enum):
    Artist = "Artist"
    Market = "Market"
    Beatmaker = "Beatmaker"
    Other = "Other"

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_datetime = Column(DateTime, default=datetime.datetime.now)
    links = Column(JSON, default=[])
    link = Column(String, unique=True, nullable=False)
    all_description = Column(String, nullable=True)
    posts = Column(Integer, default=0)
    subscribers = Column(Integer, default=0)
    subscriptions = Column(Integer, default=0)
    last_post_datetime = Column(DateTime, nullable=True)
    hashtag = Column(String, nullable=True)
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.Other)
    data = Column(JSON, default=dict)
    is_send = Column(Boolean, default=False)
    
    
