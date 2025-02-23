import asyncio
import random
import click
from aio_pika import connect_robust, Message, DeliveryMode

from robot.robot import turn_to_posts_page, get_post_links
from robot.conf import settings
from robot.helpers.utils import validate_instagram_url, POST_VALUE
from robot.database.models import AccountPost
from robot.database.orm import async_session, get_object_by_filter, create_or_update_object
from robot.helpers.logs import capture_output_to_file
from robot.management.base import MultiInstagramAccountDriver


async def main(max_scrolls: int):
    # Авторизация
    account_manager = MultiInstagramAccountDriver(settings.AUTH_LIST_POST_LINKS)
    driver = account_manager.authenticate()

    # Устанавливаем асинхронное соединение с RabbitMQ
    connection = await connect_robust(
        f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
    )

    async with connection:
        channel = await connection.channel()
        # Объявляем очередь для отправки ссылок на посты
        await channel.declare_queue(settings.QUEUE_POST_LINKS, durable=True)

        for query in settings.QUERIES:
            query_str = f'%23{query}'  # '%23' == '#'
            print(f'Поиск постов по хэштегу: #{query_str}')

            posts_found = turn_to_posts_page(driver=driver, query=query_str)
            if posts_found is False:
                continue

            post_links = set()
            for scroll in range(max_scrolls):
                new_links, page_end = get_post_links(driver=driver, wait_time=5)
                post_links.update(new_links)
                if page_end:
                    break
            print(f"Найдено {len(post_links)} ссылок на посты")

            # Валидация ссылок, запись в базу и отправка в очередь
            for post_link in post_links:
                if validate_instagram_url(post_link) != POST_VALUE:
                    print(f'Пропускаем ссылку "{post_link}" из-за несоответствия шаблону.')
                    continue

                post_object = await get_object_by_filter(
                    async_session_factory=async_session,
                    model=AccountPost,
                    filters={'link': post_link}
                )
                if post_object:
                    print(f'Такой пост уже есть в БД. Пропускаем.')
                    continue

                await create_or_update_object(
                    async_session_factory=async_session,
                    model=AccountPost,
                    filters={'link': post_link},
                    defaults={'link': post_link}
                )
                msg = Message(
                    body=post_link.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                )
                await channel.default_exchange.publish(msg, routing_key=settings.QUEUE_POST_LINKS)
                print(f'Ссылка на пост "{post_link}" отправлена в очередь.')
            # Пауза между итерациями для имитации задержки
            await asyncio.sleep(random.randrange(5, 10))


@click.option("--max-scrolls", default=2, help="Количество прокруток страницы вниз при парсинге постов")
@click.command(name="post_links_parser")
@capture_output_to_file("post_links_parser")
def run(max_scrolls):
    asyncio.run(main(max_scrolls))
