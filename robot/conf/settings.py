import yaml
import os
from dotenv import load_dotenv

SECRETS_PATH = '.env'
ROBOT_SETTINGS_PATH = 'robot.yaml'

# DATABASE
DB_USER = ''
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = ''

# MAIN PATHS
LOGS_ROOT = 'data/logs'
SCREENSHOT_ROOT = 'data/screenshots'
DB_DUMPS_ROOT = 'data/db_dumps'
COMMANDS_ROOT = 'robot/management/commands'
ACCOUNT_TYPE_MODEL_PATH = 'robot/ml/models/account_type_1.pkl'

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
RABBITMQ_USE = True
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_DEFAULT_USER = 'rabbit'
RABBITMQ_DEFAULT_PASS = 'rabbit'
QUEUE_POST_LINKS = 'post_links'
QUEUE_ACCOUNT_LINKS = 'account_links'
QUEUE_POSTPROCESS_ACCOUNTS = 'postprocess_accounts'
QUEUE_PREDICT_ACCOUNTS = 'predict_accounts'

# AUTH DATA: List[dict, dict]
AUTH_LIST_POST_LINKS_PARSER = []
AUTH_LIST_POST_DATA_PARSER = []
AUTH_LIST_ACCOUNT_DATA_PARSER = []
AUTH_LIST_ACCOUNT_POSTS_PARSER = []
AUTH_LIST_SPAM_ROBOT = []
SESSION_INSTAGRAM_COOKIES_PATH = 'data/instagram_cookies/'

# FOR ROBOTS
COMMENT_TEMPLATES = []
MESSAGE_TEMPLATES = []
QUERIES = []
ACCOUNT_LINKS_PATH = ''


# Переопределение дефолтных настроек
try:
    with open(ROBOT_SETTINGS_PATH, 'r', encoding='utf-8') as f:
        secrets = yaml.safe_load(f)
        for key, value in secrets.items():
            globals()[key] = value
        print(f'Переменные переопределены из файла {ROBOT_SETTINGS_PATH}')
except FileNotFoundError:
    print(f'Файл {ROBOT_SETTINGS_PATH} не найден. Используются настройки по умолчанию.')

load_dotenv(dotenv_path=SECRETS_PATH)
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER") or RABBITMQ_DEFAULT_USER
RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS") or RABBITMQ_DEFAULT_PASS


SQLALCHEMY_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
