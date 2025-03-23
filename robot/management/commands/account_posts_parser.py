import sys
import random
import time
import uuid
import asyncio
import click
from selenium.webdriver.common.keys import Keys
from aio_pika import connect_robust, Message, DeliveryMode

from robot.conf import settings
from robot.robot import post_parsing, get_account_posts_elements, get_post_accounts_links, parsing_post_data
from robot.helpers.utils import validate_instagram_url, ACCOUNT_VALUE, POST_VALUE
from robot.helpers.logs import capture_output_to_file
from robot.helpers.selenium_management import open_link
from robot.database.orm import get_engine_and_session, get_object_by_filter, create_or_update_object
from robot.database.models import Account, AccountPost, ACCOUNT_STATUS, POST_STATUS
from robot.management.base import MultiInstagramAccountDriver
    

class RobotCommand(MultiInstagramAccountDriver):
    def __init__(self, account_indexes: list = []):
        auth_list = settings.AUTH_LIST_ACCOUNT_POSTS_PARSER
        if account_indexes:
            auth_list = [auth_list[idx] for idx in account_indexes if -1 < idx < len(auth_list)]
        print(f'auth_list: {auth_list}')
        super().__init__(auth_list)

        self.driver = self.authenticate()
        self.channel = None
        self.async_engine, self.async_session = get_engine_and_session()

    async def account_posts_parser(self, message):
        # Автоматическое подтверждение сообщения через контекстный менеджер
        try:
            account_link = message.body.decode()
            print(f"Получена ссылка на аккаунт: {account_link}")
            account_object = await get_object_by_filter(
                async_session_factory=self.async_session,
                model=Account,
                filters={'link': account_link}
            )
            if not account_object:
                raise Exception(f'Аккаунт {account_link} не существует в БД.')

            # Переход на страницу аккаунта
            open_link(driver=self.driver, link=account_link)
            time.sleep(random.randrange(6, 9))

            # Парсинг постов аккаунта
            account_post_elements = get_account_posts_elements(driver=self.driver)
            if (account_object.data.get('posts', 0) > 0) and (len(account_post_elements) == 0):
                raise Exception(f'У аккаунта "{account_link}" не найдены посты!')

            for elem in account_post_elements:
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                elem.click()
                time.sleep(random.randrange(5, 15))

                # Сохранение ссылок на аккаунты, найденные в посте
                all_account_links = get_post_accounts_links(driver=self.driver)
                for idx, link in enumerate(all_account_links):
                    print(f'Проверка ссыки #{idx}: {link}')
                    if validate_instagram_url(link) != ACCOUNT_VALUE:
                        print(f'Пропускаю ссылку "{link}" из-за несоответствия шаблону.')
                        continue

                    print(f'Проверяю аккаунт в БД: "{link}"...')
                    new_account_object = await get_object_by_filter(
                        async_session_factory=self.async_session,
                        model=Account,
                        filters={'link': link}
                    )
                    if new_account_object:
                        print(f'Аккаунт с ссылкой {link} уже есть в БД, пропускаю...')
                        continue

                    print(f'Создаю аккаунт в БД: "{link}"...')
                    new_account_object = await create_or_update_object(
                        async_session_factory=self.async_session,
                        model=Account,
                        filters={'link': link},
                        defaults={'link': link, 'status': ACCOUNT_STATUS.PARSING}
                    )
                    if new_account_object:
                        print(f'Сохранил аккаунт в БД: {new_account_object}.')
                        print(f'Отправляю ссылку {link} в очередь "{settings.QUEUE_ACCOUNT_LINKS}"...')
                        msg = Message(body=link.encode(), delivery_mode=DeliveryMode.PERSISTENT)
                        await self.channel.default_exchange.publish(msg, routing_key=settings.QUEUE_ACCOUNT_LINKS)
                        print(f'Ссылка на аккаунт "{link}" отправлена в очередь.')
                    else:
                        raise Exception(f'Ошибка сохранения данных в БД')

                # Парсинг данных поста и привязка их к аккаунту
                post_header, post_description, post_likes = parsing_post_data(self.driver)
                print(f'post_header, post_description, post_likes: {post_header, post_description, post_likes}')
                if post_header or post_description or post_likes:
                    post_link = self.driver.current_url
                    if validate_instagram_url(post_link) != POST_VALUE:
                        print(f'Пропускаю ссылку "{post_link}" из-за несоответствия шаблону.')
                        continue

                    print(f'Записываю данные о посте: {post_link}...')
                    post_object = await create_or_update_object(
                        async_session_factory=self.async_session,
                        model=AccountPost,
                        filters={'link': post_link},
                        defaults={
                            'data': {
                                'post_header': post_header,
                                'post_description': post_description,
                                'post_likes': post_likes
                            },
                            'status': POST_STATUS.ANNOTATED
                        }
                    )
                    if post_object:
                        print(f'Сохранил пост в БД: {post_object}')
                        async with self.async_session() as session:
                            account_object = await session.merge(account_object)
                            post_object = await session.merge(post_object)

                            # Проверяем, нет ли account в post_object.accounts
                            if all(a.id != account_object.id for a in post_object.accounts):
                                print(f'Аккаунта нет в post_object.accounts: "{post_object.accounts}". Добавляю...')
                                post_object.accounts.append(account_object)

                            await session.commit()
                            print(f'Закоммитил. post_object.accounts: {post_object.accounts}')
                    else:
                        raise Exception(f'Ошибка сохранения данных в БД')

            print(f'Обновляю статус аккаунта "{account_link}" в БД...')
            account_object = await create_or_update_object(
                async_session_factory=self.async_session,
                model=Account,
                filters={'link': account_link},
                defaults={'status': ACCOUNT_STATUS.PREDICTING}
            )
            if account_object:
                print(f'Сохранил аккаунт в БД: {account_object}')

                print(f'Отправляю ссылку {account_link} в очередь "{settings.QUEUE_PREDICT_ACCOUNTS}"...')
                msg = Message(body=account_link.encode(), delivery_mode=DeliveryMode.PERSISTENT)
                await self.channel.default_exchange.publish(msg, routing_key=settings.QUEUE_PREDICT_ACCOUNTS)
                print(f'Ссылка на аккаунт "{account_link}" отправлена в очередь.')

                await message.ack()  # Подтверждаем сообщение после успешной обработки
            else:
                raise Exception(f'Ошибка сохранения данных в БД')
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
            await self.channel.declare_queue(settings.QUEUE_ACCOUNT_POSTS, durable=True)
            await self.channel.declare_queue(settings.QUEUE_ACCOUNT_LINKS, durable=True)
            await self.channel.declare_queue(settings.QUEUE_PREDICT_ACCOUNTS, durable=True)
            # Получаем очередь для потребления сообщений
            queue = await self.channel.declare_queue(settings.QUEUE_ACCOUNT_POSTS, durable=True)
            # Запускаем потребление сообщений
            await queue.consume(self.account_posts_parser)
            print("Ожидание сообщений. Для остановки нажмите CTRL+C")
            # Блокируем выполнение, чтобы держать соединение открытым
            await asyncio.Future()  # работает бесконечно


@click.command(name="account_posts_parser")
@click.option("-ids", multiple=True, type=int, default=[])
@capture_output_to_file("account_posts_parser")
def run(ids):
    print(f'account_ids: {ids}')
    command = RobotCommand(account_indexes=ids)
    asyncio.run(command.main())