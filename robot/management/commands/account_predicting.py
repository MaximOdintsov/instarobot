import asyncio
import click
import pandas as pd
from aio_pika import connect_robust

from robot.conf import settings
from robot.helpers.utils import extract_original_link, extract_emails
from robot.helpers.logs import capture_output_to_file
from robot.database.orm import get_engine_and_session, create_or_update_object, get_object_by_filter
from robot.database.models import Account, ACCOUNT_STATUS, AccountType
from robot.ml.predicting import get_account_type


class RobotCommand:
    def __init__(self):
        self.channel = None
        self.async_engine, self.async_session = get_engine_and_session()

    async def account_predicting(self, message):
        try:
            account_link = message.body.decode()
            print(f"Получена ссылка на аккаунт: {account_link}")

            account_object = await get_object_by_filter(
                async_session_factory=self.async_session,
                model=Account,
                filters={'link': account_link}
            )
            if account_object:
                data = account_object.data
                data['description'] = data['description'] or ''
                data['emails'] = extract_emails(data.get('description', ''))
                data['links_description'] = [extract_original_link(link) for link in data.get('links_description', [])]
                data['links_contacts'] = [extract_original_link(link) for link in data.get('links_contacts', [])]

                print(f'data: {data}')

                # Предсказание типа аккаунта
                df = pd.DataFrame({
                    'Описание страницы': [data.get('description', '')],
                    'Ссылки из описания': [data.get('links_description', [])],
                    'Ссылки из контактов': [data.get('links_contacts', [])],
                    'Почта существует': [1 if data.get('emails', '') else 0],
                    'Кол-во постов': [data.get('posts', '')]
                })
                print(f'df: {df}')

                predicted_account_type = get_account_type(data=df, threshold=0.8).value
                data['predicted_account_type'] = predicted_account_type
                print(f'Предсказал тип аккаунта: "{predicted_account_type}"')

                print(f'Записываю данные аккаунта "{account_link}" в БД...')
                account_object = await create_or_update_object(
                    async_session_factory=self.async_session,
                    model=Account,
                    filters={'link': account_link},
                    defaults={'account_type': AccountType(data['predicted_account_type']),
                              'status': ACCOUNT_STATUS.READY,
                              'data': data}
                )
                if account_object:
                    print(f'Сохранил аккаунт в БД: {account_object}')
            else:
                print(f'Аккаунта "{account_link}" нет в БД!')
            await message.ack()  # Подтверждаем сообщение после успешной обработки
        except Exception as e:
            print(f"Ошибка обработки: {e}")
            await message.reject(requeue=True)  # Отклоняем сообщение, чтобы оно осталось в очереди

    async def main(self):
        connection = await connect_robust(
            f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        )
        async with connection:
            # Создаем канал
            self.channel = await connection.channel()
            # Ограничиваем количество не подтверждённых сообщений до 1
            await self.channel.set_qos(prefetch_count=1)
            # Объявляем очереди (если их ещё нет)
            await self.channel.declare_queue(settings.QUEUE_PREDICT_ACCOUNTS, durable=True)
            # Получаем очередь для потребления сообщений
            queue = await self.channel.declare_queue(settings.QUEUE_PREDICT_ACCOUNTS, durable=True)
            # Запускаем потребление сообщений
            await queue.consume(self.account_predicting)
            print("Ожидание сообщений. Для остановки нажмите CTRL+C")
            # Блокируем выполнение, чтобы держать соединение открытым
            await asyncio.Future()  # работает бесконечно


@click.command(name="account_predicting")
@capture_output_to_file("account_predicting")
def run():
    command = RobotCommand()
    asyncio.run(command.main())