import asyncio
import random
import click
from aio_pika import connect_robust, Message, DeliveryMode

from robot.robot import turn_to_posts_page, get_post_links
from robot.conf import settings
from robot.helpers.utils import validate_instagram_url, POST_VALUE
from robot.database.models import AccountPost
from robot.database.orm import get_engine_and_session, get_object_by_filter, create_or_update_object
from robot.helpers.logs import capture_output_to_file
from robot.management.base import MultiInstagramAccountDriver


class RobotCommand(MultiInstagramAccountDriver):
    def __init__(self, max_scrolls: int):
        super().__init__(settings.AUTH_LIST_POST_DATA_PARSER)
        self.driver = self.authenticate()
        self.channel = None
        self.max_scrolls = max_scrolls
        self.async_engine, self.async_session = get_engine_and_session()

    async def query_process(self, query: str):
        print(f'Поиск постов по хэштегу: {query}')
        posts_found = turn_to_posts_page(driver=self.driver, query=query)
        if posts_found is False:
            return

        post_links = set()
        for scroll in range(self.max_scrolls):
            new_links, page_end = get_post_links(driver=self.driver, wait_time=5)
            post_links.update(new_links)
            if page_end:
                break
        print(f"Найдено {len(post_links)} ссылок на посты")

        # Валидация ссылок, запись в базу и отправка в очередь
        for idx, post_link in enumerate(post_links):
            print(f'Проверка ссылки #{idx}: {post_link}')
            if validate_instagram_url(post_link) != POST_VALUE:
                print(f'Пропускаю ссылку "{post_link}" из-за несоответствия шаблону.')
                continue

            print(f'Проверяю ссылку на пост: {post_link}...')
            post_object = await get_object_by_filter(
                async_session_factory=self.async_session,
                model=AccountPost,
                filters={'link': post_link}
            )
            if post_object:
                print(f'Пост с ссылкой {post_link} уже есть в БД, пропускаю...')
                continue

            print(f'Создаю пост: {post_link}...')
            post_object = await create_or_update_object(
                async_session_factory=self.async_session,
                model=AccountPost,
                filters={'link': post_link},
                defaults={'link': post_link}
            )
            if post_object:
                print(f'Сохранил пост в БД: {post_object}')

            print(f'Отправляю ссылку {post_link} в очередь "{settings.QUEUE_POST_LINKS}"...')
            msg = Message(
                body=post_link.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
            )
            await self.channel.default_exchange.publish(msg, routing_key=settings.QUEUE_POST_LINKS)
            print(f'Ссылка на пост "{post_link}" отправлена в очередь "{settings.QUEUE_POST_LINKS}".')
        return True

    async def main(self):
        # Устанавливаем асинхронное соединение с RabbitMQ
        connection = await connect_robust(
            f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        )

        print(f'Подключился к очереди: {connection}')
        async with connection:
            self.channel = await connection.channel()
            # Объявляем очередь для отправки ссылок на посты
            await self.channel.declare_queue(settings.QUEUE_POST_LINKS, durable=True)

            for query in settings.QUERIES:
                query = f'%23{query}'  # '%23' == '#'
                await self.query_process(query=query)
                await asyncio.sleep(random.randrange(5, 10))  # Пауза между итерациями для имитации задержки


@click.option("--max-scrolls", default=2, help="Количество прокруток страницы вниз при парсинге постов")
@click.command(name="post_links_parser")
@capture_output_to_file("post_links_parser")
def run(max_scrolls):
    command = RobotCommand(max_scrolls)
    asyncio.run(command.main())