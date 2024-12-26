# DATABASE
DB_PATH = "data/db/instagram.db"
SQLALCHEMY_URL = f"sqlite:///{DB_PATH}"
DATABASE_URL = F"sqlite+aiosqlite:///{DB_PATH}"


# PATHS
AUTH_DATA_PATH = 'data/incoming_data/auth_path.json'
# for parser
QUERIES_PATH = 'data/incoming_data/queries.json'
INSTA_ACCOUNTS_DATA_PATH = 'data/out/insta_accounts.xlsx'
# for send_messages
MESSAGE_TEMPLATES_PATH = 'data/incoming_data/message_templates.json'
ACCOUNT_LINKS_PATH = 'data/incoming_data/account_links.txt'
