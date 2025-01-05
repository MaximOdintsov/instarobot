# DATABASE
DB_PATH = "data/db/instagram.db"
SQLALCHEMY_URL = f"sqlite:///{DB_PATH}"
DATABASE_URL = F"sqlite+aiosqlite:///{DB_PATH}"


# PATHS
AUTH_DATA_PATH = 'data/in/auth_data.json'

QUERIES_PATH = 'data/in/queries.json'
INSTA_ACCOUNTS_DATA_PATH = 'data/out/insta_accounts.xlsx'

MESSAGE_TEMPLATES_PATH = 'data/in/message_templates.json'
COMMENT_TEMPLATES_PATH = 'data/in/comment_templates.json'
ACCOUNT_LINKS_PATH = 'data/in/account_links.txt'

# MODELS
ACCOUNT_TYPE_MODEL_PATH = 'data/modеls/account_type.pkl'


# Сон после обработки аккаунта
ACCOUNT_BREAK_MIN_TIME = 5
ACCOUNT_BREAK_MAX_TIME = 10


# Интервал после каждого действия (подписка, отправка сообщения, отправка комментария)
ACTION_BREAK_MIN_TIME = 5
ACTION_BREAK_MAX_TIME = 10
