import os
import uuid
import subprocess
from datetime import datetime
import click

from robot.conf import settings


def dump_postgres_db(db_name, user, password, host, port, output_file):
    # Формирование команды pg_dump с нужными параметрами.
    command = [
        "pg_dump",
        "-h", host,  # адрес сервера
        "-p", str(port),  # порт подключения
        "-U", user,  # пользователь
        "-F", "c",  # формат дампа (c - custom, можно использовать 'p' для plain SQL)
        "-b",  # включить большие объекты
        "-v",  # подробный вывод
        "-f", output_file,  # имя выходного файла
        db_name  # имя базы данных
    ]

    # Клонирование окружения и установка пароля в переменной окружения
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    try:
        # Выполнение команды pg_dump
        subprocess.run(command, env=env, check=True)
        print("Дамп базы данных успешно создан.")
    except subprocess.CalledProcessError as e:
        print("Ошибка при выполнении дампа:", e)


@click.command(name="db_dump")
def run():
    output_file = f'{settings.DB_DUMPS_ROOT}/{datetime.now().date()}_{uuid.uuid4()}.bak'
    dump_postgres_db(
        db_name=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        output_file=output_file
    )
