# DATABASE
DB_PATH = "data/db/instagram.db"
SQLALCHEMY_URL = f"sqlite:///{DB_PATH}"
DATABASE_URL = F"sqlite+aiosqlite:///{DB_PATH}"


# PATHS
QUERIES_PATH = 'data/incoming_data/queries.txt'
AUTH_DATA_PATH = 'data/incoming_data/auth_path.json'
MESSAGE_TEMPLATES_PATH = 'data/incoming_data/message_templates.txt'
INSTA_ACCOUNTS_DATA_PATH = 'data/out/insta_accounts.xlsx'
