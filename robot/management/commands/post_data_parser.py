import uuid
import asyncio
import click
from aio_pika import connect_robust, Message, DeliveryMode


from robot.conf import settings
from robot.robot import post_parsing
from robot.helpers.utils import validate_instagram_url, ACCOUNT_VALUE
from robot.helpers.logs import capture_output_to_file
from robot.database.orm import async_session, get_object_by_filter, create_or_update_object
from robot.database.models import Account, STATUS
from robot.management.base import MultiInstagramAccountDriver


class RobotCommand(MultiInstagramAccountDriver):

    def __init__(self):
        super().__init__(settings.AUTH_LIST_POST_DATA_PARSER)
        self.driver = self.authenticate()
        self.channel = None
        self.db_lock = asyncio.Lock()

    async def post_data_parser(self, message):
        # Автоматическое подтверждение сообщения через контекстный менеджер
        try:
            post_link = message.body.decode()
            print(f"Получена ссылка на пост: {post_link}")

            # Обработка поста для получения ссылок на аккаунты
            account_links = post_parsing(driver=self.driver, post_link=post_link)
            if not account_links:
                err_path = f'data/img_error/post-error-{uuid.uuid4()}.img'
                self.driver.save_screenshot(err_path)
                self.driver = self.switch_account()
                raise Exception(f'Произошла ошибка парсинга поста. Путь: {err_path}')
            print(f'Ссылок на аккаунты: {len(account_links)}')

            for idx, account_link in enumerate(account_links):
                print(f'Проверка ссыки #{idx}...')
                if validate_instagram_url(account_link) != ACCOUNT_VALUE:
                    print(f'Пропускаем ссылку "{account_link}" из-за несоответствия шаблону.')
                    continue
                async with self.db_lock:
                    print(f'Проверяю ссылку на аккаунт: {account_link}...')
                    account_object = await get_object_by_filter(
                        async_session_factory=async_session,
                        model=Account,
                        filters={'link': account_link}
                    )
                    if not account_object:
                        print(f'Создаем аккаунт...')
                        await create_or_update_object(
                            async_session_factory=async_session,
                            model=Account,
                            filters={'link': account_link},
                            defaults={'link': account_link, 'status': STATUS.PARSING}
                        )
                        print(f'Отправляем ссылку на аккаунт в соответствующую очередь...')
                        # Отправляем ссылку на аккаунт в соответствующую очередь
                        msg = Message(
                            body=account_link.encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                        )
                        await self.channel.default_exchange.publish(msg, routing_key=settings.QUEUE_ACCOUNT_LINKS)
                        print(f'Ссылка на аккаунт "{account_link}" отправлена в очередь.')
                    else:
                        print(f'Такой аккаунт уже есть в БД. Пропускаем.')
                        continue
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
            await self.channel.declare_queue(settings.QUEUE_POST_LINKS, durable=True)
            await self.channel.declare_queue(settings.QUEUE_ACCOUNT_LINKS, durable=True)
            # Получаем очередь для потребления сообщений
            queue = await self.channel.declare_queue(settings.QUEUE_POST_LINKS, durable=True)
            # Запускаем потребление сообщений
            await queue.consume(self.post_data_parser)
            print("Ожидание сообщений. Для остановки нажмите CTRL+C")
            # Блокируем выполнение, чтобы держать соединение открытым
            await asyncio.Future()  # работает бесконечно


@click.command(name="post_data_parser")
@capture_output_to_file("post_data_parser")
def run():
    command = RobotCommand()
    asyncio.run(command.main())