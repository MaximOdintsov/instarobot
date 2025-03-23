import random
import asyncio
import click
import time
from aio_pika import connect_robust, Message, DeliveryMode

from robot.conf import settings
from robot.robot import parsing_account_info, check_error
from robot.helpers.selenium_management import save_screenshot
from robot.helpers.logs import capture_output_to_file
from robot.database.orm import get_engine_and_session, create_or_update_object
from robot.database.models import Account, ACCOUNT_STATUS
from robot.management.base import MultiInstagramAccountDriver


class RobotCommand(MultiInstagramAccountDriver):
    def __init__(self, account_indexes: list = []):
        auth_list = settings.AUTH_LIST_ACCOUNT_DATA_PARSER
        if account_indexes:
            auth_list = [auth_list[idx] for idx in account_indexes if -1 < idx < len(auth_list)]

        print(f'auth_list: {auth_list}')
        super().__init__(auth_list)

        self.driver = self.authenticate()
        self.channel = None
        self.async_engine, self.async_session = get_engine_and_session()

    async def account_data_parser(self, message):
        try:
            account_link = message.body.decode()
            print(f"Получена ссылка на аккаунт: {account_link}")

            self.driver.get(account_link)
            time.sleep(random.randrange(3, 5))
            
            # Проверка доступности страницы
            check_error(driver=self.driver)

            # Парсинг информации об аккаунте
            account_data = parsing_account_info(driver=self.driver, account_link=account_link)

            # Проверка данных на валидность (пусто или нет)
            data_is_empty = True
            for data_item in account_data.values():
                if data_item:
                    data_is_empty = False

            if data_is_empty is False:
                print(f"Найдены данные на странице аккаунта: {account_data}")

                print(f'Записываю данные аккаунта "{account_link}" в БД...')
                account_object = await create_or_update_object(
                    async_session_factory=self.async_session,
                    model=Account,
                    filters={'link': account_link},
                    defaults={'status': ACCOUNT_STATUS.POSTPROCESSING,
                              'data': account_data}
                )
                if account_object:
                    print(f'Сохранил аккаунт в БД: {account_object}')

                # Отправляем ссылку на аккаунт в соответствующую очередь
                print(f'Отправляю ссылку {account_link} в очередь "{settings.QUEUE_ACCOUNT_POSTS}"...')
                msg = Message(body=account_link.encode(), delivery_mode=DeliveryMode.PERSISTENT)
                await self.channel.default_exchange.publish(msg, routing_key=settings.QUEUE_ACCOUNT_POSTS)
                print(f'Ссылка на аккаунт "{account_link}" отправлена в очередь.')
            else:
                account_object = await create_or_update_object(
                    async_session_factory=self.async_session,
                    model=Account,
                    filters={'link': account_link},
                    defaults={'status': ACCOUNT_STATUS.FAILED}
                )
                if account_object:
                    print(f'Поставил аккаунт в статус Failed в БД: {account_object}')

                err_path = save_screenshot(driver=self.driver, img_name='account_parsing_error')
                print(f'Произошла ошибка парсинга аккаунта. Путь до скрина: {err_path}')

            await message.ack()  # Подтверждаем сообщение после успешной обработки
            time.sleep(random.randrange(5, 10))
        except Exception as e:
            print(f"Ошибка обработки: {e}")
            self.driver = self.switch_account()
            await message.reject(requeue=True)  # Отклоняем сообщение, чтобы оно осталось в очереди
            if not self.driver:
                await self.shutdown()

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
            await self.channel.declare_queue(settings.QUEUE_ACCOUNT_LINKS, durable=True)
            await self.channel.declare_queue(settings.QUEUE_ACCOUNT_POSTS, durable=True)
            # Получаем очередь для потребления сообщений
            queue = await self.channel.declare_queue(settings.QUEUE_ACCOUNT_LINKS, durable=True)
            # Запускаем потребление сообщений
            await queue.consume(self.account_data_parser)
            print("Ожидание сообщений. Для остановки нажмите CTRL+C")
            # Блокируем выполнение, чтобы держать соединение открытым
            await asyncio.Future()  # работает бесконечно


@click.command(name="account_data_parser")
@click.option("-ids", multiple=True, type=int, default=[])
@capture_output_to_file("account_data_parser")
def run(ids):
    command = RobotCommand(account_indexes=ids)
    asyncio.run(command.main())