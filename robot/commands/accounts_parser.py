import time
import random
import json
import asyncio
import click
import pandas as pd
from selenium import webdriver

from robot.helpers.selenium_management import start_driver, close_driver
from robot.helpers.utils import (
    extract_emails,
    validate_instagram_url,
    POST_VALUE,
    ACCOUNT_VALUE
)
from robot.database.orm import  async_session, create_or_update_object, get_object_by_filter, get_objects_by_filter
from robot.helpers.excel import write_excel
from robot.robot import (
    auth,
    turn_to_posts_page,
    get_post_links,
    accounts_parsing,
    parsing_account_info
)
from robot import config
from robot.ml.predicting import get_account_type
from robot.database.models import Account, AccountType, STATUS


def account_links_parsing(driver: webdriver, post_query: str, max_scrolls: int):
    """
    1 шаг: Переход на страницу с постами и парсинг ссылок на посты
    2 шаг: Парсинг ссылок на аккаунты
    """
    account_links = []
    posts_found = turn_to_posts_page(driver=driver, query=post_query)
    if posts_found is False:
        return 0

    # Получение старых ссылок на посты
    with open(config.POST_LINKS_PATH, 'r') as f:
        old_post_links = json.load(f)

    # Парсинг ссылок на посты
    post_links = list(get_post_links(driver, max_scrolls=max_scrolls))
    post_links = [
        link for link in post_links
        if (validate_instagram_url(link) == POST_VALUE) and (link not in old_post_links)
    ]
    print(f"Найдено {len(post_links)} ссылок на посты")

    # Парсинг ссылок на аккаунты
    for idx, post_link in enumerate(post_links[:2]):
        print(f'Парсинг поста #{idx}. Ссылка: {post_link}')
        raw_account_links = accounts_parsing(driver=driver, post_link=post_link)
        for account_link in raw_account_links:
            if validate_instagram_url(account_link) == ACCOUNT_VALUE:
                account_links.append(account_link)
        time.sleep(1)
        # time.sleep(random.randrange(10, 60))

    # Запись новых ссылок на посты в файл
    with open(config.POST_LINKS_PATH, 'w') as f:
        merged_post_links = list(set(old_post_links + post_links))
        f.write(json.dumps(merged_post_links, indent=4))

    return account_links


def account_data_parser(driver: webdriver, account_link: str, post_query: str):
    """Парсит данные конкретного аккаунта и возвращает словарь с результатом."""
    account_data = parsing_account_info(driver=driver, account_link=account_link)

    account_data['account_link'] = account_link
    account_data['hashtag'] = post_query.replace('%23', '#')
    account_data['emails'] = extract_emails(account_data.get('description', ''))

    # Предсказание типа аккаунта
    df = pd.DataFrame({
        'Описание страницы': [account_data.get('description', '')],
        'Ссылки из описания': [account_data.get('links_description', [])],
        'Ссылки из контактов': [account_data.get('links_contacts', [])],
        'Почта существует': [1 if account_data.get('emails', '') else 0],
        'Кол-во постов': [account_data.get('posts', '')]
    })
    account_data['predicted_account_type'] = get_account_type(
        data=df,
        threshold=0.8
    ).value

    return account_data


async def main(max_scrolls: int):
    # Парсинг запросов
    with open(config.QUERIES_PATH, "r", encoding="utf-8") as file:
        queries = json.load(file)

    # Загрузка данных для авторизации
    with open(config.AUTH_DATA_PATH, "r", encoding="utf-8") as file:
        auth_data_list = json.load(file)

    auth_data = auth_data_list[0]
    username = auth_data.get('username')
    password = auth_data.get('password')
    if not username or not password:
        raise Exception(f'В первом элементе нет username: "{username}" или password: "{password}"')

    # Запуск парсера
    for query in queries:
        query = f'%23{query}'  # '%23' == '#'
        driver = start_driver()  # Запуск драйвера
        auth(driver=driver, username=username, password=password)  # Авторизация

        # Получение ссылок на аккаунты и сохранение их в БД (статус PARSING)
        account_links = account_links_parsing(driver, post_query=query, max_scrolls=max_scrolls)
        for link in account_links:
            await create_or_update_object(
                async_session_factory=async_session,  # Важно: передаём фабрику как параметр
                model=Account,
                filters={'link': link},
                defaults={'link': link, 'status': STATUS.PARSING}
            )

        # Парсинг содержимого аккаунтов и запись в БД (переводим в статус READY)
        accounts = await get_objects_by_filter(
            async_session_factory=async_session,
            model=Account,
            filters={'status': STATUS.PARSING}
        )
        for idx, account in enumerate(accounts):
            print(f'Парсинг аккаунта #{idx}. Ссылка: {account.link}.')
            account_data = account_data_parser(driver, account.link, query)

            await create_or_update_object(
                async_session_factory=async_session,
                model=Account,
                filters={'id': account.id},
                defaults={'account_type': AccountType(account_data['predicted_account_type']),
                          'status': STATUS.READY,
                          'data': account_data}
            )
            time.sleep(random.randrange(10, 90))

        print("Информация об аккаунтах успешно сохранена в БД!")

        # Закрываем драйвер и уходим в сон
        close_driver(driver=driver)
        sleep_time = random.randrange(1200, 4200)
        print(f"Сон {sleep_time} секунд...")
        time.sleep(sleep_time)

    # Все аккаунты со статусом READY → выгружаем в Excel
    accounts = await get_objects_by_filter(
        async_session_factory=async_session,
        model=Account,
        filters={'status': STATUS.READY}
    )
    write_excel(accounts=accounts, out_path=config.INSTA_ACCOUNTS_DATA_PATH)

    # Меняем статус на SENT
    for account in accounts:
        await create_or_update_object(
            async_session_factory=async_session,
            model=Account,
            filters={'id': account.id},
            defaults={'status': STATUS.SENT}
        )


@click.option("--max-scrolls", default=2, help="Количество прокруток страницы вниз при парсинге постов")
@click.command(name="accounts_parser")
def run(max_scrolls):
    asyncio.run(main(max_scrolls))
