import uuid
import asyncio
import click
from aio_pika import connect_robust, Message, DeliveryMode

from robot.conf import settings
from robot.robot import post_parsing
from robot.helpers.utils import validate_instagram_url, ACCOUNT_VALUE
from robot.helpers.logs import capture_output_to_file
from robot.database.orm import get_engine_and_session, get_object_by_filter, create_or_update_object
from robot.database.models import Account, ACCOUNT_STATUS
from robot.management.base import MultiInstagramAccountDriver


class RobotCommand(MultiInstagramAccountDriver):
    def __init__(self, account_indexes: list = []):
        auth_list = settings.AUTH_LIST_POST_DATA_PARSER
        if account_indexes:
            auth_list = [auth_list[idx] for idx in account_indexes if -1 < idx < len(auth_list)]

        print(f'auth_list: {auth_list}')
        super().__init__(auth_list)

        self.driver = self.authenticate()
        self.channel = None
        self.async_engine, self.async_session = get_engine_and_session()

    async def post_data_parser(self, message):
        # Автоматическое подтверждение сообщения через контекстный менеджер
        try:
            post_link = message.body.decode()
            print(f"Получена ссылка на пост: {post_link}")

            # Обработка поста для получения ссылок на аккаунты
            account_links = post_parsing(driver=self.driver, post_link=post_link)

            ## FIXME ТУТ НУЖНО ПРИВЯЗАТЬ ПОСТ К АККАУНТУ + ОТДАТЬ ОСТАВШИЕСЯ НАЙДЕННЫЕ АККАУНТЫ
            ## FIXME ТУТ ВЗЯТЬ ДАННЫЕ С ПОСТА: ОПИСАНИЕ + ХЭШТЕГИ, ВЛАДЕЛЬЦА, КОЛ-ВО ЛАЙКОВ И ТД

            if not account_links:
                err_path = f'data/img_error/post-error-{uuid.uuid4()}.img'
                self.driver.save_screenshot(err_path)
                self.driver = self.switch_account()
                raise Exception(f'Произошла ошибка парсинга поста. Путь: {err_path}')
            print(f"Найдено {len(account_links)} ссылок на посты")

            for idx, account_link in enumerate(account_links):
                print(f'Проверка ссыки #{idx}: {account_link}')
                if validate_instagram_url(account_link) != ACCOUNT_VALUE:
                    print(f'Пропускаю ссылку "{account_link}" из-за несоответствия шаблону.')
                    continue

                print(f'Проверяю ссылку на аккаунт: {account_link}...')
                account_object = await get_object_by_filter(
                    async_session_factory=self.async_session,
                    model=Account,
                    filters={'link': account_link}
                )
                if account_object:
                    print(f'Аккаунт с ссылкой {account_link} уже есть в БД, пропускаю...')
                    continue

                print(f'Создаю аккаунт: "{account_link}"...')
                account_object = await create_or_update_object(
                    async_session_factory=self.async_session,
                    model=Account,
                    filters={'link': account_link},
                    defaults={'link': account_link, 'status': ACCOUNT_STATUS.PARSING}
                )
                if account_object:
                    print(f'Сохранил аккаунт в БД: {account_object}')

                print(f'Отправляю ссылку {account_link} в очередь "{settings.QUEUE_ACCOUNT_LINKS}"...')
                # Отправляем ссылку на аккаунт в соответствующую очередь
                msg = Message(
                    body=account_link.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                )
                await self.channel.default_exchange.publish(msg, routing_key=settings.QUEUE_ACCOUNT_LINKS)
                print(f'Ссылка на аккаунт "{account_link}" отправлена в очередь "{settings.QUEUE_ACCOUNT_LINKS}".')
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
@click.option("-ids", multiple=True, type=int, default=[])
@capture_output_to_file("post_data_parser")
def run(ids):
    print(f'account_ids: {ids}')
    command = RobotCommand(account_indexes=ids)
    asyncio.run(command.main())