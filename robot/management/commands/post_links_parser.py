import time
import random
import asyncio
import click
from pika import BlockingConnection, BasicProperties

from robot.robot import turn_to_posts_page, get_post_links
from robot.conf import settings
from robot.helpers.utils import validate_instagram_url, POST_VALUE
from robot.database.models import AccountPost
from robot.database.orm import async_session, get_object_by_filter
from robot.helpers.logs import capture_output_to_file
from robot.management.base import MultiInstagramAccountDriver


async def main(max_scrolls: int):
    # Авторизация
    account_manager = MultiInstagramAccountDriver(settings.AUTH_LIST_POST_LINKS)
    driver = account_manager.authenticate()

    for query in settings.QUERIES:
        query = f'%23{query}'  # '%23' == '#'
        print(f'Поиск постов по хэштегу: #{query}')

        # Переход на страницу с постами
        posts_found = turn_to_posts_page(driver=driver, query=query)
        if posts_found is False:
            continue

        # Получение ссылок на пост
        post_links = set()
        for scroll in range(max_scrolls):
            new_links, page_end = get_post_links(driver=driver, wait_time=5)
            post_links.update(new_links)
            if page_end:
                break
        print(f"Найдено {len(post_links)} ссылок на посты")

        # Валидация и отправка ссылок в очередь
        with BlockingConnection(settings.RABBITMQ_CONNECTION) as conn:
            with conn.channel() as ch:
                ch.queue_declare(queue=settings.QUEUE_POST_LINKS, durable=True)  # Создание очереди
                for post_link in post_links:
                    if validate_instagram_url(post_link) != POST_VALUE:
                        print(f'Пропускаем ссылку "{post_link}" из-за несоответствия шаблону.')
                        continue

                    post_object = await get_object_by_filter(
                        async_session_factory=async_session,
                        model=AccountPost,
                        filters={'link': post_link}
                    )
                    if not post_object:
                        ch.basic_publish(
                            exchange="",
                            routing_key=settings.QUEUE_POST_LINKS,  # Выбор очереди
                            body=str(post_link),
                            properties=BasicProperties(delivery_mode=2)  # Persistent сообщение
                        )
                        print(f'Ссылка "{post_link}" отправлена в очередь.')
        time.sleep(random.randrange(5, 10))


@click.option("--max-scrolls", default=2, help="Количество прокруток страницы вниз при парсинге постов")
@click.command(name="post_links_parser")
@capture_output_to_file("post_links_parser")
def run(max_scrolls):
    asyncio.run(main(max_scrolls))