import yaml

# DATABASE
DB_PATH = "data/db/instagram.db"
SQLALCHEMY_URL = f"sqlite:///{DB_PATH}"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


# MAIN PATHS
LOGS_ROOT = 'data/logs'
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
RABBITMQ_USE = False
RABBITMQ_HOST = ''
RABBITMQ_PORT = ''
RABBITMQ_SECRETS = 'rabbitmq/secrets.env'
QUEUE_POST_LINKS = ''
QUEUE_ACCOUNT_LINKS = ''
QUEUE_ACCOUNT_DATA = ''


# AUTH DATA: List[dict, dict]
AUTH_LIST_POST_LINKS = []
AUTH_LIST_POST_DATA_PARSER = []
AUTH_LIST_ACCOUNT_DATA_PARSER = []
AUTH_LIST_SPAM_ROBOT = []


# FOR ROBOTS
COMMENT_TEMPLATES = []
MESSAGE_TEMPLATES = []
QUERIES = []
ACCOUNT_LINKS_PATH = ''


# Переопределение дефолтных настроек
ROBOT_SETTINGS_PATH = 'robot.yaml'
try:
    with open(ROBOT_SETTINGS_PATH, 'r', encoding='utf-8') as f:
        print(f'Переопределяю настройки из файла {ROBOT_SETTINGS_PATH}')
        # Используем safe_load для безопасности
        secrets = yaml.safe_load(f)
        for key, value in secrets.items():
            globals()[key] = value
except FileNotFoundError:
    print(f'Файл {ROBOT_SETTINGS_PATH} не найден. Используются настройки по умолчанию.')



if RABBITMQ_USE is True:
    from pika import ConnectionParameters, PlainCredentials
    import os
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=RABBITMQ_SECRETS)
    RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
    RABBITMQ_DEFAULT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
    RABBITMQ_CONNECTION = ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=PlainCredentials(username=RABBITMQ_DEFAULT_USER, password=RABBITMQ_DEFAULT_PASS)
    )


