import datetime
import enum

from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Boolean, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class STATUS(enum.Enum):
    PARSING = 'PARSING'
    PREDICTING = 'PREDICTING'
    FAILED = 'FAILED'
    READY = 'READY'
    SENT = 'SENT'
    VALIDATED = 'VALIDATED'


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

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    create_datetime = Column(
        DateTime, default=func.now()
    )
    modify_datetime = Column(
        DateTime, onupdate=func.now()
    )

    link = Column(
        String, unique=True, nullable=False
    )
    status = Column(
        Enum(STATUS, name='status_enum'), nullable=False, default=STATUS.PARSING, server_default='PARSING'
    )
    account_type = Column(
        Enum(AccountType, name='account_type_enum'), nullable=False, default=AccountType.UNKNOWN
    )
    data = Column(
        JSON, default=dict
    )

    is_send = Column(
        Boolean, default=False
    )  # Записан ли экземпляр в таблицу
    is_processed = Column(
        Boolean, default=False
    )  # Обработан ли экземпляр
