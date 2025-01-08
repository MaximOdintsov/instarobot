import time
import random
import json
import asyncio
import click
import pandas as pd
from selenium import webdriver

from robot.helpers.selenium_management import start_driver, close_driver
from robot.helpers.utils import extract_emails, validate_instagram_url, POST_VALUE, ACCOUNT_VALUE
from robot.database.orm import async_session, insert_account, get_accounts_not_processed, get_accounts_not_send, mark_account_as_sent
from robot.helpers.excel import write_excel
from robot.robot import auth, turn_to_posts_page, get_post_links, accounts_parsing, parsing_account_info
from robot import config
from robot.ml.predicting import get_account_type
from robot.database.models import AccountType


def account_links_parsing(driver: webdriver, post_query: str, max_scrolls: int):
    """
    1 шаг: Переход на страницу с постами и парсинг ссылок на посты
    2 шаг: 
    Парсинг ссылок на аккаунты
    """
    account_links = []
    # Переход на страницу с постами (по хэштегу) + проверка, найдены ли посты по хэштегу
    posts_found = turn_to_posts_page(driver=driver, query=post_query)
    if posts_found is False:
        return 0
    
    ########################
    ### ШАГ 1: Получение ссылок
    ########################
    
    # Получение старых ссылок на посты
    with open(config.POST_LINKS_PATH, 'r') as f:
        old_post_links = json.load(f)
        
    # Парсинг ссылок на посты
    post_links = list(get_post_links(driver, max_scrolls=max_scrolls))
    for post_link in post_links:
        link_type = validate_instagram_url(post_link)
        if (link_type != POST_VALUE) or (post_link in old_post_links):
            post_links.remove(post_link)
    print(f"Найдено {len(post_links)} ссылок на посты")
    
    ########################
    ### ШАГ 2: Парсинг ссылок на аккаунты
    ########################
    
    for idx, post_link in enumerate(post_links):
        print(f'Парсинг поста #{idx}. Ссылка: {post_link}')
        raw_account_links = accounts_parsing(driver=driver, post_link=post_link)
        for account_link in raw_account_links:
            link_type = validate_instagram_url(account_link)
            if link_type == ACCOUNT_VALUE:
                account_links.append(account_link)
        time.sleep(random.randrange(10, 60))
                
    # Запись новых ссылок на посты в файл
    with open(config.POST_LINKS_PATH, 'w') as f:
        merged_post_links = list(set(old_post_links + post_links))
        f.write(json.dumps(merged_post_links, indent=4))
        
    return account_links


def account_data_parser(driver: webdriver, account_link: str, post_query: str):
    account_data = parsing_account_info(driver=driver, account_link=account_link)
    
    account_data['account_link'] = account_link
    account_data['hashtag'] = post_query.replace('%23', '#')
    account_data['emails'] = extract_emails(account_data.get('description', ''))

    # Предсказание типа аккаунта
    df = pd.DataFrame(
        {
            'Описание страницы': [account_data.get('description', '')],
            'Ссылки из описания': [account_data.get('links_description', [])],
            'Ссылки из контактов': [account_data.get('links_contacts', [])],
            'Почта существует': [1 if account_data.get('emails', '') else 0],  # приводим в булево значение 1 / 0
            'Кол-во постов': [account_data.get('posts', '')]
        }
    )
    account_data['predicted_account_type'] = get_account_type(data=df, threshold=0.8).value
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
        
        # Получение ссылок на аккаунты и сохранение их в БД
        account_links = account_links_parsing(driver, post_query=query, max_scrolls=max_scrolls)
        for account_link in account_links:
            await insert_account(async_session=async_session, account_link=account_link)
        
        # Парсинг содержимого аккаунтов и запись в БД 
        accounts = await get_accounts_not_processed(async_session)
        accounts_len = len(accounts)
        for idx, account in enumerate(accounts):
            print(f'Парсинг акканута #{idx}. Ссылка: {account.link}. Всего аккаунтов для обработки: {accounts_len}')
            account_data = account_data_parser(driver=driver, account_link=account.link, post_query=query)
            await insert_account(
                async_session=async_session,
                account_link=account.link,
                account_type=AccountType(account_data['predicted_account_type']),
                is_processed=True,
                account_data=account_data,
            )
            time.sleep(random.randrange(10, 90))
        print(f'Информация об аккаунтах спарсилась и записалась в БД!')
        
        close_driver(driver=driver)
        sleep_time = random.randrange(1200, 4200)
        print(f'Сон {sleep_time} секунд...')
        time.sleep(sleep_time)
    
    # Запись данных в таблицу
    accounts = await get_accounts_not_send(async_session)
    write_excel(accounts=accounts, out_path=config.INSTA_ACCOUNTS_DATA_PATH)
    for account in accounts:
        await mark_account_as_sent(async_session, account)


@click.option("--max-scrolls", default=2, help="Количество прокруток страницы вниз при парсинге постов")
@click.command(name="accounts_parser")
def run(max_scrolls):
    """
    Парсер Instagram-аккаунтов по хэштегам.
    """
    asyncio.run(main(max_scrolls))
    