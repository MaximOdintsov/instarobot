import yaml

# DATABASE
DB_PATH = "data/db/instagram.db"
SQLALCHEMY_URL = f"sqlite:///{DB_PATH}"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# PATHS
LOGS_ROOT = 'data/logs'
COMMANDS_ROOT = 'robot/commands'

#AUTH_DATA_PATH = 'data/in/auth_data.json'
QUERIES_PATH = 'data/in/queries.json'
INSTA_ACCOUNTS_DATA_PATH = 'data/out/insta_accounts.xlsx'
POST_LINKS_PATH = 'data/in/post_links.json'
MESSAGE_TEMPLATES_PATH = 'data/in/message_templates.json'
COMMENT_TEMPLATES_PATH = 'data/in/comment_templates.json'
ACCOUNT_LINKS_PATH = 'data/in/account_links.txt'

# MODELS
ACCOUNT_TYPE_MODEL_PATH = 'data/modеls/account_type_1.pkl'


# Сон после обработки аккаунта
ACCOUNT_BREAK_MIN_TIME = 5
ACCOUNT_BREAK_MAX_TIME = 10


# Интервал после каждого действия (подписка, отправка сообщения, отправка комментария)
ACTION_BREAK_MIN_TIME = 5
ACTION_BREAK_MAX_TIME = 10


# GOOGLE TABLES
GOOGLE_API_TOKEN_PATH = ''
GOOGLE_TABLE_NAME = ''
GOOGLE_WORKSHEET_NAME = ''
UPDATE_ERROR_LOGS_PATH = 'data/logs/update_db_error.log'

# RABBITMQ
QUEUE_POST_LINKS = ''
QUEUE_ACCOUNT_LINKS = ''
QUEUE_ACCOUNT_DATA = ''

# AUTH DATA: List[dict, dict]
AUTH_LIST_POST_LINKS = []
AUTH_LIST_POST_DATA_PARSER = []
AUTH_LIST_ACCOUNT_DATA_PARSER = []


# Переопределение настроек
file_path = 'robot.yaml'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        print(f'Переопределяю настройки из файла {file_path}')
        # Используем safe_load для безопасности
        secrets = yaml.safe_load(f)
        for key, value in secrets.items():
            globals()[key] = value
except FileNotFoundError:
    print(f'Файл {file_path} не найден. Используются настройки по умолчанию.')
