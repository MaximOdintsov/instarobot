import enum

from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Boolean, func, Table, ForeignKey

from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String


class Base(DeclarativeBase):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_datetime = Column(DateTime, default=func.now())
    modify_datetime = Column(DateTime, onupdate=func.now())


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


account_post_association = Table(
    'account_post_association',
    Base.metadata,
    Column('account_id', Integer, ForeignKey('accounts.id')),
    Column('account_post_id', Integer, ForeignKey('account_posts.id'))
)


class Account(Base):
    __tablename__ = 'accounts'

    link = Column(String, unique=True, nullable=False)
    data = Column(JSON, default=dict)
    status = Column(
        Enum(STATUS, name='status_enum'), nullable=False, default=STATUS.PARSING, server_default='PARSING'
    )
    account_type = Column(
        Enum(AccountType, name='account_type_enum'), nullable=False, default=AccountType.UNKNOWN
    )
    # Добавляем отношение "многие ко многим" к постам
    posts = relationship(
        "AccountPost",
        secondary=account_post_association,
        back_populates="accounts"
    )


class AccountPost(Base):
    __tablename__ = 'account_posts'

    link = Column(String, unique=True, nullable=False)
    data = Column(JSON, default=dict)

    # Добавляем отношение "многие ко многим" к аккаунтам
    accounts = relationship(
        "Account",
        secondary=account_post_association,
        back_populates="posts"
    )

