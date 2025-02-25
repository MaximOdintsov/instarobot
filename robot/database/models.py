import enum

from sqlalchemy import DateTime, JSON, Enum, func, Table, ForeignKey, Column, Integer, String, text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    create_datetime = Column(DateTime, default=func.now())
    modify_datetime = Column(DateTime, default=func.now(), onupdate=func.now())


class ACCOUNT_STATUS(enum.IntEnum):
    PARSING = 5
    POSTPROCESSING = 15
    FAILED = 20
    READY = 30
    ANNOTATED = 40
    VALIDATED = 100


# class POST_STATUS(enum.IntEnum):
#     PARSING = 5
#     READY = 10


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
        Integer,
        nullable=False,
        default=ACCOUNT_STATUS.PARSING,
        server_default=text("5")
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
    # status = Column(
    #     Integer,
    #     nullable=False,
    #     default=POST_STATUS.PARSING,
    #     server_default=text("5")
    # )
    # Добавляем отношение "многие ко многим" к аккаунтам
    accounts = relationship(
        "Account",
        secondary=account_post_association,
        back_populates="posts"
    )

